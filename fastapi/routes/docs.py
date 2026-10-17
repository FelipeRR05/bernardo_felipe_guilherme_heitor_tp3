"""Página /docs (Swagger UI) servida pela própria API, com uma CSP sem 'unsafe-inline'.

Correção do TP3 para os dois findings Medium do OWASP ZAP:
  - CSP: script-src unsafe-inline
  - CSP: style-src unsafe-inline

O /docs padrão do FastAPI tem um script inline que inicializa o Swagger, e por isso a
CSP dele precisava de 'unsafe-inline'. Aqui geramos o mesmo HTML, calculamos o hash
SHA-256 desse script e liberamos só ele na CSP. Qualquer outro script inline que
alguém consiga injetar na página tem outro hash e é bloqueado pelo navegador.
"""

import base64
import hashlib
import re

from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)

# Só os arquivos do Swagger UI no CDN, e não o CDN inteiro.
SWAGGER_NO_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"

HTML_DA_DOCUMENTACAO = get_swagger_ui_html(
    openapi_url="/openapi.json",
    title="Customer Support Intent API - Documentação",
    oauth2_redirect_url=None,
).body.decode("utf-8")

SCRIPT_INLINE = re.search(
    r"<script>(.*?)</script>", HTML_DA_DOCUMENTACAO, flags=re.DOTALL
).group(1)
HASH_DO_SCRIPT = base64.b64encode(
    hashlib.sha256(SCRIPT_INLINE.encode("utf-8")).digest()
).decode("ascii")

# Correção TP3 (ZAP): sem 'unsafe-inline' em script-src e style-src. O único script
# inline liberado é o de inicialização do Swagger, identificado pelo hash.
CSP_DA_DOCUMENTACAO = (
    "default-src 'none'; "
    f"script-src {SWAGGER_NO_CDN} 'sha256-{HASH_DO_SCRIPT}'; "
    f"style-src {SWAGGER_NO_CDN}; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


@router.get("/docs")
def documentacao() -> HTMLResponse:
    """Swagger UI com a CSP própria da documentação."""

    return HTMLResponse(
        HTML_DA_DOCUMENTACAO,
        headers={"Content-Security-Policy": CSP_DA_DOCUMENTACAO},
    )
