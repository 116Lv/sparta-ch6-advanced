#!/bin/sh
set -eu

COMPOSE_FILE=docker-compose.multi-instance.yml
PROJECT_NAME="ch6-multi-$(date +%s)-$$"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
RESULT_ROOT="$REPOSITORY_ROOT/build/reports/k6/$PROJECT_NAME"
WATCHDOG_ROOT="${TMPDIR:-/tmp}/$PROJECT_NAME-watchdog"
K6_RESULT_DIR="$RESULT_ROOT"
export K6_RESULT_DIR
FAILED=1
STARTUP_TIMEOUT=360
LOAD_TIMEOUT=90
OPERATION_TIMEOUT=30
CONVERGENCE_ATTEMPTS=120
LOG_TIMEOUT=20
CLEANUP_TIMEOUT=40
WATCHDOG_SEQUENCE=0
ACTIVE_TARGET_PID=
ACTIVE_WATCHDOG_PID=
ACTIVE_TARGET_FILE="$WATCHDOG_ROOT/active-target"
ACTIVE_WATCHDOG_FILE="$WATCHDOG_ROOT/active-watchdog"
mkdir -p "$WATCHDOG_ROOT" "$K6_RESULT_DIR"
chmod 777 "$K6_RESULT_DIR"

clear_active_processes() {
    ACTIVE_TARGET_PID=
    ACTIVE_WATCHDOG_PID=
    rm -f "$ACTIVE_TARGET_FILE" "$ACTIVE_WATCHDOG_FILE"
}

terminate_active_processes() {
    target_pid=${ACTIVE_TARGET_PID:-}
    watchdog_pid=${ACTIVE_WATCHDOG_PID:-}
    [ -s "$ACTIVE_TARGET_FILE" ] && IFS= read -r target_pid < "$ACTIVE_TARGET_FILE"
    [ -s "$ACTIVE_WATCHDOG_FILE" ] && IFS= read -r watchdog_pid < "$ACTIVE_WATCHDOG_FILE"
    [ -n "$target_pid" ] && kill -TERM "$target_pid" 2>/dev/null || true
    [ -n "$watchdog_pid" ] && kill -TERM "$watchdog_pid" 2>/dev/null || true
    sleep 1
    [ -n "$target_pid" ] && kill -KILL "$target_pid" 2>/dev/null || true
    [ -n "$watchdog_pid" ] && kill -KILL "$watchdog_pid" 2>/dev/null || true
    [ -n "$target_pid" ] && wait "$target_pid" 2>/dev/null || true
    [ -n "$watchdog_pid" ] && wait "$watchdog_pid" 2>/dev/null || true
    clear_active_processes
}

run_with_watchdog() {
    timeout_seconds=$1
    input_file=$2
    shift 2
    WATCHDOG_SEQUENCE=$((WATCHDOG_SEQUENCE + 1))
    marker="$WATCHDOG_ROOT/timeout-$WATCHDOG_SEQUENCE"
    rm -f "$marker"
    "$@" < "$input_file" &
    target_pid=$!
    ACTIVE_TARGET_PID=$target_pid
    printf '%s\n' "$target_pid" > "$ACTIVE_TARGET_FILE"
    (
        elapsed=0
        while [ "$elapsed" -lt "$timeout_seconds" ]; do
            sleep 1
            kill -0 "$target_pid" 2>/dev/null || exit 0
            elapsed=$((elapsed + 1))
        done
        if kill -0 "$target_pid" 2>/dev/null; then
            : > "$marker"
            kill -TERM "$target_pid" 2>/dev/null || true
            sleep 2
            kill -KILL "$target_pid" 2>/dev/null || true
        fi
    ) &
    watchdog_pid=$!
    ACTIVE_WATCHDOG_PID=$watchdog_pid
    printf '%s\n' "$watchdog_pid" > "$ACTIVE_WATCHDOG_FILE"
    command_status=0
    wait "$target_pid" || command_status=$?
    kill "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true
    clear_active_processes
    if [ -f "$marker" ]; then
        rm -f "$marker"
        printf 'Command timed out after %s seconds: %s\n' "$timeout_seconds" "$*" >&2
        return 124
    fi
    return "$command_status"
}

