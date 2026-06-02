# ============================================================
# technical.py — Cálculo dos Indicadores Técnicos
#
# Indicadores técnicos são ferramentas matemáticas que usam
# o histórico de preços pra tentar prever o comportamento
# futuro de uma ação. Não são infalíveis, mas ajudam muito!
# ============================================================

import pandas as pd
import numpy as np
from src.utils.helpers import logger, interpretar_rsi, interpretar_macd


def calcular_rsi(closes: pd.Series, periodo: int = 14) -> pd.Series:
    """
    Calcula o RSI (Relative Strength Index — Índice de Força Relativa)

    O RSI mede a velocidade e a magnitude das mudanças de preço.
    Varia de 0 a 100:
    - Acima de 70: ação "sobrecomprada" (subiu demais, pode cair)
    - Abaixo de 30: ação "sobrevendida" (caiu demais, pode subir)
    - Entre 30-70: zona neutra

    Parâmetros:
        closes: série com os preços de fechamento
        periodo: janela de cálculo (padrão 14 dias)
    """
    # Calcula a variação diária do preço
    delta = closes.diff()

    # Separa os dias que subiram dos que caíram
    ganhos = delta.where(delta > 0, 0.0)   # dias positivos
    perdas = -delta.where(delta < 0, 0.0)  # dias negativos (valor positivo)

    # Calcula a média dos ganhos e das perdas (usando média exponencial)
    media_ganhos = ganhos.ewm(com=periodo - 1, min_periods=periodo).mean()
    media_perdas = perdas.ewm(com=periodo - 1, min_periods=periodo).mean()

    # RS = razão entre médias de ganhos e perdas
    rs = media_ganhos / media_perdas

    # Fórmula do RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calcular_macd(closes: pd.Series,
                  periodo_rapido: int = 12,
                  periodo_lento: int = 26,
                  periodo_sinal: int = 9) -> tuple:
    """
    Calcula o MACD (Moving Average Convergence Divergence)

    O MACD é feito da diferença entre duas médias móveis exponenciais.
    Quando a linha MACD cruza a linha de Signal de baixo pra cima = COMPRA
    Quando a linha MACD cruza a linha de Signal de cima pra baixo = VENDA

    Retorna uma tupla: (macd_line, signal_line, histograma)
    """
    # EMA rápida (12 dias) — responde mais rápido ao mercado
    ema_rapida = closes.ewm(span=periodo_rapido, adjust=False).mean()

    # EMA lenta (26 dias) — mais estável, responde mais devagar
    ema_lenta = closes.ewm(span=periodo_lento, adjust=False).mean()

    # Linha MACD = diferença entre as duas EMAs
    macd_line = ema_rapida - ema_lenta

    # Linha de Signal = EMA da linha MACD (suaviza o sinal)
    signal_line = macd_line.ewm(span=periodo_sinal, adjust=False).mean()

    # Histograma = diferença entre MACD e Signal (mostra força da tendência)
    histograma = macd_line - signal_line

    return macd_line, signal_line, histograma


def calcular_medias_moveis(closes: pd.Series) -> dict:
    """
    Calcula SMA e EMA de 20 e 50 períodos.

    SMA (Simple Moving Average) = média simples dos últimos N fechamentos
    EMA (Exponential Moving Average) = média que dá mais peso aos dias recentes

    Retorna um dicionário com todas as médias calculadas.
    """
    medias = {
        # Médias simples
        "SMA_20": closes.rolling(window=20).mean(),
        "SMA_50": closes.rolling(window=50).mean(),
        # Médias exponenciais (mais sensíveis a movimentos recentes)
        "EMA_20": closes.ewm(span=20, adjust=False).mean(),
        "EMA_50": closes.ewm(span=50, adjust=False).mean(),
    }
    return medias


def calcular_bollinger_bands(closes: pd.Series, periodo: int = 20, desvios: float = 2.0) -> dict:
    """
    Calcula as Bandas de Bollinger.

    As bandas são calculadas usando a SMA e o desvio padrão:
    - Banda Central = SMA de 20 períodos
    - Banda Superior = SMA + 2 desvios padrão
    - Banda Inferior = SMA - 2 desvios padrão

    Quando o preço toca a banda inferior = possível oportunidade de compra
    Quando o preço toca a banda superior = possível momento de venda
    """
    # Média central (SMA 20)
    banda_central = closes.rolling(window=periodo).mean()

    # Desvio padrão dos preços na janela
    desvio_padrao = closes.rolling(window=periodo).std()

    # Bandas superior e inferior
    banda_superior = banda_central + (desvios * desvio_padrao)
    banda_inferior = banda_central - (desvios * desvio_padrao)

    return {
        "BB_superior": banda_superior,
        "BB_central": banda_central,
        "BB_inferior": banda_inferior,
    }


def analisar_volume(volume: pd.Series, periodo: int = 20) -> dict:
    """
    Analisa o comportamento do volume de negociações.

    Volume alto confirma tendências (muito importante!).
    Se o preço sobe com volume alto = movimento mais confiável.
    Se o preço sobe com volume baixo = movimento suspeito.
    """
    # Volume médio dos últimos N dias
    volume_medio = volume.rolling(window=periodo).mean()

    # Volume do último dia
    volume_atual = volume.iloc[-1]
    media_atual = volume_medio.iloc[-1]

    # Razão entre volume atual e média
    razao_volume = volume_atual / media_atual if media_atual > 0 else 1.0

    return {
        "volume_serie": volume,
        "volume_medio": volume_medio,
        "volume_atual": volume_atual,
        "volume_medio_atual": media_atual,
        "razao_volume": razao_volume,
        "interpretacao": _interpretar_volume(razao_volume)
    }


