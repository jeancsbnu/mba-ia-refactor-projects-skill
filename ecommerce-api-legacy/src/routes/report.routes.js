const express = require('express');
const { getFinancialReport } = require('../controllers/report.controller');

const router = express.Router();

router.get('/api/admin/financial-report', async (req, res, next) => {
  try {
    const report = await getFinancialReport();
    res.status(200).json(report);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