bounded_compose() {
    timeout_seconds=$1
    shift
    run_with_watchdog "$timeout_seconds" /dev/null docker compose \
        -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

bounded_compose_with_input() {
    timeout_seconds=$1
    shift
    input_file="$WATCHDOG_ROOT/stdin"
    cat > "$input_file"
    status=0
    run_with_watchdog "$timeout_seconds" "$input_file" docker compose \
        -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@" || status=$?
    rm -f "$input_file"
    return "$status"
}

cleanup() {
    status=$?
    trap - 0 HUP INT TERM
    terminate_active_processes
    if [ "$status" -eq 0 ] && [ "$FAILED" -ne 0 ]; then
        status=1
    fi
    if [ "$status" -ne 0 ] || [ "$FAILED" -ne 0 ]; then
        printf '%s\n' 'Multi-instance E2E failed; recent service logs follow.' >&2
        bounded_compose "$OPERATION_TIMEOUT" ps >&2 || true
        bounded_compose "$LOG_TIMEOUT" logs --no-color --tail=100 app-1 app-2 nginx mysql redis kafka >&2 || true
        [ ! -f "$K6_RESULT_DIR/k6-summary.json" ] || {
            printf '%s\n' 'Available k6 summary:' >&2
            cat "$K6_RESULT_DIR/k6-summary.json" >&2
        }
    fi
    bounded_compose "$CLEANUP_TIMEOUT" down -v --remove-orphans >/dev/null 2>&1 || true
    rm -f "$WATCHDOG_ROOT"/timeout-* "$WATCHDOG_ROOT"/headers-* "$WATCHDOG_ROOT"/stdin
    rmdir "$WATCHDOG_ROOT" 2>/dev/null || true
    exit "$status"
}
trap cleanup 0
trap 'exit 130' HUP INT TERM

fail() {
    printf 'Multi-instance E2E assertion failed: %s\n' "$1" >&2
    return 1
}

resolve_python() {
    for candidate in python3 python; do
        path=$(command -v "$candidate" 2>/dev/null || true)
        case "$path" in
            /*)
                if [ -x "$path" ] && "$path" -c 'import json' >/dev/null 2>&1; then
                    printf '%s\n' "$path"
                    return 0
                fi
                ;;
        esac
    done
    fail 'python3 or python with the stdlib json module is required'
}

mysql_query() {
    bounded_compose "$OPERATION_TIMEOUT" exec -T mysql \
        mysql --batch --skip-column-names -uroot -proot cafe -e "$1"
}

wait_for_sql() {
    description=$1
    sql=$2
    expected=$3
    attempts=0
    actual=
    while [ "$attempts" -lt "$CONVERGENCE_ATTEMPTS" ]; do
        actual=$(mysql_query "$sql" 2>/dev/null || true)
        [ "$actual" = "$expected" ] && return 0
        attempts=$((attempts + 1))
        sleep 1
    done
    fail "$description (expected '$expected', got '$actual')"
}

http_json() {
    method=$1
    url=$2
    body=${3-}
    if [ -n "$body" ]; then
        curl --fail --silent --show-error --max-time 10 \
            -X "$method" -H 'Content-Type: application/json' --data "$body" "$url"
    else
        curl --fail --silent --show-error --max-time 10 -X "$method" "$url"
    fi
}

capture_upstream() {
    output_file=$1
    header_file="$WATCHDOG_ROOT/headers-current"
    if ! curl --fail --silent --show-error --max-time 10 \
        -D "$header_file" -o /dev/null "$BASE_URL/api/v1/menus"; then
        rm -f "$header_file"
        fail 'load-balancer upstream probe failed'
    fi
    awk 'BEGIN { IGNORECASE=1 }
            /^X-Upstream-Addr:/ {
                sub(/^[^:]*:[[:space:]]*/, "")
                gsub("\\r", "")
                count = split($0, addresses, ",")
                final = addresses[count]
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", final)
                if (length(final) > 0) print final
            }' "$header_file" >> "$output_file"
    rm -f "$header_file"
}

consumer_offset() {
    description=$(bounded_compose "$OPERATION_TIMEOUT" exec -T kafka /opt/kafka/bin/kafka-consumer-groups.sh \
        --bootstrap-server kafka:9092 --group coffee-order-analytics --describe) \
        || fail 'Kafka consumer-group describe failed'
    printf '%s\n' "$description" | awk '
        $2 == "coffee.order.paid" {
            found = 1
            if ($4 !~ /^[0-9]+$/) invalid = 1
            total += $4
        }
        END {
            if (invalid) exit 2
            if (!found) exit 3
            print total
        }'
}

wait_for_stable_positive_offset() {
    attempts=0
    previous=
    while [ "$attempts" -lt "$CONVERGENCE_ATTEMPTS" ]; do
        current=$(consumer_offset)
        if [ "$current" -gt 0 ]; then
            if [ -n "$previous" ] && [ "$current" -eq "$previous" ]; then
                printf '%s\n' "$current"
                return 0
            fi
            previous=$current
        else
            previous=
        fi
        attempts=$((attempts + 1))
        sleep 1
    done
    fail 'analytics consumer offset did not reach a stable positive baseline'
}

