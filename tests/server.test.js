import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../src/server.js';
import { initStore } from '../src/store.js';

test('GET /v1/models returns available models list', async (t) => {
  await initStore();
  const app = createServer();
  const server = app.listen(0);
  const port = server.address().port;

  t.after(() => server.close());

  const res = await fetch(`http://localhost:${port}/v1/models`);
  const data = await res.json();
  
  assert.equal(res.status, 200);
  assert.ok(Array.isArray(data.data));
});

test('POST /v1/chat/completions returns 400 without provider', async (t) => {
  await initStore();
  const app = createServer();
  const server = app.listen(0);
  const port = server.address().port;

  t.after(() => server.close());

  const res = await fetch(`http://localhost:${port}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'test', messages: [{ role: 'user', content: 'hi' }] })
  });
  
  assert.equal(res.status, 400);
});