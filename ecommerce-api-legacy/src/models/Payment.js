const { getDb } = require('../database');

const create = (enrollmentId, amount, status) =>
  getDb().run(
    "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
    [enrollmentId, amount, status]
  );

module.exports = { create };
