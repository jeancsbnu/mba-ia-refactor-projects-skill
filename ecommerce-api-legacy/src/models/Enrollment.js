const { getDb } = require('../database');

const create = (userId, courseId) =>
  getDb().run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, courseId]);

module.exports = { create };
