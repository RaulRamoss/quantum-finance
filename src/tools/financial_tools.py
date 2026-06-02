# ============================================================
# financial_tools.py — Ferramentas do Agente LangChain
#
# No LangChain, "tools" são funções que o agente pode chamar
# pra executar ações no mundo real (buscar dados, calcular, etc.)
#
# O agente decide SOZINHO quando usar cada ferramenta,
# com base na descrição que a gente escreve pra cada uma.
# ============================================================

import yfinance as yf
import pandas as pd
from langchain.tools import tool
from src.sentiment.analyzer import buscar_noticias, analisar_conjunto_noticias
from src.indicators.technical import calcular_todos_indicadores
from src.recommendation.engine import gerar_recomendacao
from src.utils.helpers import logger


# ============================================================
# O decorador @tool do LangChain transforma uma função Python
# numa ferramenta que o agente pode usar autonomamente.
# A docstring IMPORTANTÍSSIMA — é ela que ensina o agente
# quando e como usar a ferramenta!
# ============================================================

@tool
def search_news(ticker: str) -> str:
    """
    Busca e analisa notícias financeiras recentes relacionadas a um ticker da B3.

    Use esta ferramenta quando precisar entender o contexto noticioso de uma ação.
    Por exemplo: 'Quais notícias existem sobre VALE3?' ou 'Como está o sentimento para PETR4?'

    Parâmetros:
        ticker: código da ação na B3 (ex: 'VALE3', 'PETR4', 'BBAS3', 'ITUB4')

    Retorna: resumo das notícias com análise de sentimento
    """
    logger.info(f"[Tool] search_news chamada para {ticker}")

    try:
        # Busca as notícias nos feeds RSS
        noticias = buscar_noticias(ticker, max_noticias=10)

        # Analisa o sentimento do conjunto de notícias
        analise = analisar_conjunto_noticias(noticias)

        # Formata o resultado como texto (o agente processa texto)
        resultado = f"""
=== ANÁLISE DE NOTÍCIAS: {ticker} ===
Total de notícias analisadas: {analise['total_noticias']}
• Notícias positivas: {analise['noticias_positivas']}
• Notícias negativas: {analise['noticias_negativas']}
• Notícias neutras: {analise['noticias_neutras']}

Score de sentimento: {analise['score_medio']:.3f} (de -1 a +1)
Classificação geral: {analise['label_geral']}

Principais notícias:
"""
        for i, detalhe in enumerate(analise.get("detalhes", [])[:5], 1):
            resultado += f"{i}. [{detalhe['sentimento']}] {detalhe['titulo']}\n"

        return resultado

    except Exception as e:
        logger.error(f"Erro em search_news: {e}")
        return f"Erro ao buscar notícias para {ticker}: {str(e)}"


@tool
def get_price_data(ticker: str, period: str = "3mo") -> str:
    """
    Obtém dados históricos de preços e volume de uma ação da B3 via Yahoo Finance.

    Use esta ferramenta quando precisar de dados de mercado como preço atual,
    variação, volume e histórico de preços.

    Parâmetros:
        ticker: código da ação (ex: 'VALE3.SA', 'PETR4.SA')
                IMPORTANTE: para ações brasileiras, adicione '.SA' ao final!
        period: período de histórico ('1mo', '3mo', '6mo', '1y', '2y')

    Retorna: resumo dos dados de mercado
    """
    logger.info(f"[Tool] get_price_data chamada para {ticker} ({period})")

    try:
        # Adiciona .SA se não tiver (sufixo da B3 no Yahoo Finance)
        ticker_yf = ticker if ".SA" in ticker else ticker + ".SA"

        # Baixa os dados do Yahoo Finance
        ativo = yf.Ticker(ticker_yf)
        hist = ativo.history(period=period)

        if hist.empty:
            return f"Não foi possível obter dados para {ticker}. Verifique o ticker."

        # Pega informações básicas
        preco_atual = hist["Close"].iloc[-1]
        preco_anterior = hist["Close"].iloc[-2]
        variacao = ((preco_atual - preco_anterior) / preco_anterior) * 100
        volume_atual = hist["Volume"].iloc[-1]
        preco_max = hist["High"].max()
        preco_min = hist["Low"].min()

        resultado = f"""
=== DADOS DE MERCADO: {ticker} ===
Preço atual: R$ {preco_atual:.2f}
Variação (dia): {variacao:+.2f}%
Volume: {volume_atual:,.0f} ações
Máximo ({period}): R$ {preco_max:.2f}
Mínimo ({period}): R$ {preco_min:.2f}
Registros disponíveis: {len(hist)} dias de histórico
Período: {hist.index[0].strftime('%d/%m/%Y')} a {hist.index[-1].strftime('%d/%m/%Y')}
"""
        return resultado

    except Exception as e:
        logger.error(f"Erro em get_price_data: {e}")
        return f"Erro ao buscar dados de {ticker}: {str(e)}"


