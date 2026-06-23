const logger = {
  info: (msg, data = {}) =>
    console.log(JSON.stringify({ level: 'info', msg, ...data, ts: new Date().toISOString() })),
  warn: (msg, data = {}) =>
    console.warn(JSON.stringify({ level: 'warn', msg, ...data, ts: new Date().toISOString() })),
  error: (msg, err = {}) =>
    console.error(JSON.stringify({ level: 'error', msg, error: err.message || String(err), ts: new Date().toISOString() })),
};

module.exports = logger;
