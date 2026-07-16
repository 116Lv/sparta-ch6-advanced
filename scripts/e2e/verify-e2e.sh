#!/bin/sh
set -eu

COMPOSE_FILE=docker-compose.e2e.yml
PROJECT_NAME="ch6-e2e-$(date +%s)-$$"
FAILED=1
STARTUP_TIMEOUT=300
OPERATION_TIMEOUT=30
LOG_TIMEOUT=20
CLEANUP_TIMEOUT=30
WATCHDOG_SEQUENCE=0
WATCHDOG_ROOT="${TMPDIR:-/tmp}/$PROJECT_NAME-watchdog"
ACTIVE_TARGET_PID=
ACTIVE_WATCHDOG_PID=
ACTIVE_TARGET_FILE="$WATCHDOG_ROOT/active-target"
ACTIVE_WATCHDOG_FILE="$WATCHDOG_ROOT/active-watchdog"
mkdir -p "$WATCHDOG_ROOT"

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
    shift
    WATCHDOG_SEQUENCE=$((WATCHDOG_SEQUENCE + 1))
    marker="$WATCHDOG_ROOT/timeout-$WATCHDOG_SEQUENCE"
    rm -f "$marker"
    "$@" <&0 &
    target_pid=$!
    ACTIVE_TARGET_PID=$target_pid
    printf '%s\n' "$target_pid" > "$ACTIVE_TARGET_FILE"
    (
        sleep "$timeout_seconds"
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
    run_with_watchdog "$timeout_seconds" docker compose \
        -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

cleanup() {
    status=$?
    trap - 0 HUP INT TERM
    terminate_active_processes
    if [ "$status" -eq 0 ] && [ "$FAILED" -ne 0 ]; then
        status=1
    fi
    if [ "$status" -ne 0 ] || [ "$FAILED" -ne 0 ]; then
        printf '%s\n' 'E2E failed; recent service logs follow.' >&2
        bounded_compose "$OPERATION_TIMEOUT" ps >&2 || true
        bounded_compose "$LOG_TIMEOUT" logs --no-color --tail=80 app mysql redis kafka >&2 || true
    fi
    bounded_compose "$CLEANUP_TIMEOUT" down -v --remove-orphans >/dev/null 2>&1 || true
    rm -f "$WATCHDOG_ROOT"/timeout-*
    rmdir "$WATCHDOG_ROOT" 2>/dev/null || true
    exit "$status"
}
trap cleanup 0
trap 'exit 130' HUP INT TERM

fail() {
    printf 'E2E assertion failed: %s\n' "$1" >&2
    return 1
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
    while [ "$attempts" -lt 60 ]; do
        actual=$(mysql_query "$sql" 2>/dev/null || true)
        [ "$actual" = "$expected" ] && return 0
        attempts=$((attempts + 1))
        sleep 1
    done
    fail "$description (expected '$expected', got '$actual')"
}

consumer_offset() {
    description=$(bounded_compose "$OPERATION_TIMEOUT" exec -T kafka kafka-consumer-groups.sh \
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
    while [ "$attempts" -lt 60 ]; do
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
    while [ "$attempts" -lt 60 ]; do
        current=$(consumer_offset)
        [ "$current" -eq "$expected" ] && return 0
        [ "$current" -gt "$expected" ] && fail "analytics consumer offset exceeded expected value $expected"
        attempts=$((attempts + 1))
        sleep 1
    done
    fail "analytics consumer offset did not become exactly $expected"
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

verify_charge_response() {
    expected_user_id=$1
    "$PYTHON" -c '
import json, sys
body = json.load(sys.stdin)
expected = {"userId": int(sys.argv[1]), "chargedAmount": 10000, "balance": 10000}
if not isinstance(body, dict) or body != expected:
    raise SystemExit("charge response contract mismatch")
' "$expected_user_id"
}

verify_order_response() {
    expected_user_id=$1
    expected_menu_id=$2
    "$PYTHON" -c '
import json, sys
body = json.load(sys.stdin)
if not isinstance(body, dict):
    raise SystemExit("order response must be an object")
order_id = body.get("orderId")
if not isinstance(order_id, int) or isinstance(order_id, bool) or order_id <= 0:
    raise SystemExit("orderId must be a positive integer")
expected = {
    "orderId": body["orderId"],
    "userId": int(sys.argv[1]),
    "menuId": int(sys.argv[2]),
    "paymentAmount": 3000,
    "remainingPoint": 7000,
    "status": "PAID",
}
if body != expected:
    raise SystemExit("order response contract mismatch")
print(order_id)
' "$expected_user_id" "$expected_menu_id"
}

verify_popular_response() {
    expected_menu_id=$1
    "$PYTHON" -c '
import json, sys
body = json.load(sys.stdin)
expected = {
    "periodDays": 7,
    "menus": [{
    "menuId": int(sys.argv[1]),
    "name": "E2E Coffee",
    "price": 3000,
    "orderCount": 1,
    }],
}
if not isinstance(body, dict) or body != expected:
    raise SystemExit("popular-menu response contract mismatch")
' "$expected_menu_id"
}

snapshot_seven_markers() {
    for marker_date in $SEVEN_DATES; do
        marker_value=$(bounded_compose "$OPERATION_TIMEOUT" exec -T redis \
            redis-cli --raw GET "popular-menu:complete:$marker_date" | tr -d '\r')
        expected_total=0
        expected_members=0
        if [ "$marker_date" = "$TODAY" ]; then
            expected_total=1
            expected_members=1
        fi
        printf '%s\n' "$marker_value" | awk -F'|' \
            -v total="$expected_total" -v members="$expected_members" \
            'NF == 3 && length($1) > 0 && $2 == total && $3 == members { valid = 1 }
             END { exit valid ? 0 : 1 }' \
            || fail "Redis completion marker metadata mismatch for $marker_date"
        printf '%s=%s\n' "$marker_date" "$marker_value"
    done
}

command -v docker >/dev/null 2>&1 || fail 'docker is required'
command -v curl >/dev/null 2>&1 || fail 'curl is required'
PYTHON=$(resolve_python)

bounded_compose "$STARTUP_TIMEOUT" up --build -d --wait --wait-timeout 240
APP_PORT=$(bounded_compose "$OPERATION_TIMEOUT" port app 8080 | awk -F: 'END { print $NF }')
[ -n "$APP_PORT" ] || fail 'app host port was not published'
BASE_URL="http://127.0.0.1:$APP_PORT"
http_json GET "$BASE_URL/api/v1/menus" >/dev/null

# Flyway-created tables are the readiness contract; seed only durable production fixtures.
fixture=$(mysql_query "INSERT INTO users(created_at,updated_at) VALUES(NOW(),NOW()); SET @uid=LAST_INSERT_ID(); INSERT INTO menus(name,price,status,created_at,updated_at) VALUES('E2E Coffee',3000,'ON_SALE',NOW(),NOW()); SET @mid=LAST_INSERT_ID(); SELECT @uid,@mid;")
USER_ID=$(printf '%s\n' "$fixture" | awk 'END { print $1 }')
MENU_ID=$(printf '%s\n' "$fixture" | awk 'END { print $2 }')
[ -n "$USER_ID" ] && [ -n "$MENU_ID" ] || fail 'fixture identifiers were not returned'

charge=$(http_json POST "$BASE_URL/api/v1/users/$USER_ID/points/charge" '{"amount":10000}')
printf '%s' "$charge" | verify_charge_response "$USER_ID"

order=$(http_json POST "$BASE_URL/api/v1/orders" "{\"userId\":$USER_ID,\"menuId\":$MENU_ID}")
ORDER_ID=$(printf '%s' "$order" | verify_order_response "$USER_ID" "$MENU_ID")

TODAY=$(mysql_query 'SELECT DATE(CONVERT_TZ(UTC_TIMESTAMP(),"+00:00","+09:00"));')
wait_for_sql 'paid order row' "SELECT COUNT(*) FROM orders WHERE id=$ORDER_ID AND user_id=$USER_ID AND menu_id=$MENU_ID AND order_price=3000 AND status='PAID';" 1
wait_for_sql 'successful payment row' "SELECT COUNT(*) FROM payments WHERE order_id=$ORDER_ID AND user_id=$USER_ID AND amount=3000 AND status='SUCCESS';" 1
wait_for_sql 'charge and use histories' "SELECT COUNT(*) FROM point_histories WHERE user_id=$USER_ID AND ((type='CHARGE' AND amount=10000) OR (type='USE' AND amount=3000));" 2
wait_for_sql 'final user point balance' "SELECT balance FROM user_points WHERE user_id=$USER_ID;" 7000
wait_for_sql 'daily sales row' "SELECT order_count FROM daily_menu_sales WHERE sales_date='$TODAY' AND menu_id=$MENU_ID;" 1
wait_for_sql 'ORDER_PAID outbox row' "SELECT COUNT(*) FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';" 1
wait_for_sql 'Outbox PUBLISHED state' "SELECT status FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';" PUBLISHED

EVENT_ID=$(mysql_query "SELECT id FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';")
wait_for_sql 'consumer processed marker' "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;" 1
wait_for_sql 'consumer analytics effect' "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID AND aggregate_id=$ORDER_ID AND user_id=$USER_ID AND menu_id=$MENU_ID AND payment_amount=3000;" 1
OFFSET_BASELINE=$(wait_for_stable_positive_offset)

REDIS_SCORE=$(bounded_compose "$OPERATION_TIMEOUT" exec -T redis \
    redis-cli --raw ZSCORE "popular-menu:$TODAY" "$MENU_ID" | tr -d '\r')
[ "$REDIS_SCORE" = 1 ] || fail "Redis ranking score (expected 1, got '$REDIS_SCORE')"
popular=$(http_json GET "$BASE_URL/api/v1/menus/popular?days=7&limit=3")
printf '%s' "$popular" | verify_popular_response "$MENU_ID"
SEVEN_DATES=$("$PYTHON" -c '
from datetime import date, timedelta
today = date.fromisoformat(__import__("sys").argv[1])
print(" ".join(str(today - timedelta(days=offset)) for offset in range(7)))
' "$TODAY")
MARKERS_AFTER_REBUILD=$(snapshot_seven_markers)
popular_cached=$(http_json GET "$BASE_URL/api/v1/menus/popular?days=7&limit=3")
printf '%s' "$popular_cached" | verify_popular_response "$MENU_ID"
MARKERS_AFTER_CACHE_HIT=$(snapshot_seven_markers)
[ "$MARKERS_AFTER_CACHE_HIT" = "$MARKERS_AFTER_REBUILD" ] \
    || fail 'popular-menu cache-hit request changed seven-day marker generations'

MESSAGE="{\"eventId\":$EVENT_ID,\"eventType\":\"ORDER_PAID\",\"aggregateId\":$ORDER_ID,\"payload\":{\"userId\":$USER_ID,\"menuId\":$MENU_ID,\"paymentAmount\":3000}}"
EXPECTED_OFFSET=$((OFFSET_BASELINE + 1))
printf '%s\n' "$MESSAGE" | bounded_compose "$OPERATION_TIMEOUT" exec -T kafka kafka-console-producer.sh \
    --bootstrap-server kafka:9092 --topic coffee.order.paid
wait_for_exact_offset "$EXPECTED_OFFSET"
[ "$(mysql_query "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed processed marker count'
[ "$(mysql_query "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed analytics count'

FAILED=0
printf '%s\n' 'Docker Compose black-box E2E scenario completed.'
