import test from 'node:test';
import assert from 'node:assert/strict';
import { formatProviderRequest } from '../src/proxy.js';

test('formatProviderRequest generates correct headers and URL per provider', (t) => {
  const req = formatProviderRequest('openrouter', 'sk-or-123', {
    model: 'google/gemini-2.5-flash',
    messages: [{ role: 'user', content: 'hello' }]
  });

  assert.equal(req.url, 'https://openrouter.ai/api/v1/chat/completions');
  assert.equal(req.headers['Authorization'], 'Bearer sk-or-123');
  assert.equal(req.payload.model, 'google/gemini-2.5-flash');
});

test('formatProviderRequest supports gemini openai compatibility endpoint', (t) => {
  const req = formatProviderRequest('gemini', 'AIzaSy123', {
    model: 'gemini-2.5-flash',
    messages: [{ role: 'user', content: 'hello' }]
  });

  assert.equal(req.url, 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions');
  assert.equal(req.headers['Authorization'], 'Bearer AIzaSy123');
});
