const logger = require('../utils/logger');

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  if (status >= 500) logger.error('Erro inesperado', err);
  res.status(status).json({ error: err.message });
}

module.exports = { HttpError, errorHandler };
