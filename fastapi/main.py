"""Ponto de entrada da API.

Para rodar, de dentro da pasta fastapi/:

    uvicorn main:app --reload

A documentação interativa fica em http://127.0.0.1:8000/docs

Para recriar o banco:

    python sqlite_database.py
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import (
    CABECALHOS_PERMITIDOS,
    METODOS_PERMITIDOS,
    ORIGENS_PERMITIDAS,
)
from routes import auth, docs, health, predict, predictions
from security.middleware import CabecalhosDeSeguranca
from security.rate_limit import limiter, resposta_de_limite_excedido

DESCRICAO_DA_API = """
API do sistema de atendimento ao cliente do Projeto de Bloco: recebe a mensagem de um
chamado e devolve a intenção do cliente.

**Como usar pelo /docs**

1. Clique em **Authorize** e entre com usuário e senha.
   O Swagger chama o `POST /auth/token` e guarda o token JWT.
2. A partir daí, as rotas com cadeado mandam o cabeçalho `Authorization: Bearer <token>`.

**Autenticação:** `GET /health` e `POST /auth/token` são públicas. As demais exigem o token
JWT, que vale 30 minutos. Sem token, ou com token inválido ou expirado, a resposta é 401.

**Controles de segurança:** cada usuário só enxerga as próprias predições (proteção contra
BOLA), campos que não fazem parte do modelo são recusados com 422 e o login aceita no
máximo 10 tentativas por minuto por IP (depois disso, 429).
"""

TAGS_DA_DOCUMENTACAO = [
    {"name": "health", "description": "Verificação de que a API está no ar. Pública."},
    {"name": "auth", "description": "Login com usuário e senha, que devolve o token JWT."},
    {"name": "predict", "description": "Classificação da intenção de uma mensagem. Exige token."},
    {
        "name": "predictions",
        "description": "Consulta das predições do usuário autenticado. Exige token.",
    },
]

# Correção TP3 (ZAP - CSP unsafe-inline): o /docs padrão e o /redoc foram desligados.
# O /docs agora é servido por routes/docs.py, com uma CSP sem 'unsafe-inline'. O /redoc
# não é pedido no projeto e precisaria de estilos inline para funcionar.
app = FastAPI(
    title="Customer Support Intent API",
    description=DESCRICAO_DA_API,
    version="3.0.0",
    openapi_tags=TAGS_DA_DOCUMENTACAO,
    docs_url=None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, resposta_de_limite_excedido)
app.add_middleware(SlowAPIMiddleware)


app.add_middleware(CabecalhosDeSeguranca)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=METODOS_PERMITIDOS,
    allow_headers=CABECALHOS_PERMITIDOS,
)

@app.exception_handler(RequestValidationError)
async def erro_de_validacao(
    request: Request, exc: RequestValidationError
) -> JSONResponse:

    erros = [
        {
            "campo": ".".join(str(parte) for parte in erro.get("loc", [])),
            "mensagem": erro.get("msg", ""),
            "tipo": erro.get("type", ""),
        }
        for erro in exc.errors()
    ]

    return JSONResponse(status_code=422, content={"detail": erros})


@app.exception_handler(Exception)
async def erro_inesperado(request: Request, exc: Exception) -> JSONResponse:

    return JSONResponse(
        status_code=500, content={"detail": "Erro interno do servidor"}
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(predictions.router)
app.include_router(docs.router)
