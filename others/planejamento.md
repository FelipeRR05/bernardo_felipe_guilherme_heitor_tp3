# Planejamento da próxima etapa (TP3)

Este documento define três coisas para a próxima etapa do projeto: o modelo que vamos usar para
classificar a intenção das mensagens, como o texto vai ser transformado em números e qual é a
URL da nossa API que fica autorizada como alvo do teste adversarial no TP4/TP5.

O problema de classificação (a pergunta, X, y, as classes e a distribuição delas) está formalizado
na seção 3 do notebook `eda/eda_tp3.ipynb`.

---

## 1. Modelo candidato: Regressão Logística

**Escolhemos a Regressão Logística multinomial** (`LogisticRegression` do scikit-learn), que
trata as 5 intenções de uma vez só.

Por que ela é adequada para o problema:

- **É um modelo de classificação.** Ela devolve uma das 5 intenções e a
  probabilidade de cada uma. Com a probabilidade, a API pode devolver a confiança junto com a
  intenção e, se o modelo estiver em dúvida, mandar o chamado para um atendente humano. Era
  justamente o que faltava quando tentamos usar regressão linear (seção 3 do notebook).
- **Funciona bem com texto transformado em contagens.** O `CountVectorizer` gera uma matriz com
  milhares de colunas e quase toda vazia (os números estão na seção 2 deste documento). Modelos lineares como a
  Regressão Logística lidam bem com esse tipo de matriz, e a regularização (parâmetro `C`) evita
  que o modelo decore o treino. Na regressão do TP3 já vimos sobreajuste com só 75 colunas.
- **É fácil de interpretar.** Cada palavra recebe um peso para cada intenção, então dá para ver
  o que o modelo aprendeu. Isso importa neste dataset: 69,3% das mensagens começam com a mesma
  frase, e precisamos conferir se o modelo está aprendendo algo sobre a intenção ou se agarrou em
  algum detalhe da geração dos dados.
- **É leve.** Treina em segundos e responde em milissegundos. Como a API vai ser atacada, um
  modelo pesado deixaria cada chamada ao `POST /predict` cara e facilitaria derrubar o servidor.

Como as classes são balanceadas, o modelo vai ser comparado com o chute da classe mais frequente,
que acerta 20,7%. Ele só vale a pena se ficar acima disso.

---

## 2. Representação do texto: CountVectorizer

**A técnica definida é o `CountVectorizer`.** Ele monta um vocabulário com as palavras que
aparecem nas mensagens de treino e transforma cada mensagem num vetor com a contagem de cada
palavra do vocabulário. A ordem das palavras se perde, mas o que o cliente escreveu fica
representado em números que o modelo consegue usar.

Por que escolhemos o CountVectorizer:

- **É simples e transparente.** Cada coluna é uma palavra e cada valor é quantas vezes ela
  aparece. Junto com os pesos da Regressão Logística, dá para explicar cada previsão palavra por
  palavra.
- **Combina com o modelo escolhido.** A matriz esparsa que ele gera é o tipo de entrada com que a
  Regressão Logística trabalha bem.
- **É rápido e determinístico.** O mesmo texto sempre vira o mesmo vetor, e transformar uma
  mensagem nova na API é instantâneo.
- **Entra num `Pipeline` do scikit-learn**, como fizemos na regressão. Assim o vocabulário é
  aprendido só com os dados de treino e o pipeline inteiro (CountVectorizer + modelo) pode ser
  salvo e carregado pela API.

Como vamos configurar:

| Parâmetro | Valor | Motivo |
|---|---|---|
| Placeholder | removido antes | `{product_purchased}` aparece em 100% das mensagens e, sem as stopwords, vira a palavra mais frequente do vocabulário, sem dizer nada sobre a intenção |
| `lowercase` | `True` (padrão) | "Refund" e "refund" são a mesma palavra |
| `stop_words` | `"english"` | Tira palavras como "the", "to" e "my", que estão entre as mais frequentes e não ajudam a separar as intenções. As mensagens estão em inglês |
| `min_df` | `2` | Descarta palavras que aparecem numa mensagem só, que não ajudam o modelo a generalizar |

Com essa configuração, nos 6.775 chamados de treino o vocabulário fica com **2.499 palavras**, e
cada chamado usa em média 18 delas: só **0,73%** da matriz é diferente de zero. Na validação
cruzada também vamos testar incluir pares de palavras (`ngram_range=(1, 2)`), que capturam
expressões como "cancel subscription".

---

## 3. Alvo autorizado para o teste adversarial (TP4/TP5)

A nossa API vai ficar exposta na internet pelo **Cloudflare Tunnel**, e esta é a URL autorizada
para o pentest:

| Item | Valor |
|---|---|
| URL da API (Cloudflare Tunnel) | **[PREENCHER: https://....trycloudflare.com]** |
| Documentação interativa | `<URL da API>/docs` |
| Usuários de teste | `admin` / `admin123` e `analista` / `analista123` |
| Escopo autorizado | Somente a API nessa URL |

### Como a API é exposta

```bash
# Terminal 1 - dentro da pasta fastapi/
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn main:app --host 127.0.0.1 --port 8000 --no-server-header

# Terminal 2
cloudflared tunnel --url http://127.0.0.1:8000
```

O `cloudflared` mostra a URL pública (`https://<nome-aleatório>.trycloudflare.com`), que é a que
vai na tabela acima.

Cuidados:

- **A chave do JWT precisa ser trocada.** A chave padrão está no repositório, que é público, e
  com ela qualquer um conseguiria gerar tokens válidos.
- **A URL do túnel rápido muda toda vez que o `cloudflared` é reiniciado.** Se isso acontecer,
  atualizamos este documento e avisamos o colega.
- **O `TRUST_PROXY_HEADERS` fica desligado (padrão).** Atrás do túnel, todas as requisições
  chegam de 127.0.0.1, então o limite de 10 logins por minuto passa a valer para todos os
  clientes juntos. Ligar a opção faria a API confiar no `X-Forwarded-For`, que o atacante pode
  preencher com qualquer valor para escapar do limite.
