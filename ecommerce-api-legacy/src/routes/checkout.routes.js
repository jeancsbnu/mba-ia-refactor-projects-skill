const express = require('express');
const { processCheckout } = require('../controllers/checkout.controller');

const router = express.Router();

router.post('/api/checkout', async (req, res, next) => {
  try {
    const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
    const result = await processCheckout({ userName, email, password, courseId, cardNumber });
    res.status(200).json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
