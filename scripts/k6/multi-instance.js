import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL || 'http://nginx:8080';
const fixtureUserId = __ENV.FIXTURE_USER_ID;
const fixtureMenuId = __ENV.FIXTURE_MENU_ID;

export const options = {
  summaryTrendStats: ['med', 'p(95)', 'p(99)'],
  scenarios: {
    normal_reads: {
      executor: 'constant-vus',
      vus: 2,
      duration: '4s',
      exec: 'normalReads',
    },
    same_user_contention: {
      executor: 'constant-vus',
      vus: 2,
      duration: '4s',
      startTime: '5s',
      exec: 'sameUserContention',
    },
  },
  thresholds: {
    checks: ['rate == 1'],
    http_req_failed: ['rate == 0'],
  },
};

function commonChecks(response, label) {
  return check(response, {
    [`${label}: status is 200`]: (r) => r.status === 200,
    [`${label}: upstream is identified`]: (r) => Boolean(r.headers['X-Upstream-Addr']),
  });
}

export function normalReads() {
  commonChecks(http.get(`${baseUrl}/api/v1/menus`), 'normal read');
  sleep(0.2);
}

export function sameUserContention() {
  const response = http.post(
    `${baseUrl}/api/v1/orders`,
    JSON.stringify({ userId: Number(fixtureUserId), menuId: Number(fixtureMenuId) }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  commonChecks(response, 'same-user order');
  sleep(0.3);
}

function metricValue(data, metric, field) {
  return data.metrics[metric] && data.metrics[metric].values[field];
}

export function handleSummary(data) {
  const httpRequests = metricValue(data, 'http_reqs', 'count');
  const httpRequestFailureRate = metricValue(data, 'http_req_failed', 'rate');
  const summary = {
    checks: metricValue(data, 'checks', 'passes'),
    checkFailures: metricValue(data, 'checks', 'fails'),
    httpRequests,
    requestRatePerSecond: metricValue(data, 'http_reqs', 'rate'),
    // http_req_failed is a Rate: its `fails` field counts false samples (successful requests).
    httpRequestFailures: Math.round(httpRequests * httpRequestFailureRate),
    httpRequestFailureRate,
    latencyMs: {
      p50: metricValue(data, 'http_req_duration', 'med'),
      p95: metricValue(data, 'http_req_duration', 'p(95)'),
      p99: metricValue(data, 'http_req_duration', 'p(99)'),
    },
  };
  return {
    '/results/k6-summary.json': JSON.stringify(summary, null, 2),
    stdout: `K6_RESULT ${JSON.stringify(summary)}\n`,
  };
}
