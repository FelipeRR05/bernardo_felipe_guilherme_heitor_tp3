"""Testes de segurança da API.

O que cada grupo de testes cobre:

  - Autenticação: login com credenciais válidas e inválidas, token falso
  - Rota protegida: acesso sem token ou com token inválido
  - Autorização/BOLA: usuário tentando acessar recurso de outro usuário
  - Validação de entrada: campo extra no body e texto fora dos limites
  - Rate limiting: bloqueio com 429 depois de 10 tentativas de login
  - Cabeçalhos, CORS e a CSP do /docs (finding do ZAP corrigido no TP3)

Para rodar, a partir da raiz do projeto:

    pytest tests/ -v
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from conftest import token_de
from models.prediction import Prediction



def test_login_com_credenciais_validas_devolve_token(client: TestClient):
    resposta = client.post(
        "/auth/token", data={"username": "admin", "password": "admin123"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"].count(".") == 2  # formato do JWT: header.payload.assinatura


def test_login_com_senha_errada_devolve_401(client: TestClient):
    resposta = client.post(
        "/auth/token", data={"username": "admin", "password": "senha-errada"}
    )

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Usuário ou senha inválidos"}
    assert resposta.headers["WWW-Authenticate"] == "Bearer"
    assert "access_token" not in resposta.text


def test_usuario_inexistente_recebe_a_mesma_resposta_da_senha_errada(client: TestClient):
    # Se as respostas fossem diferentes, daria para descobrir quais usuários existem.
    senha_errada = client.post(
        "/auth/token", data={"username": "admin", "password": "senha-errada"}
    )
    inexistente = client.post(
        "/auth/token", data={"username": "usuario-que-nao-existe", "password": "x"}
    )

    assert senha_errada.status_code == inexistente.status_code == 401
    assert senha_errada.json() == inexistente.json()


def test_acesso_sem_token_e_recusado(client: TestClient):
   

    for resposta in [
        client.get("/predictions/"),
        client.get("/predictions/1"),
        client.post("/predict", json={"texto": "teste"}),
    ]:
        assert resposta.status_code == 401
        assert resposta.json() == {"detail": "Token ausente, inválido ou expirado"}


def test_token_invalido_tambem_e_recusado(client: TestClient):
    

    resposta = client.get(
        "/predictions/", headers={"Authorization": "Bearer token-inventado"}
    )
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Token ausente, inválido ou expirado"}


def test_token_assinado_com_outra_chave_e_recusado(client: TestClient):
   

    import jwt

    token_falso = jwt.encode(
        {"sub": "1", "username": "admin", "exp": 9999999999},
        "chave-do-atacante-que-nao-e-a-chave-da-api",
        algorithm="HS256",
    )

    resposta = client.get(
        "/predictions/", headers={"Authorization": f"Bearer {token_falso}"}
    )
    assert resposta.status_code == 401



def test_usuario_acessa_a_propria_predicao(client: TestClient, sessao: Session):
  

    predicao_do_admin = sessao.exec(
        select(Prediction).where(Prediction.texto.contains("admin"))
    ).first()

    resposta = client.get(
        f"/predictions/{predicao_do_admin.id}", headers=token_de(client, "admin")
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == predicao_do_admin.id


def test_usuario_nao_acessa_predicao_de_outro(client: TestClient, sessao: Session):
   

    predicao_do_admin = sessao.exec(
        select(Prediction).where(Prediction.texto.contains("admin"))
    ).first()

    resposta = client.get(
        f"/predictions/{predicao_do_admin.id}", headers=token_de(client, "analista")
    )

    
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Predição não encontrada"}
   
    assert "admin" not in resposta.text


def test_predicao_inexistente_responde_igual_a_predicao_alheia(
    client: TestClient, sessao: Session
):
    

    predicao_do_admin = sessao.exec(
        select(Prediction).where(Prediction.texto.contains("admin"))
    ).first()
    cabecalho = token_de(client, "analista")

    alheia = client.get(f"/predictions/{predicao_do_admin.id}", headers=cabecalho)
    inexistente = client.get("/predictions/999999", headers=cabecalho)

    assert alheia.status_code == inexistente.status_code == 404
    assert alheia.json() == inexistente.json()


def test_listagem_mostra_so_as_proprias_predicoes(client: TestClient):
    

    resposta = client.get("/predictions/", headers=token_de(client, "analista"))

    assert resposta.status_code == 200
    textos = [p["texto"] for p in resposta.json()]
    assert any("analista" in t for t in textos)
    assert not any("admin" in t for t in textos)



def test_campo_extra_no_body_e_rejeitado_com_422(client: TestClient):
    

    resposta = client.post(
        "/predict",
        json={"texto": "Meu produto não liga.", "campo_extra": "qualquer coisa"},
        headers=token_de(client, "admin"),
    )

    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["campo"] == "body.campo_extra"
    assert erro["tipo"] == "extra_forbidden"


def test_tentativa_de_forjar_o_dono_e_rejeitada(client: TestClient):
   

    resposta = client.post(
        "/predict",
        json={"texto": "Predição com dono forjado.", "owner_id": 1},
        headers=token_de(client, "analista"),
    )

    assert resposta.status_code == 422


def test_texto_vazio_e_rejeitado_com_422(client: TestClient):
    resposta = client.post(
        "/predict", json={"texto": ""}, headers=token_de(client, "admin")
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["campo"] == "body.texto"


def test_texto_acima_de_5000_caracteres_e_rejeitado_com_422(client: TestClient):
    resposta = client.post(
        "/predict", json={"texto": "a" * 5001}, headers=token_de(client, "admin")
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["tipo"] == "string_too_long"


def test_requisicao_correta_continua_funcionando(client: TestClient, sessao: Session):
    

    from models.user import User

    analista = sessao.exec(select(User).where(User.username == "analista")).first()

    resposta = client.post(
        "/predict",
        json={"texto": "Predição legítima do analista."},
        headers=token_de(client, "analista"),
    )

    assert resposta.status_code == 200
    assert resposta.json()["owner_id"] == analista.id



def test_cabecalhos_de_seguranca_estao_presentes(client: TestClient):
   

    resposta = client.get("/health")
    assert resposta.status_code == 200
    cabecalhos = resposta.headers

    assert "max-age=" in cabecalhos["Strict-Transport-Security"]
    assert cabecalhos["X-Frame-Options"] == "DENY"
    assert cabecalhos["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'none'" in cabecalhos["Content-Security-Policy"]


def test_cabecalhos_aparecem_tambem_nos_erros(client: TestClient):
    
    resposta = client.get("/predictions/")
    assert resposta.status_code == 401
    cabecalhos = resposta.headers

    assert cabecalhos["X-Frame-Options"] == "DENY"
    assert cabecalhos["X-Content-Type-Options"] == "nosniff"


def test_origem_da_allowlist_e_aceita(client: TestClient):
    resposta = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert resposta.status_code == 200
    assert (
        resposta.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )


def test_origem_fora_da_allowlist_nao_recebe_permissao(client: TestClient):
    resposta = client.get("/health", headers={"Origin": "https://site-qualquer.com"})
    assert resposta.status_code == 200
    assert "access-control-allow-origin" not in resposta.headers



def test_login_bloqueia_com_429_depois_de_10_tentativas(
    client: TestClient, monkeypatch
):
    

    from security.rate_limit import limiter

    limiter.enabled = True
    limiter.reset()

    codigos = []
    for _ in range(12):
        resposta = client.post(
            "/auth/token", data={"username": "admin", "password": "senha-errada"}
        )
        codigos.append(resposta.status_code)
        if resposta.status_code == 429:
            bloqueada = resposta

    limiter.reset()
    limiter.enabled = False

    assert 429 in codigos, f"Rate limiting não bloqueou. Códigos: {codigos}"
    
    assert codigos[:10] == [401] * 10
    assert codigos[10] == 429

    assert bloqueada.json() == {
        "detail": "Muitas tentativas em pouco tempo. Espere um momento e tente novamente."
    }
    assert bloqueada.headers["Retry-After"] == "60"


def test_docs_funciona_sem_unsafe_inline_na_csp(client: TestClient):
    # Correção do TP3 para os findings Medium do ZAP (CSP com unsafe-inline).
    resposta = client.get("/docs")

    assert resposta.status_code == 200
    assert "swagger-ui" in resposta.text
    csp = resposta.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in csp
    assert "'sha256-" in csp
    assert client.get("/redoc").status_code == 404
