================================
RELATÓRIO DE AUDITORIA ARQUITETURAL
================================
Projeto: ecommerce-api-legacy
Stack:   Node.js + Express 4.18 (SQLite in-memory)
Arquivos: 3 analisados | ~182 linhas de código

## Resumo
CRITICAL: 4 | HIGH: 8 | MEDIUM: 4 | LOW: 3
Checagem de APIs deprecated: executada — nenhum encontrado

## Findings

### [CRITICAL] God Class / God Module
Arquivo: src/AppManager.js:1-142
Descrição: A classe `AppManager` concentra criação do banco, schema, seeds, definição das três rotas, validação, regra de checkout, processamento de pagamento, geração de relatório financeiro e auditoria.
Impacto: Qualquer mudança tem raio de explosão grande; nada testável em isolamento; impossível evoluir camadas independentemente.
Recomendação: Quebrar em models/ (esquema e queries), controllers/ (regra de checkout, relatório, exclusão), routes/ (definição HTTP) e config/ (boot do DB).

### [CRITICAL] Credenciais / Segredos Hardcoded
Arquivo: src/utils.js:1-7
Descrição: `dbUser`, `dbPass` (`"senha_super_secreta_prod_123"`), `paymentGatewayKey` (`"pk_live_1234567890abcdef"`) e `smtpUser` estão como string literal em código versionado.
Impacto: Segredos entram no histórico Git, ficam visíveis a qualquer leitor do repo e exigem rotação custosa após vazamento.
Recomendação: Mover para `process.env.*` carregados via `dotenv`, manter um `.env.example` no repo e falhar rápido no boot se variáveis críticas estiverem ausentes.

### [CRITICAL] Armazenamento de Senha com Hash Fraco
Arquivo: src/utils.js:17-23
Descrição: A função `badCrypto` faz loop de `Buffer.from(pwd).toString('base64')` e devolve os 10 primeiros caracteres — não há salt, não há KDF e o espaço de saída é minúsculo.
Impacto: Qualquer dump do banco expõe senhas trivialmente reversíveis por força bruta; rainbow tables quebram em segundos.
Recomendação: Substituir por `bcrypt`/`argon2` com cost factor adequado e salt por usuário; nunca logar nem retornar o campo de senha.

### [CRITICAL] Armazenamento de Senha com Hash Fraco (uso + fallback inseguro)
Arquivo: src/AppManager.js:68
Descrição: Handler de checkout chama `badCrypto(p || "123456")`, ou seja, se o cliente não enviar senha o sistema cria a conta com a senha padrão `"123456"`.
Impacto: Usuários criados sem senha viram contas de acesso público; combinado ao hash fraco, equivale a contas sem credencial.
Recomendação: Exigir senha como campo obrigatório validado na fronteira; usar bcrypt/argon2 no controller; rejeitar a requisição (`400`) se ausente.

### [HIGH] Lógica de Negócio em Controllers / Rotas (checkout)
Arquivo: src/AppManager.js:28-78
Descrição: O handler `POST /api/checkout` faz validação, busca de curso, criação condicional de usuário, processamento de pagamento, criação de matrícula, registro em payments, gravação de audit log e formatação de resposta — tudo dentro de uma cascata de callbacks aninhados.
Impacto: Impossível reusar ou testar a regra de checkout fora do HTTP; mudanças em qualquer etapa exigem mexer no handler inteiro.
Recomendação: Extrair `CheckoutController` (ou service) que receba dependências (repositórios de user/course/enrollment/payment, gateway de pagamento) e oriente o fluxo; a rota só faz parse → chama controller → traduz resultado para HTTP.

### [HIGH] Lógica de Negócio em Controllers / Rotas (financial-report)
Arquivo: src/AppManager.js:80-129
Descrição: O handler `GET /api/admin/financial-report` agrega cursos, matrículas, usuários e pagamentos com lógica de orquestração e somatório manual via contadores `coursesPending`/`enrPending`.
Impacto: Lógica de agregação intestável; concorrência e respostas dependem de mutação de contadores; difícil evoluir a regra.
Recomendação: Mover a agregação para `ReportController`/`ReportService`; o controller monta uma única query agregada (ou usa repositórios) e a rota apenas serializa.

### [HIGH] Acoplamento Forte — sem Injeção de Dependência
Arquivo: src/AppManager.js:7
Descrição: O construtor de `AppManager` instancia diretamente `new sqlite3.Database(':memory:')` e todos os métodos consomem `this.db` concreto.
Impacto: Não há como substituir o banco por um fake em testes; trocar de SQLite para outro engine requer mexer no AppManager inteiro.
Recomendação: Receber a conexão do banco (ou um repositório) por construtor; conectar uma única vez no entry point (composition root) e injetar para baixo.

### [HIGH] Estado Global Mutável entre Requisições
Arquivo: src/utils.js:9-10
Descrição: `globalCache = {}` é mutado por `logAndCache` em cada checkout, e `totalRevenue` é exportado como contador no nível do módulo.
Impacto: Vazamento de estado entre requisições/tenants e potenciais race conditions sob concorrência; cache cresce sem bound (memory leak).
Recomendação: Eliminar `globalCache`/`totalRevenue` ou substituir por estado persistido no banco; se cache for necessário, usar instância injetada por requisição.

