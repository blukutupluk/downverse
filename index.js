import { createServer } from './src/server.js';
import { initStore } from './src/store.js';
import { getLanIp } from './src/net.js';

const port = parseInt(process.env.PORT || '3000', 10);
const host = process.env.HOST || '0.0.0.0';
const dbPath = process.env.DB_PATH;

async function start() {
  try {
    await initStore(dbPath);

    const app = createServer({ dbPath });
    const server = app.listen(port, host, () => {
      const lanIp = getLanIp();
      console.log(`🚀 API Key Manager server running at http://localhost:${port}`);
      console.log(`📊 Dashboard (HP): http://127.0.0.1:${port}`);
      if (lanIp) console.log(`🌐 Dashboard (LAN): http://${lanIp}:${port}`);
      console.log(`🔌 OpenAI API: http://127.0.0.1:${port}/v1`);
      console.log(`💚 Health check: http://127.0.0.1:${port}/health`);
    });

    const shutdown = () => {
      console.log('\n👋 Shutting down...');
      server.close(() => {
        console.log('Server closed');
        process.exit(0);
      });
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  } catch (err) {
    console.error('❌ Failed to start server:', err.message);
    process.exit(1);
  }
}

start();