wait_for_exact_offset() {
    expected=$1
    attempts=0
    while [ "$attempts" -lt "$CONVERGENCE_ATTEMPTS" ]; do
        current=$(consumer_offset)
        [ "$current" -eq "$expected" ] && return 0
        [ "$current" -gt "$expected" ] && fail "analytics consumer offset exceeded expected value $expected"
        attempts=$((attempts + 1))
        sleep 1
    done
    fail "analytics consumer offset did not become exactly $expected"
}

command -v docker >/dev/null 2>&1 || fail 'docker is required'
command -v curl >/dev/null 2>&1 || fail 'curl is required'
PYTHON=$(resolve_python)

printf 'Multi-instance Compose project: %s\n' "$PROJECT_NAME"
printf 'Persistent k6 result directory: %s\n' "$K6_RESULT_DIR"
bounded_compose "$STARTUP_TIMEOUT" up --build -d --wait --wait-timeout 300
NGINX_PORT=$(bounded_compose "$OPERATION_TIMEOUT" port nginx 8080 | awk -F: 'END { print $NF }')
[ -n "$NGINX_PORT" ] || fail 'nginx host port was not published'
BASE_URL="http://127.0.0.1:$NGINX_PORT"

UPSTREAMS_BEFORE="$WATCHDOG_ROOT/headers-before"
: > "$UPSTREAMS_BEFORE"
attempt=0
while [ "$attempt" -lt 12 ]; do
    capture_upstream "$UPSTREAMS_BEFORE"
    attempt=$((attempt + 1))
done
DISTINCT_UPSTREAMS=$(sort -u "$UPSTREAMS_BEFORE" | wc -l | tr -d ' ')
[ "$DISTINCT_UPSTREAMS" -eq 2 ] || fail "expected both upstreams before load, observed: $(sort -u "$UPSTREAMS_BEFORE" | tr '\n' ' ')"

# FIXTURE identifiers scope every durable SQL assertion in this scenario.
fixture=$(mysql_query "INSERT INTO users(created_at,updated_at) VALUES(NOW(),NOW()); SET @uid=LAST_INSERT_ID(); INSERT INTO menus(name,price,status,created_at,updated_at) VALUES('Multi E2E Coffee',3000,'ON_SALE',NOW(),NOW()); SET @mid=LAST_INSERT_ID(); SELECT @uid,@mid;")
FIXTURE_USER_ID=$(printf '%s\n' "$fixture" | awk 'END { print $1 }')
FIXTURE_MENU_ID=$(printf '%s\n' "$fixture" | awk 'END { print $2 }')
[ -n "$FIXTURE_USER_ID" ] && [ -n "$FIXTURE_MENU_ID" ] || fail 'FIXTURE identifiers were not returned'
# Two VUs sleep between attempts for four seconds, so this bounded balance has ample headroom.
http_json POST "$BASE_URL/api/v1/users/$FIXTURE_USER_ID/points/charge" '{"amount":300000}' >/dev/null

bounded_compose "$LOAD_TIMEOUT" --profile k6 run --no-deps --rm -T \
    -e BASE_URL=http://nginx:8080 \
    -e FIXTURE_USER_ID="$FIXTURE_USER_ID" \
    -e FIXTURE_MENU_ID="$FIXTURE_MENU_ID" k6

SUMMARY_FILE="$K6_RESULT_DIR/k6-summary.json"
[ -s "$SUMMARY_FILE" ] || fail 'k6 summary JSON was not created'
"$PYTHON" - "$SUMMARY_FILE" <<'PY'
import json
import math
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    summary = json.load(stream)
required = {
    "checks",
    "checkFailures",
    "httpRequests",
    "requestRatePerSecond",
    "httpRequestFailures",
    "httpRequestFailureRate",
    "latencyMs",
}
if set(summary) != required:
    raise SystemExit("k6 summary keys mismatch")
if summary["checks"] <= 0 or summary["checkFailures"] != 0:
    raise SystemExit("k6 checks summary reports a failure")
if (
    summary["httpRequests"] <= 0
    or summary["httpRequestFailures"] != 0
    or summary["httpRequestFailureRate"] != 0
):
    raise SystemExit("k6 http_req_failed summary reports a failure")
throughput = summary["requestRatePerSecond"]
if not isinstance(throughput, (int, float)) or not math.isfinite(throughput) or throughput < 0:
    raise SystemExit("k6 request throughput observation is not finite and non-negative")
