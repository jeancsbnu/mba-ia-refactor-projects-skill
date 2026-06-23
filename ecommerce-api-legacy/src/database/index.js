const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const { config } = require('../config');
const logger = require('../utils/logger');

let db;

const run = (sql, params = []) =>
  new Promise((res, rej) =>
    db.run(sql, params, function (err) { err ? rej(err) : res({ lastID: this.lastID, changes: this.changes }); })
  );

const get = (sql, params = []) =>
  new Promise((res, rej) =>
    db.get(sql, params, (err, row) => err ? rej(err) : res(row))
  );

const all = (sql, params = []) =>
  new Promise((res, rej) =>
    db.all(sql, params, (err, rows) => err ? rej(err) : res(rows))
  );

function getDb() {
  if (!db) throw new Error('Banco não inicializado. Chame initDb() primeiro.');
  return { run, get, all };
}

async function initDb() {
  db = new sqlite3.Database(config.DB_PATH);
  await run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL, pass TEXT NOT NULL
  )`);
  await run(`CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
    price REAL NOT NULL, active INTEGER DEFAULT 1
  )`);
  await run(`CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, course_id INTEGER NOT NULL
  )`);
  await run(`CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_id INTEGER NOT NULL,
    amount REAL NOT NULL, status TEXT NOT NULL
  )`);
  await run(`CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  const row = await get("SELECT COUNT(*) AS count FROM courses");
  if (row.count === 0) {
    const leonanHash = await bcrypt.hash('123', 10);
    await run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", ['Leonan', 'leonan@fullcycle.com.br', leonanHash]);
    await run("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)", ['Clean Architecture', 997.00, 1]);
    await run("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)", ['Docker', 497.00, 1]);
    await run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [1, 1]);
    await run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [1, 997.00, 'PAID']);
    logger.info('Banco inicializado com dados de seed.');
  }
}

module.exports = { initDb, getDb };
