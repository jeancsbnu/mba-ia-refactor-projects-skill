const express = require('express');
const { deleteUser } = require('../controllers/users.controller');

const router = express.Router();

router.delete('/api/users/:id', async (req, res, next) => {
  try {
    const result = await deleteUser(Number(req.params.id));
    res.status(200).json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
