#!/bin/sh
set -eu

COMPOSE_FILE=docker-compose.e2e.yml
PROJECT_NAME="ch6-e2e-$(date +%s)-$$"
FAILED=1

compose() {
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

cleanup() {
    status=$?
    trap - 0 HUP INT TERM
    if [ "$status" -ne 0 ] || [ "$FAILED" -ne 0 ]; then
        printf '%s\n' 'E2E failed; recent service logs follow.' >&2
        compose ps >&2 || true
        compose logs --no-color --tail=80 app mysql redis kafka >&2 || true
    fi
    compose down -v --remove-orphans >/dev/null 2>&1 || true
    exit "$status"
}
trap cleanup 0
trap 'exit 130' HUP INT TERM

fail() {
    printf 'E2E assertion failed: %s\n' "$1" >&2
    return 1
}

mysql_query() {
    compose exec -T mysql mysql --batch --skip-column-names -uroot -proot cafe -e "$1"
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
    compose exec -T kafka kafka-consumer-groups.sh \
        --bootstrap-server kafka:9092 --group coffee-order-analytics --describe 2>/dev/null \
        | awk '$2 == "coffee.order.paid" { total += $4 } END { print total + 0 }'
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

command -v docker >/dev/null 2>&1 || fail 'docker is required'
command -v curl >/dev/null 2>&1 || fail 'curl is required'

compose up --build -d --wait --wait-timeout 240
APP_PORT=$(compose port app 8080 | awk -F: 'END { print $NF }')
[ -n "$APP_PORT" ] || fail 'app host port was not published'
BASE_URL="http://127.0.0.1:$APP_PORT"
http_json GET "$BASE_URL/api/v1/menus" >/dev/null

# Flyway-created tables are the readiness contract; seed only durable production fixtures.
fixture=$(mysql_query "INSERT INTO users(created_at,updated_at) VALUES(NOW(),NOW()); SET @uid=LAST_INSERT_ID(); INSERT INTO menus(name,price,status,created_at,updated_at) VALUES('E2E Coffee',3000,'ON_SALE',NOW(),NOW()); SET @mid=LAST_INSERT_ID(); SELECT @uid,@mid;")
USER_ID=$(printf '%s\n' "$fixture" | awk 'END { print $1 }')
MENU_ID=$(printf '%s\n' "$fixture" | awk 'END { print $2 }')
[ -n "$USER_ID" ] && [ -n "$MENU_ID" ] || fail 'fixture identifiers were not returned'

charge=$(http_json POST "$BASE_URL/api/v1/users/$USER_ID/points/charge" '{"amount":10000}')
printf '%s' "$charge" | grep -Eq '"balance"[[:space:]]*:[[:space:]]*10000' || fail 'charge response balance'

order=$(http_json POST "$BASE_URL/api/v1/orders" "{\"userId\":$USER_ID,\"menuId\":$MENU_ID}")
printf '%s' "$order" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"PAID"' || fail 'paid order response status'
ORDER_ID=$(printf '%s' "$order" | sed -n 's/.*"orderId"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p')
[ -n "$ORDER_ID" ] || fail 'orderId missing from response'

TODAY=$(mysql_query 'SELECT DATE(CONVERT_TZ(UTC_TIMESTAMP(),"+00:00","+09:00"));')
wait_for_sql 'paid order row' "SELECT COUNT(*) FROM orders WHERE id=$ORDER_ID AND user_id=$USER_ID AND menu_id=$MENU_ID AND order_price=3000 AND status='PAID';" 1
wait_for_sql 'successful payment row' "SELECT COUNT(*) FROM payments WHERE order_id=$ORDER_ID AND user_id=$USER_ID AND amount=3000 AND status='SUCCESS';" 1
wait_for_sql 'charge and use histories' "SELECT COUNT(*) FROM point_histories WHERE user_id=$USER_ID AND ((type='CHARGE' AND amount=10000) OR (type='USE' AND amount=3000));" 2
wait_for_sql 'daily sales row' "SELECT order_count FROM daily_menu_sales WHERE sales_date='$TODAY' AND menu_id=$MENU_ID;" 1
wait_for_sql 'ORDER_PAID outbox row' "SELECT COUNT(*) FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';" 1
wait_for_sql 'Outbox PUBLISHED state' "SELECT status FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';" PUBLISHED

EVENT_ID=$(mysql_query "SELECT id FROM outbox_events WHERE aggregate_id=$ORDER_ID AND event_type='ORDER_PAID';")
wait_for_sql 'consumer processed marker' "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;" 1
wait_for_sql 'consumer analytics effect' "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID AND aggregate_id=$ORDER_ID AND user_id=$USER_ID AND menu_id=$MENU_ID AND payment_amount=3000;" 1

REDIS_SCORE=$(compose exec -T redis redis-cli --raw ZSCORE "popular-menu:$TODAY" "$MENU_ID" | tr -d '\r')
[ "$REDIS_SCORE" = 1 ] || fail "Redis ranking score (expected 1, got '$REDIS_SCORE')"
popular=$(http_json GET "$BASE_URL/api/v1/menus/popular?days=7&limit=3")
printf '%s' "$popular" | grep -Eq "\"menuId\"[[:space:]]*:[[:space:]]*$MENU_ID" || fail 'popular-menu response menuId'
printf '%s' "$popular" | grep -Eq '"orderCount"[[:space:]]*:[[:space:]]*1' || fail 'popular-menu response orderCount'

MESSAGE="{\"eventId\":$EVENT_ID,\"eventType\":\"ORDER_PAID\",\"aggregateId\":$ORDER_ID,\"payload\":{\"userId\":$USER_ID,\"menuId\":$MENU_ID,\"paymentAmount\":3000}}"
OFFSET_BEFORE=$(consumer_offset)
printf '%s\n' "$MESSAGE" | compose exec -T kafka kafka-console-producer.sh \
    --bootstrap-server kafka:9092 --topic coffee.order.paid
attempts=0
while [ "$attempts" -lt 60 ]; do
    OFFSET_AFTER=$(consumer_offset)
    [ "$OFFSET_AFTER" -gt "$OFFSET_BEFORE" ] && break
    attempts=$((attempts + 1))
    sleep 1
done
[ "$OFFSET_AFTER" -gt "$OFFSET_BEFORE" ] || fail 'analytics consumer group did not consume duplicate broker record'
[ "$(mysql_query "SELECT COUNT(*) FROM processed_events WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed processed marker count'
[ "$(mysql_query "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group='coffee-order-analytics' AND event_id=$EVENT_ID;")" = 1 ] || fail 'duplicate changed analytics count'

FAILED=0
printf '%s\n' 'Docker Compose black-box E2E scenario completed.'
