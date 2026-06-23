const bcrypt = require('bcryptjs');
const { HttpError } = require('../middlewares/errorHandler');
const User = require('../models/User');
const Course = require('../models/Course');
const Enrollment = require('../models/Enrollment');
const Payment = require('../models/Payment');
const AuditLog = require('../models/AuditLog');
const logger = require('../utils/logger');

const PaymentStatus = { PAID: 'PAID', DENIED: 'DENIED' };

async function processCheckout({ userName, email, password, courseId, cardNumber }) {
  if (!userName || !email || !courseId || !cardNumber) {
    throw new HttpError(400, 'Campos obrigatórios: usr, eml, c_id, card');
  }
  if (!password) {
    throw new HttpError(400, 'Senha é obrigatória para criar uma conta');
  }

  const course = await Course.findActiveById(courseId);
  if (!course) throw new HttpError(404, 'Curso não encontrado');

  let user = await User.findByEmail(email);
  if (!user) {
    const passHash = await bcrypt.hash(password, 10);
    const result = await User.create(userName, email, passHash);
    user = { id: result.lastID };
  }

  const paymentStatus = cardNumber.startsWith('4') ? PaymentStatus.PAID : PaymentStatus.DENIED;
  if (paymentStatus === PaymentStatus.DENIED) throw new HttpError(400, 'Pagamento recusado');

  const enrollment = await Enrollment.create(user.id, courseId);
  await Payment.create(enrollment.lastID, course.price, paymentStatus);
  await AuditLog.create(`Checkout curso ${courseId} por usuário ${user.id}`);

  logger.info('Checkout realizado', { userId: user.id, courseId, enrollmentId: enrollment.lastID });

  return { msg: 'Sucesso', enrollment_id: enrollment.lastID };
}

module.exports = { processCheckout };