@tool
def calculate_indicators(ticker: str, period: str = "6mo") -> str:
    """
    Calcula todos os indicadores técnicos de análise gráfica para uma ação.

    Inclui: RSI, MACD, Médias Móveis (SMA20, SMA50, EMA20, EMA50),
    Bandas de Bollinger e análise de volume.

    Use quando precisar de análise técnica detalhada de um ativo.

    Parâmetros:
        ticker: código da ação (ex: 'VALE3', 'PETR4')
        period: período de dados para cálculo ('3mo', '6mo', '1y')
    """
    logger.info(f"[Tool] calculate_indicators chamada para {ticker}")

    try:
        # Baixa os dados
        ticker_yf = ticker if ".SA" in ticker else ticker + ".SA"
        ativo = yf.Ticker(ticker_yf)
        hist = ativo.history(period=period)

        if hist.empty:
            return f"Dados insuficientes para calcular indicadores de {ticker}"

        # Calcula todos os indicadores
        indicadores = calcular_todos_indicadores(hist)
        atual = indicadores["atual"]
        interp = indicadores["interpretacoes"]

        resultado = f"""
=== INDICADORES TÉCNICOS: {ticker} ===
Preço atual: R$ {atual['preco']:.2f}

📊 RSI (14): {atual['rsi']:.2f}
   → {interp['rsi']}

📈 MACD:
   Linha MACD: {atual['macd']:.4f}
   Linha Signal: {atual['signal']:.4f}
   → {interp['macd']}

📉 Médias Móveis:
   SMA 20: R$ {atual['sma_20']:.2f}
   SMA 50: R$ {atual['sma_50']:.2f}
   EMA 20: R$ {atual['ema_20']:.2f}
   EMA 50: R$ {atual['ema_50']:.2f}
   → {interp['tendencia_medias']}

🎯 Bandas de Bollinger:
   Superior: R$ {atual['bb_superior']:.2f}
   Central:  R$ {atual['bb_central']:.2f}
   Inferior: R$ {atual['bb_inferior']:.2f}
   → {interp['bollinger']}

📦 Volume:
   Atual: {atual['volume_atual']:,}
   Médio 20d: {atual['volume_medio']:,}
   Razão: {atual['razao_volume']:.2f}x
   → {interp['volume']}
"""
        return resultado

    except Exception as e:
        logger.error(f"Erro em calculate_indicators: {e}")
        return f"Erro ao calcular indicadores para {ticker}: {str(e)}"