latency = summary["latencyMs"]
if set(latency) != {"p50", "p95", "p99"} or any(value is None for value in latency.values()):
    raise SystemExit("k6 latency observation is incomplete")
PY
printf '%s\n' 'Validated k6 summary:'
cat "$SUMMARY_FILE"
printf '\n'

app2_hosts=$(bounded_compose "$OPERATION_TIMEOUT" exec -T nginx getent hosts app-2) \
    || fail 'nginx could not resolve app-2 before the stop step'
APP2_IP=$(printf '%s\n' "$app2_hosts" | awk 'NR == 1 { print $1 }')
[ -n "$APP2_IP" ] || fail 'nginx returned an empty app-2 address before the stop step'
APP2_UPSTREAM="$APP2_IP:8080"

bounded_compose "$OPERATION_TIMEOUT" stop app-1
UPSTREAMS_AFTER="$WATCHDOG_ROOT/headers-after"
: > "$UPSTREAMS_AFTER"
attempt=0
while [ "$attempt" -lt 6 ]; do
    capture_upstream "$UPSTREAMS_AFTER"
    attempt=$((attempt + 1))
done
[ -s "$UPSTREAMS_AFTER" ] || fail 'post-stop responses did not expose an upstream address'
[ "$(wc -l < "$UPSTREAMS_AFTER" | tr -d ' ')" -eq 6 ] \
    || fail 'not every post-stop probe returned a final upstream address'
UNEXPECTED_POST_STOP=$(awk -v expected="$APP2_UPSTREAM" '$0 != expected { count++ } END { print count + 0 }' "$UPSTREAMS_AFTER")
[ "$UNEXPECTED_POST_STOP" -eq 0 ] \
    || fail "post-stop final upstream differed from app-2 ($APP2_UPSTREAM): $(sort -u "$UPSTREAMS_AFTER" | tr '\n' ' ')"

