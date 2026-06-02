from datetime import datetime


def gerar_recomendacao(ticker, indicadores, sentimento):
    atual = indicadores.get("atual", {})
    interp = indicadores.get("interpretacoes", {})
    pontuacao = 0
    detalhes_votacao = []

    rsi = atual.get("rsi", 50)
    if rsi <= 35:
        pontuacao += 1
        detalhes_votacao.append(f"RSI ({rsi:.1f}): COMPRA - sobrevendido")
    elif rsi >= 65:
        pontuacao -= 1
        detalhes_votacao.append(f"RSI ({rsi:.1f}): VENDA - sobrecomprado")
    else:
        detalhes_votacao.append(f"RSI ({rsi:.1f}): NEUTRO")

    macd_texto = interp.get("macd", "")
    if "BULLISH" in macd_texto:
        pontuacao += 1
        detalhes_votacao.append("MACD: COMPRA")
    elif "BEARISH" in macd_texto:
        pontuacao -= 1
        detalhes_votacao.append("MACD: VENDA")
    else:
        detalhes_votacao.append("MACD: NEUTRO")

    medias_texto = interp.get("tendencia_medias", "")
    if "ALTA" in medias_texto:
        pontuacao += 1
        detalhes_votacao.append("Medias: COMPRA")
    elif "BAIXA" in medias_texto:
        pontuacao -= 1
        detalhes_votacao.append("Medias: VENDA")
    else:
        detalhes_votacao.append("Medias: NEUTRO")

    bb_texto = interp.get("bollinger", "")
    if "INFERIOR" in bb_texto:
        pontuacao += 1
        detalhes_votacao.append("Bollinger: COMPRA")
    elif "SUPERIOR" in bb_texto:
        pontuacao -= 1
        detalhes_votacao.append("Bollinger: VENDA")
    else:
        detalhes_votacao.append("Bollinger: NEUTRO")

    score_sentimento = sentimento.get("score_medio", 0.0)
    score_tecnico = pontuacao / 4
    score_final = (score_tecnico * 0.70) + (score_sentimento * 0.30)

    if score_final >= 0.15:
        recomendacao = "COMPRAR"
    elif score_final <= -0.15:
        recomendacao = "VENDER"
    else:
        recomendacao = "AGUARDAR"

    confianca = min(abs(score_final) / 0.5, 1.0)

    rsi_v = atual.get("rsi", 50)
    label_sent = sentimento.get("label_geral", "NEUTRO")
    total = sentimento.get("total_noticias", 0)
    justificativa = (
        f"Analise de {ticker}: RSI em {rsi_v:.1f} ({interp.get('rsi', '')}), "
        f"MACD {interp.get('macd', '').split('(')[0].strip()}, "
        f"{interp.get('tendencia_medias', '')}, "
        f"noticias {label_sent.lower()} ({total} analisadas). "
    )
    if recomendacao == "COMPRAR":
        justificativa += "Indicadores favoraveis para COMPRA."
    elif recomendacao == "VENDER":
        justificativa += "Indicadores sugerem pressao de VENDA."
    else:
        justificativa += "Sinais mistos, melhor AGUARDAR."

    return {
        "ticker": ticker,
        "recommendation": recomendacao,
        "confidence": round(confianca, 2),
        "reasoning": justificativa,
        "score_final": round(score_final, 3),
        "sentiment_score": round(score_sentimento, 3),
        "sentiment_label": label_sent,
        "indicators": {
            "RSI": atual.get("rsi"),
            "RSI_interpretacao": interp.get("rsi"),
            "MACD": interp.get("macd"),
            "Medias_Moveis": interp.get("tendencia_medias"),
            "Bollinger": interp.get("bollinger"),
            "Volume": interp.get("volume"),
            "Preco_Atual": atual.get("preco"),
            "SMA_20": atual.get("sma_20"),
            "SMA_50": atual.get("sma_50"),
        },
        "news_summary": {
            "total": sentimento.get("total_noticias", 0),
            "positivas": sentimento.get("noticias_positivas", 0),
            "negativas": sentimento.get("noticias_negativas", 0),
        },
        "detalhes_votacao": detalhes_votacao,
        "timestamp": datetime.now().isoformat(),
    }
