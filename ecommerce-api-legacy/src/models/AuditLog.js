const { getDb } = require('../database');

const create = (action) =>
  getDb().run("INSERT INTO audit_logs (action) VALUES (?)", [action]);

module.exports = { create };
