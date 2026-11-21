import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { initStore, getKeys, addKey, updateKey, deleteKey, getNextActiveKey, markKeyCooldown, markKeyDisabled } from '../src/store.js';

const TEST_DB = path.join(process.cwd(), 'tests', 'test-db.json');

test('Store operations and key rotation', async (t) => {
  await fs.rm(TEST_DB, { force: true });
  await initStore(TEST_DB);

  t.after(async () => {
    await fs.rm(TEST_DB, { force: true });
  });

  const k1 = addKey({ provider: 'gemini', name: 'Key 1', key: 'AIzaSy1' });
  const k2 = addKey({ provider: 'gemini', name: 'Key 2', key: 'AIzaSy2' });

  assert.equal(getKeys('gemini').length, 2);
  
  const first = getNextActiveKey('gemini');
  assert.equal(first.id, k1.id);

  markKeyCooldown(k1.id, 60000);
  const second = getNextActiveKey('gemini');
  assert.equal(second.id, k2.id);

  markKeyDisabled(k2.id, 'Invalid Key');
  const third = getNextActiveKey('gemini');
  assert.equal(third, null);

  assert.equal(deleteKey(k1.id), true);
  assert.equal(getKeys('gemini').length, 1);
});
