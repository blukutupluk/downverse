import express from 'express';
import cors from 'cors';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { initStore, getKeys } from './store.js';
import { forwardRequest } from './proxy.js';
import apiRouter from './routes/api.js';

export function createServer(options = {}) {
  const app = express();

  // Middleware
  app.use(cors());
  app.use(express.json({ limit: '50mb' }));
  app.use(express.urlencoded({ extended: true, limit: '50mb' }));

  // Initialize store if path provided
  if (options.dbPath) {
    initStore(options.dbPath).catch(err => console.error('Store init failed:', err));
  }

  // Health check
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Auto-pair: buat token OpenCode sekali pakai (5 menit) lalu redirect ke GUI.
  // Token tidak pernah disimpan / dicetak — dipakai sekali oleh WebView.
  app.get('/auto-pair', async (req, res) => {
    try {
      const execFileAsync = promisify(execFile);
      const { stdout, stderr } = await execFileAsync('opencode', ['pair'], {
        timeout: 20000,
        env: process.env
      });
      const match = `${stdout}${stderr}`.match(
        /http:\/\/127\.0\.0\.1:\d+\/auth\/connect\/[A-Za-z0-9._~-]+/
      );
      if (!match) throw new Error('pairing link tidak ditemukan');

      const paired = await fetch(match[0]).then(r => r.json());
      if (!paired.token) throw new Error('token tidak ditemukan');

      const authToken = Buffer.from(`opencode:${paired.token}`).toString('base64');
      res.redirect(302, `http://127.0.0.1:49374/?auth_token=${encodeURIComponent(authToken)}`);
    } catch (err) {
      console.error('auto-pair failed:', err.message);
      res.status(503).type('text/plain').send('Gagal membuat pairing otomatis OpenCode');
    }
  });

  // Dashboard API routes
  app.use('/api', apiRouter);

  // OpenAI compatible endpoints
  app.get('/v1/models', (req, res) => {
    const allKeys = getKeys();
    const providers = [...new Set(allKeys.map(k => k.provider))];
    
    const models = providers.map(provider => {
      const providerKeys = allKeys.filter(k => k.provider === provider && k.status === 'active');
      return {
        id: provider,
        object: 'model',
        created: Math.floor(Date.now() / 1000),
        owned_by: 'local-manager',
        provider,
        activeKeys: providerKeys.length,
        totalKeys: allKeys.filter(k => k.provider === provider).length
      };
    });

    res.json({
      object: 'list',
      data: models
    });
  });

  app.post('/v1/chat/completions', async (req, res) => {
    const { model, ...body } = req.body;

    if (!model) {
      return res.status(400).json({
        error: {
          message: 'Model is required',
          type: 'invalid_request_error'
        }
      });
    }

    // Determine provider from model name or use a default
    // Format: provider/model-name or just provider
    let provider = model.split('/')[0];
    if (!['openrouter', 'groq', 'deepseek', 'gemini', 'together'].includes(provider)) {
      // Try to find a provider with active keys
      const allKeys = getKeys();
      const activeProviders = [...new Set(allKeys.filter(k => k.status === 'active').map(k => k.provider))];
      if (activeProviders.length > 0) {
        provider = activeProviders[0];
      } else {
        return res.status(400).json({
          error: {
            message: `Unknown provider in model: ${model}. Use format: provider/model-name`,
            type: 'invalid_request_error'
          }
        });
      }
    }

    const isStream = body.stream === true;

    try {
      await forwardRequest({ provider, body: req.body, isStream, res });
    } catch (err) {
      if (err.statusCode === 429) {
        res.set('Retry-After', err.retryAfter || 60);
        return res.status(429).json({
          error: {
            message: err.message || 'All API keys are rate limited. Please try again later.',
            type: 'rate_limit_exceeded',
            retry_after: err.retryAfter || 60
          }
        });
      }
      
      console.error('Forward request error:', err);
      res.status(500).json({
        error: {
          message: err.message || 'Internal server error',
          type: 'internal_error'
        }
      });
    }
  });

  // Serve static files for dashboard
  app.use(express.static('public'));

  return app;
}