### [HIGH] Tratamento de Erro Ausente ou Silenciado (audit log)
Arquivo: src/AppManager.js:57
Descrição: O callback do `INSERT INTO audit_logs` recebe `err` mas ignora silenciosamente — a resposta `200 Sucesso` é enviada mesmo se a auditoria falhar.
Impacto: Falhas de auditoria passam batido, contrato de sucesso fica inconsistente com o estado real, sem rastreabilidade.
Recomendação: Centralizar tratamento via middleware Express; logar falhas de side-effect e decidir explicitamente se devem invalidar a transação.

### [HIGH] Tratamento de Erro Ausente ou Silenciado (delete user)
Arquivo: src/AppManager.js:131-137
Descrição: O handler `DELETE /api/users/:id` ignora `err` do banco e devolve sempre 200, com mensagem confessando que matrículas e pagamentos ficam órfãos.
Impacto: Erro real do banco vira sucesso para o cliente; integridade referencial quebra a cada chamada.
Recomendação: Propagar erro via middleware central; envolver em transação que apague (ou anonimize) dados dependentes; retornar 4xx/5xx adequados.

### [HIGH] Autenticação / Autorização Ausente — endpoint administrativo
Arquivo: src/AppManager.js:80
Descrição: `GET /api/admin/financial-report` expõe receita por curso e lista de alunos sem nenhum middleware de autenticação ou autorização.
Impacto: Qualquer cliente da internet acessa dados financeiros e PII de alunos sem credencial.
Recomendação: Middleware de autenticação (token/JWT) e autorização por papel (`admin`) aplicada à rota; nunca incluir campos sensíveis no payload.

### [HIGH] Autenticação / Autorização Ausente — exclusão de usuário
Arquivo: src/AppManager.js:131
Descrição: `DELETE /api/users/:id` não exige autenticação nem autoriza o requisitante a apagar a conta-alvo.
Impacto: Qualquer pessoa pode deletar qualquer usuário; operação destrutiva sem rastreabilidade.
Recomendação: Mesmo middleware de auth/admin; restringir self-delete a sessão própria e exigir papel privilegiado para exclusão de terceiros.

### [MEDIUM] Query N+1
Arquivo: src/AppManager.js:89-127
Descrição: O relatório financeiro itera cursos e, para cada curso, faz `SELECT` de enrollments; para cada enrollment, faz dois `SELECT` adicionais (usuário e pagamento).
Impacto: Latência cresce linearmente com o produto (cursos × matrículas); inviável conforme o banco cresce.
Recomendação: Substituir por uma única query agregada com `JOIN` entre courses/enrollments/users/payments e `SUM(amount)` agrupado por curso.

### [MEDIUM] Validação de Input Ausente
Arquivo: src/AppManager.js:29-35
Descrição: O handler lê `req.body.usr/eml/pwd/c_id/card` direto, sem checar formato de e-mail, tipo de `c_id`, tamanho/Luhn do cartão, ou exigência de senha (que ainda é encoberta pelo fallback `"123456"`).
Impacto: Inputs malformados podem provocar 500, dados inconsistentes no banco e abuso (cartões falsos aceitos).
Recomendação: Validar com `zod`/`joi`/`express-validator` na fronteira do controller; responder 400 estruturado quando inválido.

### [MEDIUM] Logging Inadequado / Vazamento de PII e Segredos
Arquivo: src/AppManager.js:45
Descrição: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` grava número de cartão de crédito **e** chave do gateway de pagamento no stdout a cada checkout.
Impacto: Logs viram repositório de PII e segredos; qualquer agregador (CloudWatch, Sentry, journald) os captura — violação direta de PCI/LGPD.
Recomendação: Trocar `console.log` por logger estruturado (`pino`/`winston`) com níveis; mascarar cartão (apenas BIN + últimos 4) e nunca logar segredos.

### [MEDIUM] Logging Inadequado
Arquivo: src/utils.js:12-15
Descrição: `logAndCache` usa `console.log` como log de produção e ainda combina log com mutação de cache global.
Impacto: Logs sem nível, sem correlação por request-id e acoplados a efeito colateral; difícil distinguir info de erro em produção.
Recomendação: Separar logging (logger estruturado) de cache (estrutura própria, injetada); remover `console.log` puro do caminho de produção.

### [LOW] Magic Numbers / Strings
Arquivo: src/AppManager.js:46
Descrição: O status do pagamento é decidido por `cc.startsWith("4") ? "PAID" : "DENIED"`; o literal `"4"` codifica regra de negócio sem nome.
Impacto: Intenção opaca para o leitor; risco de divergência se a regra for repetida.
Recomendação: Substituir por chamada a um `PaymentGateway` (mock) com constantes nomeadas (`PaymentStatus.PAID`/`DENIED`); centralizar a regra.

### [LOW] Nomenclatura Ruim
Arquivo: src/AppManager.js:29-33
Descrição: Variáveis-chave do checkout estão como `u`, `e`, `p`, `cid`, `cc`; igualmente `enr`, `c` mais abaixo.
Impacto: Reduz a legibilidade exatamente no caminho mais sensível (cartão e senha).
Recomendação: Renomear para `userName`, `email`, `password`, `courseId`, `cardNumber` etc., já no destrinchamento do body.

### [LOW] Código Morto
Arquivo: src/utils.js:10
Descrição: `let totalRevenue = 0` é declarado e exportado, mas nunca lido nem mutado por nenhum consumidor.
Impacto: Adiciona ruído e sugere acoplamento global inexistente; convida futuros usos indevidos.
Recomendação: Remover a variável e o export; o histórico Git preserva.

================================
Total: 19 findings
================================

Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
