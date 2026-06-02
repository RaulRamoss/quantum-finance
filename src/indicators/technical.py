import pandas as pd
import numpy as np


def calcular_rsi(closes, periodo=14):
    delta = closes.diff()
    ganhos = delta.where(delta > 0, 0.0)
    perdas = -delta.where(delta < 0, 0.0)
    media_ganhos = ganhos.ewm(com=periodo - 1, min_periods=periodo).mean()
    media_perdas = perdas.ewm(com=periodo - 1, min_periods=periodo).mean()
    rs = media_ganhos / media_perdas
    return 100 - (100 / (1 + rs))


def calcular_macd(closes, rapido=12, lento=26, sinal=9):
    ema_rapida = closes.ewm(span=rapido, adjust=False).mean()
    ema_lenta = closes.ewm(span=lento, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    signal = macd.ewm(span=sinal, adjust=False).mean()
    histograma = macd - signal
    return macd, signal, histograma


def calcular_medias_moveis(closes):
    return {
        "SMA_20": closes.rolling(window=20).mean(),
        "SMA_50": closes.rolling(window=50).mean(),
        "EMA_20": closes.ewm(span=20, adjust=False).mean(),
        "EMA_50": closes.ewm(span=50, adjust=False).mean(),
    }


def calcular_bollinger(closes, periodo=20, desvios=2.0):
    central = closes.rolling(window=periodo).mean()
    std = closes.rolling(window=periodo).std()
    return {
        "BB_superior": central + (desvios * std),
        "BB_central": central,
        "BB_inferior": central - (desvios * std),
    }


def analisar_volume(volume, periodo=20):
    volume_medio = volume.rolling(window=periodo).mean()
    atual = volume.iloc[-1]
    media = volume_medio.iloc[-1]
    razao = atual / media if media > 0 else 1.0
    if razao >= 1.3:
        interp = "ALTO (acima da media)"
    elif razao <= 0.7:
        interp = "BAIXO (pouco interesse)"
    else:
        interp = "NORMAL"
    return {"volume_medio": volume_medio, "volume_atual": atual,
            "volume_medio_atual": media, "razao_volume": razao, "interpretacao": interp}


def calcular_todos_indicadores(df):
    closes = df["Close"]
    volume = df["Volume"]

    rsi_serie = calcular_rsi(closes)
    macd_linha, signal_linha, hist = calcular_macd(closes)
    medias = calcular_medias_moveis(closes)
    bollinger = calcular_bollinger(closes)
    vol = analisar_volume(volume)

    rsi_atual = rsi_serie.iloc[-1]
    macd_atual = macd_linha.iloc[-1]
    signal_atual = signal_linha.iloc[-1]
    preco = closes.iloc[-1]
    sma20 = medias["SMA_20"].iloc[-1]
    sma50 = medias["SMA_50"].iloc[-1]
    bb_sup = bollinger["BB_superior"].iloc[-1]
    bb_inf = bollinger["BB_inferior"].iloc[-1]

    if rsi_atual >= 70:
        rsi_texto = "SOBRECOMPRADO (acima de 70)"
    elif rsi_atual <= 30:
        rsi_texto = "SOBREVENDIDO (abaixo de 30)"
    else:
        rsi_texto = "NEUTRO (entre 30 e 70)"

    if macd_atual > signal_atual:
        macd_texto = "BULLISH - MACD acima do Signal"
    else:
        macd_texto = "BEARISH - MACD abaixo do Signal"

    if preco > sma20 > sma50:
        medias_texto = "TENDENCIA DE ALTA"
    elif preco < sma20 < sma50:
        medias_texto = "TENDENCIA DE BAIXA"
    else:
        medias_texto = "SEM TENDENCIA CLARA"

    if preco >= bb_sup:
        bb_texto = "PRECO NA BANDA SUPERIOR"
    elif preco <= bb_inf:
        bb_texto = "PRECO NA BANDA INFERIOR (possivel oportunidade)"
    else:
        bb_texto = "PRECO DENTRO DAS BANDAS"

    return {
        "series": {
            "closes": closes, "rsi": rsi_serie,
            "macd": macd_linha, "signal": signal_linha, "histograma": hist,
            "sma_20": medias["SMA_20"], "sma_50": medias["SMA_50"],
            "ema_20": medias["EMA_20"], "ema_50": medias["EMA_50"],
            "bb_superior": bollinger["BB_superior"],
            "bb_central": bollinger["BB_central"],
            "bb_inferior": bollinger["BB_inferior"],
            "volume": volume, "volume_medio": vol["volume_medio"],
        },
        "atual": {
            "preco": round(preco, 2), "rsi": round(rsi_atual, 2),
            "macd": round(macd_atual, 4), "signal": round(signal_atual, 4),
            "sma_20": round(sma20, 2), "sma_50": round(sma50, 2),
            "ema_20": round(medias["EMA_20"].iloc[-1], 2),
            "ema_50": round(medias["EMA_50"].iloc[-1], 2),
            "bb_superior": round(bb_sup, 2),
            "bb_central": round(bollinger["BB_central"].iloc[-1], 2),
            "bb_inferior": round(bb_inf, 2),
            "volume_atual": int(vol["volume_atual"]),
            "volume_medio": int(vol["volume_medio_atual"]),
            "razao_volume": round(vol["razao_volume"], 2),
        },
        "interpretacoes": {
            "rsi": rsi_texto, "macd": macd_texto,
            "tendencia_medias": medias_texto, "bollinger": bb_texto,
            "volume": vol["interpretacao"],
        },
    }
