# Análise da tríade CIA por componente

Documento complementar ao DFD (dfd_api.png), que aprofunda a análise de segurança de cada componente com base na tríade Confidencialidade, Integridade e Disponibilidade (CID). Também registra as medidas já implementadas e as pendências identificadas, deixando claras as limitações de segurança do projeto.

- Confidencialidade: o que nesse componente não pode ser visto por quem não deveria?
- Integridade: o que não pode ser alterado sem autorização?
- Disponibilidade: o que precisa continuar funcionando, e o que o derrubaria?

Cada componente tem também o que já está implementado e o que continua em aberto, porque
achamos mais honesto registrar as lacunas do que dar a entender que está tudo resolvido.

---

## Visão geral

Cada componente da API possui um ponto de atenção principal em relação à segurança. No cliente/frontend, o cuidado maior é com a proteção do token de acesso. Nos middlewares e na rota GET /health, a prioridade é garantir que o sistema continue funcionando corretamente.
Na rota POST /auth/token, é essencial proteger as credenciais e os tokens. Já na rota POST /predict, o foco está em garantir que os dados enviados não sejam alterados indevidamente. Na rota GET /predictions/{id}, a principal preocupação é impedir que pessoas não autorizadas acessem previsões de outros usuários.
O arquivo database.db precisa ter seus dados protegidos contra acessos e alterações indevidas. Por fim, a variável JWT_SECRET_KEY exige atenção especial, pois sua exposição pode comprometer a segurança dos tokens e, consequentemente, de toda a API.

---

## C1 - Cliente / Frontend

_Entidade externa, fora da fronteira de confiança. Não controlamos este componente._

O cliente está fora da nossa fronteira de confiança, por isso não podemos confiar totalmente nos dados que ele envia. A principal preocupação é proteger o token JWT, as credenciais e os dados das predições.
Já implementado: token com expiração de 30 minutos e CORS com origens permitidas.
Em aberto: armazenamento seguro do token no frontend e configuração de HTTPS no ambiente local para proteger as credenciais durante a transmissão.

---

## C2 - Middlewares (CORS, cabeçalhos de segurança, rate limiting)

Os middlewares ajudam a proteger a API contra acessos indevidos e ataques. O CORS restringe as origens que podem acessar a API pelo navegador, os cabeçalhos de segurança reduzem riscos como clickjacking e interpretação incorreta de conteúdo, e o rate limiting limita tentativas excessivas de login, ajudando a evitar sobrecarga do servidor.
Já implementado: CORS com origens permitidas, cabeçalhos de segurança e limite de 10 tentativas por minuto no login, com resposta genérica de erro 429.
Em aberto: o contador do rate limiting fica em memória, o limite por IP não impede ataques distribuídos e ainda falta implementar CAPTCHA após falhas repetidas. |

---

## C3 - `GET /health`

Essa rota é pública e serve para verificar se a API está funcionando. Para evitar expor informações desnecessárias, ela retorna apenas o status e o nome do serviço. Como não altera dados, o risco à integridade é baixo, mas sua disponibilidade é importante para o monitoramento do sistema.
Já implementado: resposta simples, sem informações sobre versão ou ambiente, e proteção pelo rate limiting global.
Em aberto: verificar também se o banco de dados está acessível, pois atualmente a API pode responder que está funcionando mesmo com o banco indisponível.

---

## C4 - `POST /auth/token`

Essa rota é responsável por autenticar o usuário e gerar o token JWT. A principal preocupação é proteger as senhas e os tokens, evitar que pessoas descubram quais usuários estão cadastrados e impedir a falsificação de tokens. Também é importante prevenir ataques de força bruta e sobrecarga do servidor.
Já implementado: senhas protegidas com hash bcrypt, respostas iguais para usuário inexistente e senha incorreta, JWT assinado com HS256 e limite de 10 requisições por minuto.
Em aberto: configurar HTTPS no ambiente local, implementar bloqueio temporário de contas, registrar tentativas de login para auditoria e adicionar mecanismos de renovação e revogação de tokens.

---

## C5 - `POST /predict`

Essa rota recebe o texto do usuário, gera uma predição e armazena o resultado no banco de dados. É importante proteger possíveis dados pessoais e garantir que cada predição fique vinculada ao usuário correto.
Já implementado: validação dos dados com extra='forbid', limite de 5.000 caracteres, autenticação por JWT e definição do owner_id pelo token, impedindo que o usuário escolha o proprietário da predição pelo corpo da requisição.
Em aberto: limitar a quantidade de predições por usuário, avaliar uma alternativa ao SQLite para suportar mais escritas simultâneas e sanitizar o texto antes de exibi-lo futuramente.

---

## C6 - `GET /predictions/{id}`

Essa rota permite consultar uma predição específica e exige atenção especial à confidencialidade, pois cada usuário só pode acessar seus próprios dados. Sem essa verificação, alguém poderia consultar predições de outras pessoas alterando o ID na URL.
Já implementado: verificação de propriedade pelo owner_id, resposta 404 tanto para registros inexistentes quanto para registros de outros usuários, filtro por proprietário diretamente na consulta SQL e teste automatizado de acesso indevido.
Em aberto: registrar tentativas de acesso negado para identificar possíveis ataques e substituir os IDs sequenciais por UUIDs, dificultando a tentativa de descobrir outros registros.

---

## C7 - `database.db` (SQLite)

O banco de dados armazena informações importantes, como hashes de senhas e predições dos usuários. Por isso, é essencial proteger os dados contra acessos e alterações indevidas. Além disso, se o arquivo for corrompido ou perdido, toda a aplicação poderá ser afetada.
Já implementado: consultas parametrizadas com SQLModel para prevenir SQL injection, senhas armazenadas com hash bcrypt, proteção contra exposição de hashes nas respostas e chave estrangeira para relacionar as predições aos usuários.
Em aberto: criptografar o banco em repouso, implementar backups regulares, avaliar uma solução mais robusta para produção e adicionar auditoria das alterações realizadas nos dados.

---

## C8 - `JWT_SECRET_KEY`

Essa chave é essencial para a segurança da API, pois é usada para assinar os tokens JWT. Se alguém obtiver seu valor, poderá criar tokens falsos e se passar por outros usuários. Se a chave for perdida ou alterada, os tokens existentes deixarão de ser válidos.
Já implementado: chave configurada por variável de ambiente, algoritmo de assinatura fixado em HS256 e proteção contra exposição da chave nas respostas da API.
Em aberto: remover o valor padrão do config.py em produção, armazenar a chave em um cofre de segredos e implementar a rotação periódica para aumentar a segurança.

---

## Onde cada pilar está mais e menos protegido

Confidencialidade: é o pilar mais bem protegido, com senhas criptograficamente protegidas por hash, controle de acesso às predições, consultas seguras e mensagens de erro genéricas. A principal lacuna é a falta de HTTPS no ambiente local, que deixa os dados expostos durante a transmissão.
Integridade: está bem protegida por validações de entrada, identificação do proprietário pelo token e consultas parametrizadas. Porém, falta uma auditoria para registrar alterações e permitir investigar possíveis ações indevidas.
Disponibilidade: é o ponto mais fraco, pois, apesar do limite de tentativas de login, o sistema ainda depende do SQLite, não possui rotina de backup, não verifica a disponibilidade do banco no health check e não conta com monitoramento adequado. Essas seriam as principais prioridades antes de colocar a aplicação em produção.
