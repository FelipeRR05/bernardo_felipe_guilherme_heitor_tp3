"""Middleware que adiciona os cabeçalhos de segurança em todas as respostas. """

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import CSP_DA_API


class CabecalhosDeSeguranca(BaseHTTPMiddleware):
    """Acrescenta os cabeçalhos de segurança HTTP em toda resposta da API."""

    async def dispatch(self, request: Request, call_next) -> Response:
        resposta: Response = await call_next(request)

        # Correção TP3 (ZAP - CSP: script-src/style-src unsafe-inline): o middleware
        # não libera mais uma CSP permissiva para /docs e /redoc. A rota /docs
        # (routes/docs.py) já manda a própria CSP, sem 'unsafe-inline', e todas as
        # outras respostas recebem a CSP estrita da API.
        if "content-security-policy" not in resposta.headers:
            resposta.headers["Content-Security-Policy"] = CSP_DA_API

       
        resposta.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

       
        resposta.headers["X-Frame-Options"] = "DENY"

        resposta.headers["X-Content-Type-Options"] = "nosniff"

        
        resposta.headers["Referrer-Policy"] = "no-referrer"

        
        resposta.headers["Cache-Control"] = "no-store"

       
        if "server" in resposta.headers:
            del resposta.headers["server"]

        return resposta
