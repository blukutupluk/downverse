import { createServer } from './src/server.js';
import { initStore } from './src/store.js';

const port = parseInt(process.env.PORT || '3000', 10);
const dbPath = process.env.DB_PATH;

async function start() {
  try {
    await initStore(dbPath);

    const app = createServer({ dbPath });
    const server = app.listen(port, () => {
      console.log(`🚀 API Key Manager server running at http://localhost:${port}`);
      console.log(`📊 Dashboard: http://localhost:${port}`);
      console.log(`🔌 OpenAI API: http://localhost:${port}/v1`);
      console.log(`💚 Health check: http://localhost:${port}/health`);
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