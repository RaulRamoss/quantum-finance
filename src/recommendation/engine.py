# ============================================================
# engine.py — Motor de Recomendação
#
# Aqui é onde acontece a mágica! A gente pega todos os
# indicadores técnicos + sentimento das notícias e decide
# se deve COMPRAR, VENDER ou AGUARDAR.
#
# A lógica é simples mas eficaz:
# - Cada indicador dá uma "votação" (+1 compra, -1 vende, 0 neutro)
# - O sentimento das notícias também vota
# - Somamos os votos e decidimos
# ============================================================

from src.utils.helpers import logger, score_para_confianca
from datetime import datetime


def calcular_pontuacao_tecnica(indicadores: dict) -> tuple:
    """
    Calcula a pontuação técnica baseada nos indicadores.

    Cada indicador contribui com um voto:
    +1 = sinal de COMPRA
     0 = NEUTRO
    -1 = sinal de VENDA

    Retorna: (pontuacao_total, max_pontos_possiveis, detalhes)
    """
    pontuacao = 0
    detalhes = []

    atual = indicadores.get("atual", {})
    interp = indicadores.get("interpretacoes", {})

    # ---- 1. RSI ----
    rsi = atual.get("rsi", 50)
    if rsi <= 35:
        # RSI muito baixo = sobrevendido = sinal de COMPRA
        pontuacao += 1
        detalhes.append(f"RSI ({rsi:.1f}): COMPRA — ação sobrevendida")
    elif rsi >= 65:
        # RSI muito alto = sobrecomprado = sinal de VENDA
        pontuacao -= 1
        detalhes.append(f"RSI ({rsi:.1f}): VENDA — ação sobrecomprada")
    else:
        detalhes.append(f"RSI ({rsi:.1f}): NEUTRO — zona intermediária")

    # ---- 2. MACD ----
    macd_interp = interp.get("macd", "")
    if "BULLISH" in macd_interp:
        pontuacao += 1
        detalhes.append(f"MACD: COMPRA — {macd_interp}")
    elif "BEARISH" in macd_interp:
        pontuacao -= 1
        detalhes.append(f"MACD: VENDA — {macd_interp}")
    else:
        detalhes.append(f"MACD: NEUTRO")

    # ---- 3. Médias Móveis ----
    medias_interp = interp.get("tendencia_medias", "")
    if "ALTA" in medias_interp or "Golden Cross" in medias_interp:
        pontuacao += 1
        detalhes.append(f"Médias: COMPRA — {medias_interp}")
    elif "BAIXA" in medias_interp or "Death Cross" in medias_interp:
        pontuacao -= 1
        detalhes.append(f"Médias: VENDA — {medias_interp}")
    else:
        detalhes.append(f"Médias: NEUTRO — {medias_interp}")

    # ---- 4. Bandas de Bollinger ----
    bb_interp = interp.get("bollinger", "")
    if "INFERIOR" in bb_interp:
        pontuacao += 1
        detalhes.append(f"Bollinger: COMPRA — preço próximo da banda inferior")
    elif "SUPERIOR" in bb_interp:
        pontuacao -= 1
        detalhes.append(f"Bollinger: VENDA — preço próximo da banda superior")
    else:
        detalhes.append(f"Bollinger: NEUTRO — {bb_interp}")

    # ---- 5. Volume ----
    razao_vol = atual.get("razao_volume", 1.0)
    macd_val = atual.get("macd", 0)
    # Volume alto confirmando uma tendência = reforça o sinal
    if razao_vol >= 1.3 and macd_val > 0:
        pontuacao += 0.5  # Meio voto positivo
        detalhes.append(f"Volume: CONFIRMA ALTA — {razao_vol:.1f}x acima da média")
    elif razao_vol >= 1.3 and macd_val < 0:
        pontuacao -= 0.5  # Meio voto negativo
        detalhes.append(f"Volume: CONFIRMA BAIXA — {razao_vol:.1f}x acima da média")
    else:
        detalhes.append(f"Volume: NEUTRO — {interp.get('volume', 'normal')}")

    return pontuacao, 4.5, detalhes  # máximo possível é 4.5 (4 votos + 0.5 do volume)


