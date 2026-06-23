const { HttpError } = require('../middlewares/errorHandler');
const User = require('../models/User');
const logger = require('../utils/logger');

async function deleteUser(userId) {
  const user = await User.findById(userId);
  if (!user) throw new HttpError(404, 'Usuário não encontrado');
  await User.deleteById(userId);
  logger.info('Usuário deletado', { userId });
  return { msg: 'Usuário deletado' };
}

module.exports = { deleteUser };
