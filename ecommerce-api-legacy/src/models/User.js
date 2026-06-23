const { getDb } = require('../database');

const findByEmail = (email) => getDb().get("SELECT * FROM users WHERE email = ?", [email]);
const findById = (id) => getDb().get("SELECT id, name, email FROM users WHERE id = ?", [id]);
const create = (name, email, passHash) =>
  getDb().run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, passHash]);
const deleteById = (id) => getDb().run("DELETE FROM users WHERE id = ?", [id]);

module.exports = { findByEmail, findById, create, deleteById };
