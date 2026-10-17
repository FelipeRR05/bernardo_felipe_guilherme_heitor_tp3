# Análise dos findings - scan passivo OWASP ZAP (TP3)

- Ferramenta: OWASP ZAP 2.16.1 em modo daemon.
- Scan: passivo, com as 57 regras ativas e sensibilidade máxima (threshold Low).
- Alvo: API local em 127.0.0.1:8000, subida com `uvicorn main:app`.
- Requisições: 17, cobrindo rotas públicas, login certo e errado, rotas sem token, acesso à
  predição de outro usuário, campo extra no corpo, ID inválido e rota inexistente.

Relatórios:

- `relatorio_zap_tp3.html` e `relatorio_zap_tp3.json` - scan final, depois das correções
- `relatorio_zap_tp3_antes.html` - scan feito no início do TP3, antes das correções

---

## Resultado

Rodamos o scan duas vezes: uma com a API do jeito que ela terminou o TP2, e outra depois das
correções.

| Severidade | Antes: alertas (ocorrências) | Depois: alertas (ocorrências) |
|---|---|---|
| High | 0 | **0** |
| Medium | 2 (4) | **0** |
| Low | 1 (2) | 1 (1) |
| Informational | 6 (31) | 5 (29) |

O resumo do relatório HTML do ZAP conta os alertas, e cada alerta pode aparecer em várias URLs
(ocorrências).

**Depois das correções, o scan final não tem nenhum finding Medium ou High.**

Os 2 alertas Medium apareciam, cada um, em 2 páginas (`/docs` e `/redoc`). São os
mesmos que tínhamos aceitado no TP2 (`scan_passivo_zap.md`). Desta vez eles foram corrigidos.

---

## Findings de severidade MEDIUM

### M-01 - CSP: script-src unsafe-inline

- **Finding:** CSP: script-src unsafe-inline (regra 10055 do ZAP, CWE-693).
- **Severidade:** Medium, com confiança High.
- **Onde:** `/docs` e `/redoc`.

O ZAP encontrou esta política nas duas páginas:

```
script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'
```

**Por que é um risco.** A CSP existe para que o navegador só execute scripts que a aplicação
autorizou. Com `'unsafe-inline'`, qualquer `<script>` escrito dentro do HTML é executado. Se um
atacante conseguir injetar um script na página (XSS), a CSP não bloqueia nada. A página do
`/docs` é justamente onde o usuário digita a senha e onde o token JWT fica guardado, então um XSS
ali poderia roubar o token e usar a API no lugar do usuário.

**O que foi alterado.** O `'unsafe-inline'` só estava lá porque o Swagger UI tem um script inline
que inicializa a página. Em vez de liberar todos os scripts inline, liberamos só esse:

1. Desligamos o `/docs` padrão do FastAPI (`docs_url=None` no `main.py`) e passamos a servir a
   página em `fastapi/routes/docs.py`, com o mesmo HTML.
2. Nesse arquivo calculamos o hash SHA-256 do script de inicialização e colocamos esse hash na CSP
   (`'sha256-...'`). O navegador só executa um script inline se o conteúdo dele bater com o hash.
   Um script injetado tem outro conteúdo, outro hash, e é bloqueado.
3. O endereço do CDN ficou restrito à pasta do Swagger UI
   (`https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/`), e não ao CDN inteiro.
4. Desligamos o `/redoc` (`redoc_url=None`). Ele não é usado no projeto e precisaria de estilos
   inline para funcionar.
5. O middleware (`fastapi/security/middleware.py`) deixou de aplicar uma CSP permissiva para as
   rotas de documentação. A rota `/docs` manda a própria CSP e todas as outras respostas recebem a
   CSP estrita da API.

Os pontos da correção estão marcados no código com o comentário `Correção TP3 (ZAP ...)`, em
`fastapi/routes/docs.py`, `fastapi/main.py` e `fastapi/security/middleware.py`.

**Evidência de que o problema não permanece.**

- O finding não aparece no scan final (`relatorio_zap_tp3.html`).
- O cabeçalho do `/docs` depois da correção:

