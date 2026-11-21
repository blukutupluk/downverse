#!/usr/bin/env node
import { createServer } from '../src/server.js';
import { initStore } from '../src/store.js';

const args = process.argv.slice(2);
const port = parseInt(args.find(a => a.startsWith('--port='))?.split('=')[1] || '3000');
const dbPath = args.find(a => a.startsWith('--db='))?.split('=')[1];

async function main() {
  try {
    // Initialize store first
    await initStore(dbPath);

    // Create and start server
    const app = createServer({ dbPath });
    const server = app.listen(port, () => {
      console.log(`🚀 API Key Manager server running at http://localhost:${port}`);
      console.log(`📊 Dashboard: http://localhost:${port}`);
      console.log(`🔌 OpenAI API: http://localhost:${port}/v1`);
      console.log(`💚 Health check: http://localhost:${port}/health`);
      console.log('');
      console.log('Press Ctrl+C to stop');
    });

    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n👋 Shutting down...');
      server.close(() => {
        console.log('Server closed');
        process.exit(0);
      });
    });

    process.on('SIGTERM', () => {
      server.close(() => {
        process.exit(0);
      });
    });
  } catch (err) {
    console.error('❌ Failed to start server:', err.message);
    process.exit(1);
  }
}

main();