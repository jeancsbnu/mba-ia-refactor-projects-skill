const config = {
  PORT: process.env.PORT || 3000,
  DB_PATH: process.env.DB_PATH || ':memory:',
  PAYMENT_GATEWAY_KEY: process.env.PAYMENT_GATEWAY_KEY || 'dev-gateway-key',
  SMTP_USER: process.env.SMTP_USER || '',
  SMTP_PASS: process.env.SMTP_PASS || '',
};

if (process.env.NODE_ENV === 'production') {
  const required = ['PAYMENT_GATEWAY_KEY', 'SMTP_USER', 'SMTP_PASS'];
  for (const key of required) {
    if (!config[key]) throw new Error(`Variável de ambiente obrigatória ausente: ${key}`);
  }
}

module.exports = { config };