post_stop_order=$(http_json POST "$BASE_URL/api/v1/orders" "{\"userId\":$FIXTURE_USER_ID,\"menuId\":$FIXTURE_MENU_ID}")
POST_STOP_ORDER_ID=$(printf '%s' "$post_stop_order" | "$PYTHON" -c '
import json, sys
body = json.load(sys.stdin)
if body.get("status") != "PAID" or not isinstance(body.get("orderId"), int):
    raise SystemExit("post-stop order response mismatch")
print(body["orderId"])
')
[ -n "$POST_STOP_ORDER_ID" ] || fail 'post-stop paid order identifier was not returned'

EXPECTED_ORDERS=$(mysql_query "SELECT COUNT(*) FROM orders WHERE user_id=$FIXTURE_USER_ID AND menu_id=$FIXTURE_MENU_ID AND status='PAID';")
[ "$EXPECTED_ORDERS" -gt 0 ] || fail 'FIXTURE produced no paid orders'
wait_for_sql 'FIXTURE successful payments' "SELECT COUNT(*) FROM payments WHERE user_id=$FIXTURE_USER_ID AND status='SUCCESS';" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE USE histories' "SELECT COUNT(*) FROM point_histories WHERE user_id=$FIXTURE_USER_ID AND type='USE';" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE ORDER_PAID Outbox rows' "SELECT COUNT(*) FROM outbox_events WHERE event_type='ORDER_PAID' AND aggregate_id IN (SELECT id FROM orders WHERE user_id=$FIXTURE_USER_ID AND menu_id=$FIXTURE_MENU_ID);" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE PUBLISHED Outbox rows' "SELECT COUNT(*) FROM outbox_events WHERE status='PUBLISHED' AND event_type='ORDER_PAID' AND aggregate_id IN (SELECT id FROM orders WHERE user_id=$FIXTURE_USER_ID AND menu_id=$FIXTURE_MENU_ID);" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE consumer processed markers' "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id IN (SELECT id FROM outbox_events WHERE event_type='ORDER_PAID' AND aggregate_id IN (SELECT id FROM orders WHERE user_id=$FIXTURE_USER_ID AND menu_id=$FIXTURE_MENU_ID));" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE analytics effects' "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND user_id=$FIXTURE_USER_ID AND menu_id=$FIXTURE_MENU_ID;" "$EXPECTED_ORDERS"
wait_for_sql 'FIXTURE non-negative balance' "SELECT COUNT(*) FROM user_points WHERE user_id=$FIXTURE_USER_ID AND balance >= 0;" 1
wait_for_sql 'FIXTURE balance/history equation' "SELECT COUNT(*) FROM user_points up WHERE user_id=$FIXTURE_USER_ID AND up.balance=(SELECT SUM(CASE WHEN type='CHARGE' THEN amount WHEN type='USE' THEN -amount ELSE 0 END) FROM point_histories WHERE user_id=$FIXTURE_USER_ID);" 1
[ "$(mysql_query "SELECT COUNT(*) FROM payments WHERE order_id IN (SELECT id FROM orders WHERE user_id=$FIXTURE_USER_ID) GROUP BY order_id HAVING COUNT(*) > 1;")" = '' ] || fail 'a FIXTURE order has more than one payment'

EVENT_ID=$(mysql_query "SELECT id FROM outbox_events WHERE aggregate_id=$POST_STOP_ORDER_ID AND event_type='ORDER_PAID';")
[ -n "$EVENT_ID" ] || fail 'post-stop ORDER_PAID event was not found'
OFFSET_BASELINE=$(wait_for_stable_positive_offset)
duplicate_message="{\"eventId\":$EVENT_ID,\"eventType\":\"ORDER_PAID\",\"aggregateId\":$POST_STOP_ORDER_ID,\"payload\":{\"userId\":$FIXTURE_USER_ID,\"menuId\":$FIXTURE_MENU_ID,\"paymentAmount\":3000}}"
printf '%s\n' "$duplicate_message" | bounded_compose_with_input "$OPERATION_TIMEOUT" exec -T kafka /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server kafka:9092 --topic coffee.order.paid
wait_for_exact_offset "$((OFFSET_BASELINE + 1))"
[ "$(mysql_query "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed processed_events marker count'
[ "$(mysql_query "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed order_paid_analytics effect count'

TODAY=$(mysql_query 'SELECT DATE(CONVERT_TZ(UTC_TIMESTAMP(),"+00:00","+09:00"));')
MYSQL_POPULAR_COUNT=$(mysql_query "SELECT order_count FROM daily_menu_sales WHERE sales_date='$TODAY' AND menu_id=$FIXTURE_MENU_ID;")
[ "$MYSQL_POPULAR_COUNT" = "$EXPECTED_ORDERS" ] || fail "MySQL daily aggregate mismatch (expected $EXPECTED_ORDERS, got $MYSQL_POPULAR_COUNT)"
bounded_compose "$OPERATION_TIMEOUT" exec -T redis redis-cli FLUSHALL >/dev/null
recovered_popular=$(http_json GET "$BASE_URL/api/v1/menus/popular?days=7&limit=3")
printf '%s' "$recovered_popular" | "$PYTHON" -c '
import json, sys
body = json.load(sys.stdin)
expected_menu, expected_count = map(int, sys.argv[1:])
matches = [item for item in body.get("menus", []) if item.get("menuId") == expected_menu]
if len(matches) != 1 or matches[0].get("orderCount") != expected_count:
    raise SystemExit("popular-menu did not recover from the MySQL durable aggregate")
' "$FIXTURE_MENU_ID" "$MYSQL_POPULAR_COUNT"
REDIS_SCORE=$(bounded_compose "$OPERATION_TIMEOUT" exec -T redis redis-cli --raw ZSCORE "popular-menu:$TODAY" "$FIXTURE_MENU_ID" | tr -d '\r')
[ "$REDIS_SCORE" = "$MYSQL_POPULAR_COUNT" ] || fail "Redis ranking was not rebuilt (expected $MYSQL_POPULAR_COUNT, got '$REDIS_SCORE')"
SEVEN_DATES=$("$PYTHON" -c '
from datetime import date, timedelta
today = date.fromisoformat(__import__("sys").argv[1])
print(" ".join(str(today - timedelta(days=offset)) for offset in range(7)))
' "$TODAY")
for marker_date in $SEVEN_DATES; do
    REDIS_MARKER=$(bounded_compose "$OPERATION_TIMEOUT" exec -T redis \
        redis-cli --raw GET "popular-menu:complete:$marker_date" | tr -d '\r')
    expected_total=0
    expected_members=0
    if [ "$marker_date" = "$TODAY" ]; then
        expected_total=$EXPECTED_ORDERS
        expected_members=1
    fi
    printf '%s\n' "$REDIS_MARKER" | awk -F'|' \
        -v total="$expected_total" -v members="$expected_members" \
        'NF == 3 && length($1) > 0 && $2 == total && $3 == members { valid = 1 }
         END { exit valid ? 0 : 1 }' \
        || fail "Redis completeness marker metadata mismatch for $marker_date"
done

FAILED=0
printf '%s\n' 'Docker Compose multi-instance k6 E2E scenario completed.'
