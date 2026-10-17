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

| Severidade    | Antes: alertas (ocorrências) | Depois: alertas (ocorrências) |
| ------------- | ---------------------------- | ----------------------------- |
| High          | 0                            | **0**                         |
| Medium        | 2 (4)                        | **0**                         |
| Low           | 1 (2)                        | 1 (1)                         |
| Informational | 6 (31)                       | 5 (29)                        |

O resumo do relatório HTML do ZAP conta os alertas, e cada alerta pode aparecer em várias URLs
(ocorrências).

**Depois das correções, o scan final não tem nenhum finding Medium ou High.**

Os 2 alertas Medium apareciam, cada um, em 2 páginas (`/docs` e `/redoc`). São os
mesmos que tínhamos aceitado no TP2 (`scan_passivo_zap.md`). Desta vez eles foram corrigidos.

---

## Findings de severidade MEDIUM

### M-01 - CSP: script-src unsafe-inline

O OWASP ZAP identificou um risco médio nas páginas /docs e /redoc, pois a política CSP permitia a execução de scripts inline, facilitando possíveis ataques XSS e o roubo de tokens JWT.
Correção realizada: substituímos a permissão 'unsafe-inline' por um hash SHA-256 do script legítimo do Swagger UI, restringimos o acesso ao CDN, desativamos o /redoc e ajustamos o middleware para aplicar políticas CSP mais rigorosas.
Evidências: o alerta não aparece no relatório final do ZAP, a rota /redoc retorna 404 e o teste automatizado test_docs_funciona_sem_unsafe_inline_na_csp verifica essas proteções a cada execução no GitHub Actions.

### M-02 - CSP: style-src unsafe-inline

O OWASP ZAP identificou um risco médio na política CSP das páginas /docs e /redoc, pois permitiam estilos CSS inline, que poderiam facilitar alterações visuais maliciosas na página.
Correção realizada: removemos 'unsafe-inline' da diretiva style-src na configuração do Swagger UI em fastapi/routes/docs.py e desativamos a rota /redoc.
Resultado: o alerta não aparece no scan final do OWASP ZAP, confirmando que a configuração foi corrigida.

### O /docs continua funcionando

Uma CSP mais restrita poderia quebrar a página, então também abrimos o `/docs` no navegador
(Chromium) depois da correção. A página carregou as 5 rotas, o botão **Authorize** fez o login com
`admin` / `admin123`, e uma chamada a `GET /predictions/` feita pelo próprio Swagger devolveu 200.
O navegador não registrou nenhuma violação de CSP nem erro no console.

---

## Findings que continuam (Low e Informational)

Os alertas restantes do OWASP ZAP são classificados como Low ou Informational e não representam vulnerabilidades de alta gravidade.
O alerta Low no /docs ocorre porque o Swagger UI utiliza arquivos externos do CDN jsDelivr. Os demais alertas são informativos: exposição do servidor Uvicorn no cabeçalho Server, uso de HSTS em HTTP local, identificação da rota de login e do token de sessão, além do uso de JavaScript na documentação.
Esses alertas foram registrados com suas justificativas e possíveis melhorias. Para reduzir ainda mais os riscos, seria possível hospedar os arquivos do Swagger localmente, ocultar o cabeçalho do servidor e utilizar HTTPS no ambiente de execução.

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