```
$ curl -s -D - -o /dev/null http://127.0.0.1:8000/docs | grep -i content-security
content-security-policy: default-src 'none'; script-src https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/ 'sha256-P28/j37f0MgfkZ2lTEH5bnnfZ8YlHZ4cHtK+EWL/Qhw='; style-src https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/; img-src 'self' https://fastapi.tiangolo.com data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'

$ curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/redoc
404
```

- O teste `test_docs_funciona_sem_unsafe_inline_na_csp` (em `tests/test_security.py`) confere
  que a CSP do `/docs` não tem `unsafe-inline` e que o `/redoc` responde 404. Como ele roda no
  GitHub Actions a cada push, se alguém voltar a configuração antiga o workflow falha.

### M-02 - CSP: style-src unsafe-inline

- **Finding:** CSP: style-src unsafe-inline (regra 10055 do ZAP, CWE-693).
- **Severidade:** Medium, com confiança High.
- **Onde:** `/docs` e `/redoc`.

Política encontrada pelo ZAP:

```
style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'
```

**Por que é um risco.** É um risco menor que o do M-01. Com CSS inline liberado, quem
consegue injetar HTML na página pode mudar a aparência dela, por exemplo escondendo elementos ou
sobrepondo um formulário falso de login, e existem técnicas que usam CSS para vazar informações da
página.

**O que foi alterado.** A página do Swagger UI não tem nenhum estilo inline no HTML, só o arquivo
CSS que vem do CDN. Então bastou tirar o `'unsafe-inline'` do `style-src` na CSP nova, em
`fastapi/routes/docs.py`. O `/redoc`, que precisava de estilos inline, foi desligado (passo 4 do
M-01).

**Evidência de que o problema não permanece.** O finding não aparece no scan final, e o cabeçalho
mostrado no M-01 tem `style-src https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/`, sem
`unsafe-inline`.

### O /docs continua funcionando

Uma CSP mais restrita poderia quebrar a página, então também abrimos o `/docs` no navegador
(Chromium) depois da correção. A página carregou as 5 rotas, o botão **Authorize** fez o login com
`admin` / `admin123`, e uma chamada a `GET /predictions/` feita pelo próprio Swagger devolveu 200.
O navegador não registrou nenhuma violação de CSP nem erro no console.

---

## Findings que continuam (Low e Informational)

Não são Medium nem High, mas registramos por que continuam:

| Finding | Severidade | Onde | Por que continua |
|---|---|---|---|
| Cross-Domain JavaScript Source File Inclusion | Low | `/docs` | O Swagger UI vem do CDN jsDelivr. Diminuímos o risco restringindo a CSP à pasta do Swagger UI. Para zerar, seria preciso servir os arquivos pela própria API |
| Server Leaks its Webserver Application via "Server" | Informational | 12 respostas | O cabeçalho `Server: uvicorn` é colocado pelo próprio Uvicorn, depois do middleware. Some subindo a API com `uvicorn main:app --no-server-header` |
| Strict-Transport-Security Header on Plain HTTP Response | Informational | 12 respostas | O scan foi feito em HTTP local. Com HTTPS, que é o caso do Cloudflare Tunnel, o cabeçalho passa a valer |
| Session Management Response Identified | Informational | `/auth/token` | O ZAP só identificou que o login devolve um token |
| Authentication Request Identified | Informational | `/auth/token` | O ZAP só identificou a rota de login |
| Modern Web Application | Informational | `/docs` | O ZAP só identificou que a página usa JavaScript |

---

## O que este scan não cobre

O scan passivo só observa as requisições, sem atacar. Ele não testa SQL Injection, XSS de verdade
ou força bruta, e não sabe quem é dono de cada predição, então não consegue avaliar BOLA. Esses
controles são verificados pelos testes automatizados em `tests/test_security.py`.

---

## Como reproduzir

```bash
# 1. Subir o ZAP em modo daemon
./zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=SUACHAVE

# 2. Subir a API (em outro terminal, dentro de fastapi/)
uvicorn main:app

# 3. Configurar o navegador ou o cliente HTTP para usar 127.0.0.1:8090 como proxy
#    e percorrer as rotas da API

# 4. Exportar o relatório
curl "http://127.0.0.1:8090/JSON/reports/action/generate/?apikey=SUACHAVE\
&title=Scan&template=traditional-html&reportDir=<pasta>&reportFileName=relatorio_zap_tp3.html"
```
