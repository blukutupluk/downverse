import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../src/server.js';
import { initStore } from '../src/store.js';
import path from 'node:path';
import fs from 'node:fs/promises';

const TEST_DB = path.join(process.cwd(), 'tests', 'api-test-db.json');

test('Dashboard API CRUD operations', async (t) => {
  await fs.rm(TEST_DB, { force: true });
  await initStore(TEST_DB);
  const app = createServer({ dbPath: TEST_DB });
  const server = app.listen(0);
  const port = server.address().port;

  t.after(async () => {
    server.close();
    await fs.rm(TEST_DB, { force: true });
  });

  // Add key
  const addRes = await fetch(`http://localhost:${port}/api/keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider: 'groq', name: 'Test Groq', key: 'gsk_123' })
  });
  assert.equal(addRes.status, 201);
  const added = await addRes.json();
  assert.equal(added.name, 'Test Groq');

  // List keys
  const listRes = await fetch(`http://localhost:${port}/api/keys`);
  const keys = await listRes.json();
  assert.equal(keys.length, 1);

  // Update key
  const updateRes = await fetch(`http://localhost:${port}/api/keys/${added.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Updated Groq', status: 'active' })
  });
  assert.equal(updateRes.status, 200);
  const updated = await updateRes.json();
  assert.equal(updated.name, 'Updated Groq');

  // Get stats
  const statsRes = await fetch(`http://localhost:${port}/api/stats`);
  const stats = await statsRes.json();
  assert.ok(typeof stats.totalKeys === 'number');
  assert.ok(typeof stats.activeKeys === 'number');
  assert.ok(typeof stats.providers === 'object');

  // Delete key
  const delRes = await fetch(`http://localhost:${port}/api/keys/${added.id}`, {
    method: 'DELETE'
  });
  assert.equal(delRes.status, 204);

  const finalList = await fetch(`http://localhost:${port}/api/keys`);
  const finalKeys = await finalList.json();
  assert.equal(finalKeys.length, 0);
});