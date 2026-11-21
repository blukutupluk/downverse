import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const CLI = path.join(process.cwd(), 'src', 'opencode-account-cli.js');

function run(args, env = {}) {
  return spawnSync(process.execPath, [CLI, ...args], {
    encoding: 'utf8',
    env: { ...process.env, ...env }
  });
}

test('CLI with no args prints usage and exits 0', (t) => {
  const res = run([]);
  assert.equal(res.status, 0);
  assert.match(res.stdout, /add/);
  assert.match(res.stdout, /list/);
  assert.match(res.stdout, /switch/);
});

test('CLI rejects unknown command with exit 1', (t) => {
  const res = run(['bogus-command']);
  assert.equal(res.status, 1);
  assert.match(res.stderr + res.stdout, /perintah tidak dikenal|unknown/i);
});

test('CLI list shows email but never the token', async (t) => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'oa-test-'));
  const db = path.join(dir, 'test.db');
  const token = 'SECRET_ACCESS_TOKEN_XYZ';

  await fs.writeFile(path.join(dir, 'seed.py'), `
import sqlite3, json, sys
c = sqlite3.connect(sys.argv[1])
c.execute('CREATE TABLE credential (id TEXT, integration_id TEXT, label TEXT, value TEXT, active INTEGER)')
v = json.dumps({'type':'oauth','access':'${token}','refresh':'REFRESH_XYZ','metadata':{'email':'user@example.com','orgName':'Personal'}})
c.execute('INSERT INTO credential VALUES (?,?,?,?,?)', ('cred_1','opencode','Personal',v,1))
c.commit()
`);
  execFileSync('python3', [path.join(dir, 'seed.py'), db]);

  t.after(async () => fs.rm(dir, { recursive: true, force: true }));

  const res = run(['list'], { OPENCODE_DB: db });
  assert.equal(res.status, 0, res.stderr);
  assert.match(res.stdout, /user@example\.com/);
  assert.doesNotMatch(res.stdout + res.stderr, /SECRET_ACCESS_TOKEN_XYZ/);
  assert.doesNotMatch(res.stdout + res.stderr, /REFRESH_XYZ/);
});