@tool
def analyze_sentiment(text: str) -> str:
    """
    Analisa o sentimento de um texto financeiro.

    Retorna um score de -1 (muito negativo) a +1 (muito positivo)
    e a classificação: POSITIVO, NEGATIVO ou NEUTRO.

    Use quando precisar avaliar o tom de uma notícia específica
    ou de um conjunto de informações textuais.

    Parâmetros:
        text: texto a ser analisado
    """
    from src.sentiment.analyzer import analisar_sentimento
    logger.info("[Tool] analyze_sentiment chamada")

    sentimento = analisar_sentimento(text)

    resultado = f"""
=== ANÁLISE DE SENTIMENTO ===
Score: {sentimento['score']:.3f} (de -1 a +1)
Classificação: {sentimento['label']}
• Positivo: {sentimento['positivo']:.1%}
• Negativo: {sentimento['negativo']:.1%}
• Neutro: {sentimento['neutro']:.1%}
"""
    return resultado


@tool
def generate_recommendation(ticker: str) -> str:
    """
    Gera uma recomendação completa de investimento para um ativo.

    Esta é a ferramenta principal! Ela combina análise técnica
    e análise de sentimento de notícias para gerar uma recomendação
    de COMPRAR, VENDER ou AGUARDAR com justificativa detalhada.

    Use quando o usuário pedir uma recomendação ou análise completa.

    Parâmetros:
        ticker: código da ação na B3 (ex: 'VALE3', 'PETR4', 'BBAS3', 'ITUB4')
    """
    logger.info(f"[Tool] generate_recommendation chamada para {ticker}")

    try:
        # Passo 1: Baixa os dados de mercado
        ticker_yf = ticker if ".SA" in ticker else ticker + ".SA"
        ativo = yf.Ticker(ticker_yf)
        hist = ativo.history(period="6mo")

        if hist.empty:
            return f"Não foi possível obter dados para {ticker}"

        # Passo 2: Calcula os indicadores técnicos
        indicadores = calcular_todos_indicadores(hist)

        # Passo 3: Busca e analisa as notícias
        noticias = buscar_noticias(ticker, max_noticias=10)
        sentimento = analisar_conjunto_noticias(noticias)

        # Passo 4: Gera a recomendação final
        recomendacao = gerar_recomendacao(ticker, indicadores, sentimento)

        # Formata o resultado de forma legível
        emoji = {"COMPRAR": "🟢", "VENDER": "🔴", "AGUARDAR": "🟡"}.get(
            recomendacao["recommendation"], "⚪"
        )

        resultado = f"""
╔══════════════════════════════════════════╗
║  RECOMENDAÇÃO QUANTUM FINANCE            ║
╚══════════════════════════════════════════╝

Ativo: {recomendacao['ticker']}
{emoji} RECOMENDAÇÃO: {recomendacao['recommendation']}
Confiança: {recomendacao['confidence']:.0%} ({recomendacao['confidence_label']})

📋 JUSTIFICATIVA:
{recomendacao['reasoning']}

📊 INDICADORES TÉCNICOS:
• RSI: {recomendacao['indicators']['RSI']:.1f} → {recomendacao['indicators']['RSI_interpretacao']}
• MACD: {recomendacao['indicators']['MACD']}
• Médias: {recomendacao['indicators']['Medias_Moveis']}
• Bollinger: {recomendacao['indicators']['Bollinger']}
• Volume: {recomendacao['indicators']['Volume']}
• Preço Atual: R$ {recomendacao['indicators']['Preco_Atual']:.2f}

📰 SENTIMENTO DAS NOTÍCIAS:
• Score: {recomendacao['sentiment_score']:.3f}
• Classificação: {recomendacao['sentiment_label']}
• Notícias analisadas: {recomendacao['news_summary']['total']}
  ({recomendacao['news_summary']['positivas']} positivas,
   {recomendacao['news_summary']['negativas']} negativas)

Gerado em: {recomendacao['timestamp']}
"""
        return resultado

    except Exception as e:
        logger.error(f"Erro em generate_recommendation: {e}")
        return f"Erro ao gerar recomendação para {ticker}: {str(e)}"


# Lista de todas as ferramentas disponíveis
# Usada na construção do agente
TODAS_FERRAMENTAS = [
    search_news,
    get_price_data,
    calculate_indicators,
    analyze_sentiment,
    generate_recommendation,
]