def _interpretar_volume(razao: float) -> str:
    """Interpreta a razão entre volume atual e médio."""
    if razao >= 2.0:
        return "MUITO ALTO (forte interesse dos investidores)"
    elif razao >= 1.3:
        return "ALTO (acima da média, confirma movimento)"
    elif razao >= 0.7:
        return "NORMAL (volume dentro do esperado)"
    else:
        return "BAIXO (pouco interesse, movimento fraco)"


def calcular_todos_indicadores(df: pd.DataFrame) -> dict:
    """
    Função principal que calcula TODOS os indicadores de uma vez.

    Recebe um DataFrame com colunas: Open, High, Low, Close, Volume
    Retorna um dicionário com todos os indicadores calculados.
    """
    logger.info("Calculando indicadores técnicos...")

    # Valida se temos dados suficientes (pelo menos 50 dias pra SMA50)
    if len(df) < 50:
        logger.warning(f"Dados insuficientes: {len(df)} registros (mínimo 50)")

    closes = df["Close"]
    volume = df["Volume"]

    # --- RSI ---
    rsi_serie = calcular_rsi(closes)
    rsi_atual = rsi_serie.iloc[-1]

    # --- MACD ---
    macd_line, signal_line, histograma = calcular_macd(closes)
    macd_atual = macd_line.iloc[-1]
    signal_atual = signal_line.iloc[-1]
    hist_atual = histograma.iloc[-1]

    # --- Médias Móveis ---
    medias = calcular_medias_moveis(closes)
    preco_atual = closes.iloc[-1]

    # --- Bollinger Bands ---
    bollinger = calcular_bollinger_bands(closes)
    bb_superior = bollinger["BB_superior"].iloc[-1]
    bb_inferior = bollinger["BB_inferior"].iloc[-1]
    bb_central = bollinger["BB_central"].iloc[-1]

    # --- Volume ---
    vol_analise = analisar_volume(volume)

    # Monta o resultado com os valores numéricos e as interpretações
    resultado = {
        # Dados brutos (para os gráficos)
        "series": {
            "closes": closes,
            "rsi": rsi_serie,
            "macd": macd_line,
            "signal": signal_line,
            "histograma": histograma,
            "sma_20": medias["SMA_20"],
            "sma_50": medias["SMA_50"],
            "ema_20": medias["EMA_20"],
            "ema_50": medias["EMA_50"],
            "bb_superior": bollinger["BB_superior"],
            "bb_central": bollinger["BB_central"],
            "bb_inferior": bollinger["BB_inferior"],
            "volume": volume,
            "volume_medio": vol_analise["volume_medio"],
        },
        # Valores atuais (para a análise)
        "atual": {
            "preco": round(preco_atual, 2),
            "rsi": round(rsi_atual, 2),
            "macd": round(macd_atual, 4),
            "signal": round(signal_atual, 4),
            "histograma_macd": round(hist_atual, 4),
            "sma_20": round(medias["SMA_20"].iloc[-1], 2),
            "sma_50": round(medias["SMA_50"].iloc[-1], 2),
            "ema_20": round(medias["EMA_20"].iloc[-1], 2),
            "ema_50": round(medias["EMA_50"].iloc[-1], 2),
            "bb_superior": round(bb_superior, 2),
            "bb_central": round(bb_central, 2),
            "bb_inferior": round(bb_inferior, 2),
            "volume_atual": int(vol_analise["volume_atual"]),
            "volume_medio": int(vol_analise["volume_medio_atual"]),
            "razao_volume": round(vol_analise["razao_volume"], 2),
        },
        # Interpretações em texto (para o agente de decisão)
        "interpretacoes": {
            "rsi": interpretar_rsi(rsi_atual),
            "macd": interpretar_macd(macd_atual, signal_atual),
            "tendencia_medias": _interpretar_medias(
                preco_atual,
                medias["SMA_20"].iloc[-1],
                medias["SMA_50"].iloc[-1]
            ),
            "bollinger": _interpretar_bollinger(
                preco_atual, bb_superior, bb_inferior, bb_central
            ),
            "volume": vol_analise["interpretacao"],
        }
    }

    logger.info("Indicadores calculados com sucesso!")
    return resultado


def _interpretar_medias(preco: float, sma20: float, sma50: float) -> str:
    """Interpreta a posição do preço em relação às médias móveis."""
    if preco > sma20 > sma50:
        return "TENDÊNCIA DE ALTA (preço acima de SMA20 e SMA50)"
    elif preco < sma20 < sma50:
        return "TENDÊNCIA DE BAIXA (preço abaixo de SMA20 e SMA50)"
    elif sma20 > sma50:
        return "CRUZAMENTO ALTISTA (SMA20 cruzou acima da SMA50 - Golden Cross)"
    elif sma20 < sma50:
        return "CRUZAMENTO BAIXISTA (SMA20 cruzou abaixo da SMA50 - Death Cross)"
    else:
        return "SEM TENDÊNCIA DEFINIDA"


def _interpretar_bollinger(preco: float, superior: float,
                           inferior: float, central: float) -> str:
    """Interpreta a posição do preço nas Bandas de Bollinger."""
    if preco >= superior:
        return "PREÇO NA BANDA SUPERIOR (sobrecomprado, cuidado!)"
    elif preco <= inferior:
        return "PREÇO NA BANDA INFERIOR (sobrevendido, possível oportunidade)"
    elif preco > central:
        return "PREÇO ACIMA DA BANDA CENTRAL (levemente otimista)"
    else:
        return "PREÇO ABAIXO DA BANDA CENTRAL (levemente pessimista)"
