const { initDb } = require('./database');
const { createApp } = require('./app');
const { config } = require('./config');
const logger = require('./utils/logger');

async function start() {
  await initDb();
  const app = createApp();
  app.listen(config.PORT, () => {
    logger.info(`LMS API running on port ${config.PORT}`);
  });
}

start().catch((err) => {
  console.error('Falha ao iniciar o servidor:', err.message);
  process.exit(1);
});
