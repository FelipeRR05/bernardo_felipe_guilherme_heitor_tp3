# Projeto de Bloco - Análise e Segurança de Agentes de IA

[![Testes de segurança](https://github.com/FelipeRR05/bernardo_felipe_guilherme_heitor_tp3/actions/workflows/testes.yml/badge.svg)](https://github.com/FelipeRR05/bernardo_felipe_guilherme_heitor_tp3/actions/workflows/testes.yml)

**Disciplina:** Projeto de Bloco: Análise e Segurança de Agentes de IA - Instituto Infnet
**Professor:** Tiago Cariolano de Souza Xavier
**Grupo:** Bernardo de Moraes Eleuterio, Felipe Roberto Rocha, Guilherme Valentim Ramalho da Silva e Heitor Cella Oliveira

---

## Objetivo do projeto

Construir um sistema de atendimento ao cliente apoiado por IA e, principalmente, **cuidar da
segurança da aplicação que serve esse sistema**. A ideia do bloco é que, mais para a frente, um
colega tente invadir esta API - então quanto mais sólida ela estiver agora, melhor.

Nos TP1 e TP2 fizemos o **EDA completo** do dataset de chamados de suporte e construímos a **API
FastAPI com os controles do OWASP Top 10 aplicados**, auditada com um scan passivo do OWASP ZAP.

Nesta etapa (TP3) fechamos o Trimestre 1 e planejamos o próximo:

1. Uma **regressão linear** sobre o dataset, com R², RMSE, Residual Plot e Q-Q Plot, e a
   **formalização do problema de classificação** (seções 2 e 3 do notebook).
2. A **suíte de testes de segurança** completa, rodando a cada push no **GitHub Actions**.
3. A **auditoria final com o OWASP ZAP**, com os findings Medium corrigidos e o `/docs`
   documentando todas as rotas.
4. O **planejamento** do modelo de classificação e do teste adversarial.

**O principal achado do EDA:** o dataset é sintético e suas colunas foram geradas de forma
independente umas das outras. A correlação mais forte entre variáveis distintas é |r| ≈ 0,04, e
69,3% dos chamados começam com exatamente o mesmo texto, rotulado com as cinco intenções. Isso
significa que o classificador previsto para a próxima etapa pode não funcionar acima do acaso com
esses dados. A discussão completa está na seção 1.8 do notebook.

---

## Estrutura de pastas

```
.
├── README.md
├── .github/
│   └── workflows/
│       └── testes.yml           # GitHub Actions: roda pytest tests/ -v a cada push
├── data/
│   └── customer_support_tickets.csv     # dataset usado no projeto
├── eda/
│   └── eda_tp3.ipynb            # EDA (1.1 a 1.8), regressão linear (2) e formalização (3)
├── fastapi/
│   ├── main.py                  # ponto de entrada, middlewares e tratadores de erro
│   ├── config.py                # configurações (JWT, CORS, CSP, rate limit)
│   ├── database.py              # engine e sessão do SQLModel
│   ├── sqlite_database.py       # cria o database.db e chama a população inicial
│   ├── sqlite_populate.py       # insere os usuários e as predições de exemplo
│   ├── database.db              # banco SQLite já populado
│   ├── requirements.txt
│   ├── models/                  # modelos Pydantic e tabelas SQLModel
│   │   ├── auth.py
│   │   ├── erro.py              # respostas de erro documentadas no /docs
│   │   ├── health.py
│   │   ├── prediction.py        # tabela prediction + entrada/saída da rota
│   │   └── user.py              # tabela user
│   ├── routes/                  # endpoints
│   │   ├── auth.py              # POST /auth/token (com rate limiting)
│   │   ├── docs.py              # GET /docs (Swagger UI com CSP sem unsafe-inline)
│   │   ├── health.py            # GET /health
│   │   ├── predict.py           # POST /predict
│   │   └── predictions.py       # GET /predictions e /predictions/{id} (ownership)
│   └── security/                # autenticação e controles de segurança
│       ├── jwt_handler.py       # geração e validação do JWT
│       ├── middleware.py        # cabeçalhos de segurança HTTP
│       ├── oauth2.py            # OAuth2PasswordBearer e dependência de autenticação
│       ├── password.py          # hash bcrypt
│       └── rate_limit.py        # configuração do SlowAPI
├── tests/
│   ├── conftest.py              # banco em memória e fixtures
│   └── test_security.py         # testes de segurança
├── zap/
│   ├── relatorio_zap_tp3.html   # relatório final do OWASP ZAP (TP3)
│   ├── relatorio_zap_tp3.json   # o mesmo relatório em JSON
│   ├── relatorio_zap_tp3_antes.html   # scan do TP3 antes das correções
│   ├── scan_passivo_zap_TP3.md  # análise dos findings Medium e High do TP3
│   ├── relatorio_zap.html       # relatório do TP2
│   ├── relatorio_zap.json
│   └── scan_passivo_zap.md      # análise do TP2
└── others/
    ├── planejamento.md          # modelo candidato, CountVectorizer e alvo do teste adversarial
    ├── dfd_api.png              # diagrama de fluxo de dados
    └── analise_cia.md           # tríade CIA aplicada a cada componente
```

---

## Instalação

Pré-requisito: Python 3.12 (`python --version`), a mesma versão usada no GitHub Actions.

```bash
# 1. Clonar o repositório
git clone https://github.com/FelipeRR05/bernardo_felipe_guilherme_heitor_tp3.git
cd bernardo_felipe_guilherme_heitor_tp3

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Instalar as dependências da API
cd fastapi
pip install -r requirements.txt

# 4. Se for abrir o notebook de EDA, instalar também as dependências da análise
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter
```

As dependências estão separadas de propósito: quem só quer rodar ou testar a API não precisa
instalar pandas, seaborn e companhia.

---

## Criação e população do banco de dados

O projeto já inclui o fastapi/database.db pronto para uso. Caso seja necessário recriá-lo, dentro da pasta fastapi/, execute:

```bash
python sqlite_database.py
```

O script apaga o banco anterior, recria as tabelas user e prediction e chama o sqlite_populate.py, que insere os dados iniciais: os usuários admin e analista e três predições de exemplo.

Para só popular de novo um banco que já existe (apaga os dados e insere tudo outra vez, sem recriar as tabelas):

```bash
python sqlite_populate.py
```

### Usuários criados

O sistema possui dois usuários de teste para demonstrar o controle de acesso:

admin → possui as predições 1 e 2.
analista → possui a predição 3.

A existência de dois usuários permite testar o ownership, verificando que um usuário não consegue acessar as predições do outro.

---

## Execução da API

De dentro da pasta `fastapi/`:

```bash
uvicorn main:app --reload
```

A API sobe em <http://127.0.0.1:8000> e a documentação interativa fica em
<http://127.0.0.1:8000/docs>.

### Variáveis de ambiente (todas opcionais)

O projeto utiliza variáveis de ambiente para configurar aspectos importantes da aplicação:

JWT_SECRET_KEY - chave usada para assinar os tokens.
ACCESS_TOKEN_EXPIRE_MINUTES - define a validade do token, padrão de 30 minutos.
DATABASE_URL - configura a conexão com o banco de dados.
CORS_ALLOWED_ORIGINS - define quais origens podem acessar a API.
RATE_LIMIT_LOGIN - controla o limite de tentativas de login, padrão de 10 por minuto.
TRUST_PROXY_HEADERS - permite confiar em cabeçalhos de proxy somente quando houver um proxy reverso confiável.

---

## Execução dos testes

Os testes podem ser executados a partir da raiz do projeto com:

```bash
pytest tests/ -v
```

O resultado esperado é de 21 testes aprovados. Eles usam o TestClient do FastAPI e um banco SQLite em memória, sem alterar o database.db do projeto. Todos conferem o status code e, quando faz sentido, o conteúdo da resposta.

O que os testes cobrem:

- Autenticação: login com credenciais válidas devolve o token, senha errada e usuário inexistente recebem o mesmo 401, e tokens falsos são recusados;
- Rota protegida: acesso sem token ou com token inválido recebe 401;
- Autorização/BOLA: um usuário não consegue ver a predição de outro e recebe o mesmo 404 de uma predição que não existe;
- Validação de entrada: campo extra no corpo, tentativa de forjar o dono e texto vazio ou acima de 5000 caracteres são rejeitados com 422;
- Rate limiting: depois de 10 tentativas de login, a 11ª recebe 429 com o cabeçalho Retry-After;
- Cabeçalhos de segurança, CORS e a CSP do /docs.

---

## Integração contínua (GitHub Actions)

O workflow está em .github/workflows/testes.yml e roda automaticamente a cada push. Ele:

1. obtém o código do repositório (actions/checkout);
2. configura o Python 3.12 (actions/setup-python);
3. instala as dependências do fastapi/requirements.txt;
4. executa pytest tests/ -v.

Se qualquer teste falhar, o pytest termina com erro e o workflow fica marcado como falha. O selo no topo deste README mostra o resultado da última execução, e o histórico fica na aba [Actions](https://github.com/FelipeRR05/bernardo_felipe_guilherme_heitor_tp3/actions) do repositório.

---

## Rotas da API

A API possui 5 rotas principais:

GET /health - verifica se a API está funcionando.
POST /auth/token - realiza o login e gera o JWT, com limite de 10 tentativas por minuto.
POST /predict - recebe um texto, identifica a intenção e salva a predição.
GET /predictions/ - lista apenas as predições do usuário autenticado.
GET /predictions/{id} - consulta uma predição, desde que pertença ao usuário autenticado.

### Respostas possíveis de cada rota

A API documenta os principais códigos de resposta e controles de segurança:

/health → 200 se estiver funcionando.
/auth/token → 200, 401, 422 ou 429, conforme o resultado do login.
/predict → 200 para sucesso, 401 para autenticação inválida e 422 para dados inválidos.
/predictions → 200, 401, 404 ou 422, conforme acesso e validação.

Todas essas respostas, os corpos esperados e quais rotas exigem token estão documentados em /docs.

O fluxo básico é: login → receber JWT → consultar/criar predições → testar bloqueios de acesso.

Usuários inexistentes e senhas erradas retornam o mesmo 401, enquanto recursos inexistentes e de outros usuários retornam 404, evitando vazamento de informações.

---

## Controles de segurança implementados

A API possui diversos controles de segurança, incluindo:

JWT + OAuth2 para autenticação.
bcrypt para proteger as senhas.
Validação Pydantic com extra='forbid'.
SQLModel para evitar consultas SQL inseguras.
Verificação de ownership para impedir acesso indevido a dados (BOLA).
Cabeçalhos de segurança como HSTS, CSP e X-Frame-Options.
CORS configurado com allowlist de origens permitidas.
Rate limiting no login para reduzir tentativas de força bruta.

Os controles estão organizados principalmente nas pastas security/, routes/, além de main.py, config.py e database.py.

### Cabeçalhos de segurança

A API adiciona automaticamente alguns cabeçalhos de segurança para evitar problemas como XSS, clickjacking, cache de dados sensíveis e downgrade para HTTP.

Entre eles estão Strict-Transport-Security, X-Frame-Options, Content-Security-Policy, Referrer-Policy e Cache-Control.

Eles podem ser verificados com:

curl -D - -o /dev/null http://127.0.0.1:8000/health

A página /docs tem a própria CSP, que libera só o script de inicialização do Swagger (pelo hash SHA-256) e os arquivos do Swagger UI no CDN, sem 'unsafe-inline'. O /redoc foi desligado no TP3.

Além disso, o Uvicorn adiciona o Server: uvicorn. A remoção pelo middleware não funciona, pois o cabeçalho é inserido pelo próprio servidor. Para um ambiente mais seguro, pode-se usar --no-server-header.

---

## Rate limiting: o limite escolhido e por quê

Foi adotado um limite de 10 requisições por minuto por IP no POST /auth/token para reduzir:

Força bruta e password spraying;
Sobrecarga de CPU causada pelo bcrypt;
Impactos na disponibilidade do serviço.

Com o limite, 10.000 tentativas passam de cerca de 17 minutos para aproximadamente 17 horas, tornando o ataque mais lento e detectável.

Decisões de implementação:

X-Forwarded-For só é confiável quando TRUST_PROXY_HEADERS=true.
A resposta 429 é genérica para não revelar informações úteis ao atacante.
Teste: após 10 tentativas, a 11ª retorna HTTP 429.

Limitações: o contador é mantido em memória, não funcionando de forma centralizada em múltiplas réplicas. Além disso, o limite por IP não impede ataques distribuídos; um controle por conta poderia complementar a proteção.

---

## Auditoria com OWASP ZAP

No TP3 fizemos a auditoria final com o OWASP ZAP 2.16.1, em scan passivo, usando 57 regras em sensibilidade máxima.

| Severidade    | Antes das correções: alertas (ocorrências) | Scan final: alertas (ocorrências) |
| ------------- | ------------------------------------------ | --------------------------------- |
| High          | 0                                          | 0                                 |
| Medium        | 2 (4)                                      | 0                                 |
| Low           | 1 (2)                                      | 1 (1)                             |
| Informational | 6 (31)                                     | 5 (29)                            |

Os dois findings Medium (CSP com 'unsafe-inline' em script-src e style-src, no /docs e no /redoc) foram corrigidos. A análise de cada um, com o risco, a correção e a evidência, está em zap/scan_passivo_zap_TP3.md, e o relatório final em zap/relatorio_zap_tp3.html.

### Alterações na API no TP3

- fastapi/routes/docs.py: o /docs passou a ser servido pela própria API, com uma CSP sem 'unsafe-inline';
- fastapi/main.py: /docs padrão e /redoc desligados, descrição da API e das tags para o /docs;
- fastapi/security/middleware.py: não aplica mais uma CSP permissiva às rotas de documentação;
- fastapi/routes/ e fastapi/models/erro.py: descrição de cada rota e o formato das respostas de erro documentados no /docs.

Os pontos que corrigem os findings do ZAP estão marcados no código com o comentário "Correção TP3".

---

## EDA, regressão linear e formalização do problema

O notebook eda/eda_tp3.ipynb já está executado e contém:

- as 8 etapas do EDA (TP1 e TP2): compreensão, inspeção, qualidade, limpeza, análise univariada e multivariada, outliers/anomalias e conclusões;
- seção 2 (TP3): regressão linear para prever o número de palavras da descrição, com R², RMSE, Residual Plot, Q-Q Plot, limitações e por que ela não representa o problema de classificação;
- seção 3 (TP3): formalização do problema de classificação, com X, y, as 5 classes, a distribuição delas e por que a regressão linear não serve para prever a intenção.

Pode ser executado novamente com Jupyter após instalar as dependências da análise.

---

## Planejamento da próxima etapa

O documento others/planejamento.md define o modelo candidato (Regressão Logística), a representação do texto com CountVectorizer e a URL da nossa API, exposta pelo Cloudflare Tunnel, que fica autorizada como alvo do teste adversarial no TP4/TP5.

---

## Modelagem de ameaças

O DFD está em others/dfd_api.png, identificando 3 fronteiras de confiança: internet, servidor da API e zona autenticada. A análise da tríade CIA (Confidencialidade, Integridade e Disponibilidade) dos 8 componentes está em others/analise_cia.md.
