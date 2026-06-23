const { getDb } = require('../database');

const findActiveById = (id) =>
  getDb().get("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);

module.exports = { findActiveById };
