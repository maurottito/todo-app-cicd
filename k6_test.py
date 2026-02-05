import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.05'],
    http_reqs: ['rate>20'],
  },
};

const BASE_URL = 'http://localhost';

export default function() {
  // Test health endpoint
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status 200': (r) => r.status === 200,
    'health check response contains healthy': (r) => r.body.includes('healthy'),
  });

  // Test list tasks endpoint
  let tasksRes = http.get(`${BASE_URL}/tasks`);
  check(tasksRes, {
    'tasks list status 200': (r) => r.status === 200,
    'tasks response is JSON': (r) => r.headers['Content-Type'].includes('application/json'),
  });

  // Test add task endpoint
  const payload = JSON.stringify({
    task: `Load Test Task ${Date.now()}`,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  let addRes = http.post(`${BASE_URL}/add`, payload, params);
  check(addRes, {
    'add task status 201': (r) => r.status === 201,
    'add task returns task_id': (r) => JSON.parse(r.body).task_id !== undefined,
  });

  sleep(1);
}