import test from 'node:test';
import assert from 'node:assert/strict';
import { getLanIp, detectVpn, probeServer } from '../src/net.js';

test('getLanIp returns a valid IPv4 address or null', (t) => {
  const ip = getLanIp();
  if (ip !== null) {
    assert.match(ip, /^\d{1,3}(\.\d{1,3}){3}$/);
    assert.notEqual(ip, '127.0.0.1');
  }
});

test('detectVpn returns an array (tunnel interfaces only)', (t) => {
  const vpns = detectVpn();
  assert.ok(Array.isArray(vpns));
  for (const v of vpns) {
    assert.match(v.name, /^(tun|ppp|wg|ipsec|tap)/i);
  }
});

test('probeServer reports unreachable for closed port without throwing', async (t) => {
  const result = await probeServer('127.0.0.1', 59999, 1500);
  assert.equal(result.reachable, false);
  assert.ok(result.error);
});
