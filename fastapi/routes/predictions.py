"""Rotas de consulta das predições - é aqui que mora a proteção contra BOLA."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session, select

from database import pegar_sessao
from models.erro import ErroDeValidacaoResponse, ErroResponse
from models.prediction import Prediction, PredictionResponse
from models.user import User
from security.oauth2 import usuario_autenticado

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get(
    "/",
    response_model=list[PredictionResponse],
    summary="Lista as predições do usuário autenticado",
    description=(
        "Exige token JWT. Devolve só as predições do usuário do token. As predições "
        "de outros usuários nunca aparecem na lista."
    ),
    responses={
        200: {"description": "Lista apenas as predições do próprio usuário."},
        401: {"model": ErroResponse, "description": "Token ausente, inválido ou expirado."},
    },
)
def listar(
    usuario: User = Depends(usuario_autenticado),
    sessao: Session = Depends(pegar_sessao),
) -> list[Prediction]:
    """Devolve só as predições de quem está chamando."""

    return list(
        sessao.exec(select(Prediction).where(Prediction.owner_id == usuario.id)).all()
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Busca uma predição por ID, conferindo se ela é do usuário",
    description=(
        "Exige token JWT. Recebe o ID da predição na URL (`prediction_id`, número "
        "inteiro) e só devolve a predição se ela pertencer ao usuário do token."
    ),
    responses={
        200: {"description": "A predição existe e pertence ao usuário autenticado."},
        401: {"model": ErroResponse, "description": "Token ausente, inválido ou expirado."},
        404: {
            "model": ErroResponse,
            "description": (
                "A predição não existe OU pertence a outro usuário. As duas "
                "situações devolvem exatamente a mesma resposta, de propósito."
            ),
        },
        422: {
            "model": ErroDeValidacaoResponse,
            "description": "O ID informado na URL não é um número inteiro.",
        },
    },
)
def buscar_por_id(
    prediction_id: int = Path(description="ID da predição que se quer consultar."),
    usuario: User = Depends(usuario_autenticado),
    sessao: Session = Depends(pegar_sessao),
) -> Prediction:
    """Busca uma predição pelo ID, mas só devolve se ela for do usuário."""

    predicao = sessao.exec(
        select(Prediction).where(Prediction.id == prediction_id)
    ).first()

    if predicao is None or predicao.owner_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predição não encontrada",
        )

    return predicao
