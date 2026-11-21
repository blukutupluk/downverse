import test from 'node:test';
import assert from 'node:assert/strict';
import { generateOpenCodeConfig } from '../bin/integrate-opencode.js';

test('generateOpenCodeConfig returns valid custom provider config', (t) => {
  const config = generateOpenCodeConfig('http://localhost:3000');
  assert.ok(config.provider['local-manager']);
  assert.equal(config.provider['local-manager'].options.baseURL, 'http://localhost:3000/v1');
  assert.equal(config.provider['local-manager'].options.apiKey, 'local-manager');
  assert.ok(Array.isArray(config.provider['local-manager'].models));
});