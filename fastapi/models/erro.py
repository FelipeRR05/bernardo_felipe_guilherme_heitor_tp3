"""Modelos das respostas de erro, usados para documentar os erros no /docs."""

from pydantic import BaseModel, Field


class ErroResponse(BaseModel):
    """Erro com uma mensagem só (401, 404, 429 e 500)."""

    detail: str = Field(description="Mensagem do erro.")


class ErroDeCampo(BaseModel):
    """Um problema de validação em um campo da requisição."""

    campo: str = Field(description="Onde está o problema, por exemplo body.texto.")
    mensagem: str = Field(description="O que está errado com o valor enviado.")
    tipo: str = Field(description="Código do erro de validação do Pydantic.")


class ErroDeValidacaoResponse(BaseModel):
    """Erro 422: a requisição não passou na validação."""

    detail: list[ErroDeCampo]
