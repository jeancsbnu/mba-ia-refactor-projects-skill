# Guidelines de Arquitetura MVC (alvo da Fase 3)

Este arquivo define a arquitetura alvo para a qual toda refatoração converge. A skill é agnóstica de tecnologia, então as **responsabilidades** de cada camada são estáveis entre stacks, mesmo quando os **nomes das pastas** variam por convenção.

---

## As três camadas + módulos de apoio

### 1. Models (`models/`)
**Responsabilidade:** representar dados persistentes e as regras que os governam.

Permitido nesta camada:
- Declaração de schema (classes ORM, definições de tabela).
- Validação de campo (comprimento, tipo, formato).
- Métodos de acesso a dados que consultam/atualizam a própria tabela (`find_by_id`, `find_active`, `save`, `delete`).
- Invariantes de domínio que se aplicam a uma única entidade (ex.: `Pedido.total = soma(itens)`).

Não permitido nesta camada:
- Formato de request/response HTTP.
- Workflows cross-entity (vão para controllers).
- Formatação de view / serialização além de um `to_dict()` simples.

Um arquivo por aggregate root: `models/usuario.py`, `models/produto.py`, `models/pedido.py` (ou `.js`).

---

### 2. Views ou Routes (`views/` para templates Flask, `routes/` para APIs)
**Responsabilidade:** traduzir entre HTTP (ou outro transporte) e a camada de controllers.

Permitido:
- Declarações de rota (`@app.route`, `router.get(...)`).
- Parsing do request recebido (query params, body, headers).
- Invocar o controller certo com inputs já parseados.
- Mapear retorno do controller para resposta HTTP (status code + body).
- Plugar middleware de autenticação nas rotas.

Não permitido:
- Lógica de negócio, queries de banco, workflows multi-step, side-effects.
- Mais de ~15 linhas por função de rota.

Uma função de rota deve se ler como uma receita: parse → chama controller → retorna.

Para APIs Flask, a camada tipicamente se chama `routes/` (sem templates Jinja); para apps Flask full-stack com HTML, `views/` é apropriado. Qualquer um serve — escolher o que combina com o domínio.

---

### 3. Controllers (`controllers/`)
**Responsabilidade:** orquestrar casos de uso e aplicar regras de negócio.

Permitido:
- Coordenar múltiplos models dentro de um único caso de uso.
- Validar regras cross-entity (ex.: "pedido só pode ser enviado se usuário estiver verificado").
- Chamar serviços externos (email, pagamento) — geralmente via clientes injetados.
- Retornar estruturas de dados puras (dicts, DTOs), não respostas HTTP.

Não permitido:
- Ler diretamente `request` / `response`. (Isso é responsabilidade da camada de routes.)
- Renderizar JSON / HTML diretamente.
- SQL direto (usar models).

Um controller por cluster de caso de uso: `controllers/produto_controller.py`, `controllers/pedido_controller.py`.

---

### Camadas de apoio

#### `config/`
**Responsabilidade:** centralizar configuração dependente de ambiente.

- Ler todas as variáveis de ambiente aqui (`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET`, `CORS_ORIGINS`, etc.).
- Fornecer defaults tipados para desenvolvimento.
- Falhar rápido no boot se faltar valor obrigatório em produção.

Nenhuma chamada `os.environ.get(...)` fora deste módulo.

#### `middlewares/` (ou `errors/`)
**Responsabilidade:** concerns cross-cutting acionados pelo pipeline de middleware do framework.

- Handler central de erros (mapeia tipos de exceção para respostas HTTP).
- Log de request / injeção de correlation-id.
- Checagens de autenticação / autorização.
- Configuração de CORS.

#### `services/` (opcional)
**Responsabilidade:** integrações com sistemas externos não-DB (email, pagamento, produtores de fila).

Usar apenas se o projeto tem mais de ~2 integrações externas. Caso contrário, inline no controller.

#### `utils/` (opcional, com parcimônia)
Funções puras sem dependências. Formatação de data, geração de slug etc. Resistir à tentação de jogar tudo aqui.

#### Entry point (`app.py` / `src/app.js` / `main.py`)
**Composition root.** Importa o framework, instancia o app, conecta a config, registra middlewares, monta rotas, sobe o servidor. Deve ser pequeno (< ~60 linhas).

---

## Layout alvo do diretório

### Python / Flask
```
src/
├── config/
│   └── settings.py
├── models/
│   ├── __init__.py
│   ├── <entidade>_model.py
│   └── ...
├── routes/
│   ├── __init__.py
│   ├── <entidade>_routes.py
│   └── ...
├── controllers/
│   ├── __init__.py
│   ├── <entidade>_controller.py
│   └── ...
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py
└── app.py                # composition root
```

Em projetos Flask muito pequenos pode-se manter `src/` achatado e um `app.py` na raiz.

### Node.js / Express
```
src/
├── config/
│   └── index.js
├── models/
│   ├── User.js
│   └── ...
├── routes/
│   ├── index.js
│   ├── users.routes.js
│   └── ...
├── controllers/
│   ├── users.controller.js
│   └── ...
├── middlewares/
│   ├── errorHandler.js
│   └── auth.js
└── app.js                # composition root, exporta `app`
└── server.js             # importa app, chama listen()
```

Separar `app.js` (configuração do Express) de `server.js` (sobe o servidor) torna o app trivialmente testável com `supertest`.

---

## Convenções de nomenclatura

- Python: arquivos e identificadores em `snake_case`.
- JavaScript: identificadores em `camelCase`; arquivos de rota/controller costumam usar `camelCase` ou `kebab-case`. Seguir a convenção existente do projeto.
- Uma classe/entidade por arquivo.
- Sufixos revelam a camada: `_model.py`, `_controller.py`, `_routes.py` (ou `.controller.js`, `.routes.js`, `.model.js`).

---

## Critérios de validação (Fase 3 deve satisfazer)

Uma refatoração só está completa quando **todos** os pontos abaixo valem:

1. A pasta de cada camada existe e contém arquivos casando com sua responsabilidade.
2. Config está centralizada — sem segredos hardcoded, sem leitura de ambiente fora de `config/`.
3. Models não têm código HTTP; routes não têm lógica de negócio; controllers não fazem referência a `request`/`response`.
4. Tratamento de erro está centralizado em um único middleware/handler.
5. O entry point apenas faz fiação; não contém lógica de negócio.
6. A aplicação sobe sem erros.
7. Todo endpoint que existia antes continua respondendo com o mesmo método HTTP e path.

---

## Adaptando a profundidade da mudança

- **Entrada monolítica**: produzir a estrutura completa acima.
- **Entrada parcialmente organizada**: manter pastas válidas existentes, mover apenas código fora do lugar. Exemplos:
  - Se `routes/` existe e as funções estão enxutas, deixar; apenas mover lógica de negócio para controllers.
  - Se `models/` existe com classes ORM, deixar; não duplicar.
  - Se `services/` existe para integrações externas, manter.
- Nunca apagar testes nem configurações não relacionadas. Na dúvida, deixar como está.
