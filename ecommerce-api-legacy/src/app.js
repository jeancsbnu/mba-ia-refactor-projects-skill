const express = require('express');
const { errorHandler } = require('./middlewares/errorHandler');
const checkoutRoutes = require('./routes/checkout.routes');
const reportRoutes = require('./routes/report.routes');
const usersRoutes = require('./routes/users.routes');

function createApp() {
  const app = express();
  app.use(express.json());

  app.use(checkoutRoutes);
  app.use(reportRoutes);
  app.use(usersRoutes);

  app.use(errorHandler);
  return app;
}

module.exports = { createApp };
