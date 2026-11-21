import test from 'node:test';
import assert from 'node:assert/strict';
import { parseCredentialValue, sanitizeCredential, formatCredentialTable } from '../src/opencode-accounts.js';

const SAMPLE_VALUE = JSON.stringify({
  type: 'oauth',
  methodID: 'device',
  refresh: 'secret-refresh-token',
  access: 'secret-access-token',
  expires: 1797731802808,
  metadata: {
    server: 'https://opencode.ai/console',
    accountID: 'user_01ABC',
    email: 'user@example.com',
    orgID: 'org_01XYZ',
    orgName: 'Personal'
  }
});

test('parseCredentialValue extracts email, org and account without leaking tokens', (t) => {
  const parsed = parseCredentialValue(SAMPLE_VALUE);
  assert.equal(parsed.email, 'user@example.com');
  assert.equal(parsed.orgName, 'Personal');
  assert.equal(parsed.accountID, 'user_01ABC');
  assert.equal(parsed.type, 'oauth');
  assert.equal(parsed.access, undefined);
  assert.equal(parsed.refresh, undefined);
});

test('parseCredentialValue returns nullish fields for malformed JSON', (t) => {
  const parsed = parseCredentialValue('not-json');
  assert.equal(parsed.email, null);
  assert.equal(parsed.orgName, null);
});

test('sanitizeCredential removes token-like fields', (t) => {
  const row = {
    id: 'cred_1',
    integration_id: 'opencode',
    label: 'Personal',
    value: SAMPLE_VALUE,
    active: 1,
    access: 'secret',
    refresh: 'secret',
    token: 'secret'
  };
  const clean = sanitizeCredential(row);
  assert.equal(clean.id, 'cred_1');
  assert.equal(clean.label, 'Personal');
  assert.equal(clean.active, 1);
  assert.equal(clean.value, undefined);
  assert.equal(clean.access, undefined);
  assert.equal(clean.refresh, undefined);
  assert.equal(clean.token, undefined);
  assert.equal(clean.email, 'user@example.com');
});

test('formatCredentialTable contains email and active marker but no token string', (t) => {
  const rows = [
    sanitizeCredential({ id: 'cred_1', integration_id: 'opencode', label: 'Personal', value: SAMPLE_VALUE, active: 1 }),
    sanitizeCredential({ id: 'cred_2', integration_id: 'opencode', label: 'Other', value: SAMPLE_VALUE, active: 0 })
  ];
  const table = formatCredentialTable(rows);
  assert.match(table, /user@example\.com/);
  assert.match(table, /Personal/);
  assert.match(table, /AKTIF/);
  assert.doesNotMatch(table, /secret-access-token/);
  assert.doesNotMatch(table, /secret-refresh-token/);
});

test('formatCredentialTable handles empty list', (t) => {
  assert.match(formatCredentialTable([]), /tidak ada/i);
});
