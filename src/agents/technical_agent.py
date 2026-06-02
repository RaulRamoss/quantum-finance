import yfinance as yf
from src.indicators.technical import calcular_todos_indicadores


class TechnicalAgent:
    def __init__(self, periodo="6mo"):
        self.periodo = periodo

    def executar(self, ticker):
        ticker_yf = ticker if ".SA" in ticker else ticker + ".SA"
        hist = yf.Ticker(ticker_yf).history(period=self.periodo)
        if hist.empty:
            return {"erro": f"sem dados para {ticker}"}
        indicadores = calcular_todos_indicadores(hist)
        tendencia = self._tendencia(indicadores)
        return {
            "ticker": ticker,
            "indicadores": indicadores,
            "tendencia_geral": tendencia,
        }

    def _tendencia(self, indicadores):
        interp = indicadores.get("interpretacoes", {})
        alta, baixa = 0, 0
        if "BULLISH" in interp.get("macd", ""):
            alta += 1
        elif "BEARISH" in interp.get("macd", ""):
            baixa += 1
        if "ALTA" in interp.get("tendencia_medias", ""):
            alta += 1
        elif "BAIXA" in interp.get("tendencia_medias", ""):
            baixa += 1
        rsi = indicadores["atual"].get("rsi", 50)
        if rsi < 40:
            alta += 0.5
        elif rsi > 60:
            baixa += 0.5
        if alta > baixa:
            return "ALTISTA"
        elif baixa > alta:
            return "BAIXISTA"
        return "LATERAL"