def gerar_recomendacao(ticker: str, indicadores: dict, sentimento: dict) -> dict:
    """
    Função principal que gera a recomendação de investimento.

    Combina a análise técnica com o sentimento das notícias
    e retorna uma recomendação no formato JSON.

    Parâmetros:
        ticker: código da ação (ex: "VALE3")
        indicadores: resultado do calcular_todos_indicadores()
        sentimento: resultado do analisar_conjunto_noticias()

    Retorna:
        dict com recomendação, confiança e justificativa
    """
    logger.info(f"Gerando recomendação para {ticker}...")

    # ---- ANÁLISE TÉCNICA ----
    pontuacao_tecnica, max_pontos, detalhes_tecnicos = calcular_pontuacao_tecnica(indicadores)

    # Normaliza a pontuação técnica para -1 a +1
    score_tecnico = pontuacao_tecnica / max_pontos

    # ---- ANÁLISE DE SENTIMENTO ----
    score_sentimento = sentimento.get("score_medio", 0.0)
    label_sentimento = sentimento.get("label_geral", "NEUTRO")

    # ---- SCORE FINAL (ponderado) ----
    # Técnica tem peso 70%, sentimento tem peso 30%
    # Você pode ajustar esses pesos conforme preferir!
    PESO_TECNICO = 0.70
    PESO_SENTIMENTO = 0.30

    score_final = (score_tecnico * PESO_TECNICO) + (score_sentimento * PESO_SENTIMENTO)

    # ---- DECISÃO ----
    # Thresholds (limiares) para tomar a decisão
    THRESHOLD_COMPRA = 0.15   # Score acima disso = COMPRAR
    THRESHOLD_VENDA = -0.15   # Score abaixo disso = VENDER

    if score_final >= THRESHOLD_COMPRA:
        recomendacao = "COMPRAR"
    elif score_final <= THRESHOLD_VENDA:
        recomendacao = "VENDER"
    else:
        recomendacao = "AGUARDAR"

    # ---- NÍVEL DE CONFIANÇA ----
    # Confiança = intensidade do score (quão longe do zero estamos)
    confianca = min(abs(score_final) / 0.5, 1.0)  # Normaliza pra 0-1
    confianca = round(confianca, 2)

    # ---- JUSTIFICATIVA EM LINGUAGEM NATURAL ----
    justificativa = _gerar_justificativa(
        ticker, recomendacao, indicadores, sentimento, detalhes_tecnicos
    )

    # ---- RELATÓRIO DETALHADO ----
    atual = indicadores.get("atual", {})

    resultado = {
        "ticker": ticker,
        "recommendation": recomendacao,
        "confidence": confianca,
        "confidence_label": score_para_confianca(confianca),
        "reasoning": justificativa,
        "score_tecnico": round(score_tecnico, 3),
        "score_sentimento": round(score_sentimento, 3),
        "score_final": round(score_final, 3),
        "sentiment_label": label_sentimento,
        "sentiment_score": round(score_sentimento, 3),
        "indicators": {
            "RSI": atual.get("rsi"),
            "RSI_interpretacao": indicadores.get("interpretacoes", {}).get("rsi"),
            "MACD": indicadores.get("interpretacoes", {}).get("macd"),
            "Medias_Moveis": indicadores.get("interpretacoes", {}).get("tendencia_medias"),
            "Bollinger": indicadores.get("interpretacoes", {}).get("bollinger"),
            "Volume": indicadores.get("interpretacoes", {}).get("volume"),
            "Preco_Atual": atual.get("preco"),
            "SMA_20": atual.get("sma_20"),
            "SMA_50": atual.get("sma_50"),
        },
        "news_summary": {
            "total": sentimento.get("total_noticias", 0),
            "positivas": sentimento.get("noticias_positivas", 0),
            "negativas": sentimento.get("noticias_negativas", 0),
            "neutras": sentimento.get("noticias_neutras", 0),
        },
        "detalhes_votacao": detalhes_tecnicos,
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(f"Recomendação para {ticker}: {recomendacao} (confiança: {confianca})")
    return resultado


def _gerar_justificativa(ticker: str, recomendacao: str,
                          indicadores: dict, sentimento: dict,
                          detalhes_tecnicos: list) -> str:
    """
    Gera uma justificativa em linguagem natural para a recomendação.
    É isso que torna o agente "explicável"!
    """
    atual = indicadores.get("atual", {})
    interp = indicadores.get("interpretacoes", {})

    rsi = atual.get("rsi", 50)
    preco = atual.get("preco", 0)
    label_sentimento = sentimento.get("label_geral", "NEUTRO")
    total_noticias = sentimento.get("total_noticias", 0)
    noticias_pos = sentimento.get("noticias_positivas", 0)

    # Monta a justificativa baseada nos indicadores mais relevantes
    partes = []

    # RSI
    partes.append(f"RSI em {rsi:.1f} ({interp.get('rsi', 'neutro')})")

    # MACD
    partes.append(f"MACD {interp.get('macd', 'neutro').split('(')[0].strip()}")

    # Médias
    tendencia = interp.get("tendencia_medias", "sem tendência definida")
    partes.append(tendencia)

    # Bollinger
    bb = interp.get("bollinger", "preço na zona intermediária")
    partes.append(bb)

    # Notícias
    if total_noticias > 0:
        pct_positivas = (noticias_pos / total_noticias) * 100
        partes.append(
            f"notícias {label_sentimento.lower()} "
            f"({noticias_pos}/{total_noticias} positivas, {pct_positivas:.0f}%)"
        )

    # Junta tudo na justificativa
    justificativa = f"Análise de {ticker}: {'; '.join(partes)}. "

    # Conclusão baseada na recomendação
    if recomendacao == "COMPRAR":
        justificativa += (
            f"O conjunto dos indicadores aponta para um cenário favorável de COMPRA, "
            f"com confirmação pelo sentimento {label_sentimento.lower()} das notícias recentes."
        )
    elif recomendacao == "VENDER":
        justificativa += (
            f"Os indicadores sugerem pressão vendedora. "
            f"Recomenda-se considerar VENDA ou redução de posição."
        )
    else:
        justificativa += (
            f"Os sinais estão mistos ou inconclusivos. "
            f"Recomenda-se AGUARDAR uma definição mais clara da tendência antes de agir."
        )

    return justificativa
