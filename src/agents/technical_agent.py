# ============================================================
# technical_agent.py — Agente de Análise Técnica
#
# Este agente é o "analista gráfico" do sistema.
# Ele pega os dados históricos de preços e calcula todos
# os indicadores técnicos, interpretando o que significam.
# ============================================================

import yfinance as yf
from src.indicators.technical import calcular_todos_indicadores
from src.utils.helpers import logger


class TechnicalAgent:
    """
    Agente especializado em análise técnica de ações.

    Responsabilidades:
    - Coletar dados históricos de preços (via yfinance)
    - Calcular todos os indicadores técnicos
    - Interpretar os sinais dos indicadores
    - Determinar a tendência geral do ativo
    """

    def __init__(self, nome: str = "TechnicalAgent", periodo: str = "6mo"):
        self.nome = nome
        self.periodo = periodo  # Período de dados a baixar
        logger.info(f"[{self.nome}] Inicializado (período: {periodo})")

    def executar(self, ticker: str) -> dict:
        """
        Executa a análise técnica completa de um ativo.

        Parâmetros:
            ticker: código da ação (ex: 'VALE3')

        Retorna:
            dict com dados, indicadores e interpretações
        """
        logger.info(f"[{self.nome}] Iniciando análise técnica para {ticker}")

        # ---- RACIOCÍNIO ----
        pensamento = self._raciocinar(ticker)
        logger.info(f"[{self.nome}] Raciocínio: {pensamento}")

        # ---- AÇÃO: Coletar dados ----
        dados = self._coletar_dados(ticker)

        if dados is None:
            logger.error(f"[{self.nome}] Falha ao coletar dados para {ticker}")
            return {"erro": f"Não foi possível coletar dados para {ticker}"}

        # ---- AÇÃO: Calcular indicadores ----
        logger.info(f"[{self.nome}] Calculando indicadores para {ticker}...")
        indicadores = calcular_todos_indicadores(dados)

        # ---- AÇÃO: Determinar tendência geral ----
        tendencia = self._determinar_tendencia(indicadores)

        # ---- OBSERVAÇÃO: Estrutura o resultado ----
        resultado = {
            "agente": self.nome,
            "ticker": ticker,
            "raciocinio": pensamento,
            "dados_disponiveis": len(dados),
            "indicadores": indicadores,
            "tendencia_geral": tendencia,
            "resumo": self._gerar_resumo(ticker, indicadores, tendencia),
        }

        logger.info(f"[{self.nome}] Análise concluída! Tendência: {tendencia}")
        return resultado

    def _raciocinar(self, ticker: str) -> str:
        """Simula o raciocínio antes de agir."""
        return (
            f"Para analisar tecnicamente {ticker}, preciso: "
            f"(1) baixar {self.periodo} de histórico de preços, "
            f"(2) calcular RSI, MACD, médias móveis e Bollinger Bands, "
            f"(3) interpretar os sinais e determinar a tendência."
        )

    def _coletar_dados(self, ticker: str):
        """
        Baixa os dados históricos do Yahoo Finance.
        Adiciona '.SA' se necessário (sufixo da B3).
        """
        try:
            ticker_yf = ticker if ".SA" in ticker else ticker + ".SA"
            ativo = yf.Ticker(ticker_yf)
            hist = ativo.history(period=self.periodo)

            if hist.empty:
                logger.warning(f"Nenhum dado retornado para {ticker_yf}")
                return None

            logger.info(f"  Dados coletados: {len(hist)} registros")
            return hist

        except Exception as e:
            logger.error(f"Erro ao coletar dados de {ticker}: {e}")
            return None

    def _determinar_tendencia(self, indicadores: dict) -> str:
        """
        Determina a tendência geral baseada nos indicadores.
        Conta quantos indicadores estão bullish vs bearish.
        """
        interp = indicadores.get("interpretacoes", {})
        pontos_alta = 0
        pontos_baixa = 0

        # Analisa cada indicador
        macd = interp.get("macd", "")
        if "BULLISH" in macd:
            pontos_alta += 1
        elif "BEARISH" in macd:
            pontos_baixa += 1

        medias = interp.get("tendencia_medias", "")
        if "ALTA" in medias or "Golden" in medias:
            pontos_alta += 1
        elif "BAIXA" in medias or "Death" in medias:
            pontos_baixa += 1

        rsi = indicadores.get("atual", {}).get("rsi", 50)
        if rsi < 40:
            pontos_alta += 0.5  # RSI baixo = favorável pra compra
        elif rsi > 60:
            pontos_baixa += 0.5

        bb = interp.get("bollinger", "")
        if "INFERIOR" in bb:
            pontos_alta += 1
        elif "SUPERIOR" in bb:
            pontos_baixa += 1

        # Decide a tendência
        if pontos_alta > pontos_baixa + 0.5:
            return "ALTISTA"
        elif pontos_baixa > pontos_alta + 0.5:
            return "BAIXISTA"
        else:
            return "LATERAL/NEUTRO"

    def _gerar_resumo(self, ticker: str, indicadores: dict, tendencia: str) -> str:
        """Gera resumo textual da análise técnica."""
        atual = indicadores.get("atual", {})
        rsi = atual.get("rsi", 0)
        preco = atual.get("preco", 0)

        return (
            f"Análise técnica de {ticker}: preço R$ {preco:.2f}, "
            f"RSI {rsi:.1f}, tendência {tendencia}. "
            f"MACD: {indicadores.get('interpretacoes', {}).get('macd', 'N/A')}."
        )
