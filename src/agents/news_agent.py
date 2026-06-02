# ============================================================
# news_agent.py — Agente Especializado em Notícias
#
# Este agente é responsável por coletar e analisar notícias
# financeiras. Ele faz parte da arquitetura Multi-Agent:
# cada agente tem uma responsabilidade específica.
#
# No padrão ReAct, o agente:
# 1. PENSA (Reasoning): analisa o que precisa fazer
# 2. AGE (Acting): usa as ferramentas disponíveis
# 3. OBSERVA: processa o resultado
# ============================================================

from src.sentiment.analyzer import buscar_noticias, analisar_conjunto_noticias
from src.utils.helpers import logger


class NewsAgent:
    """
    Agente especializado em análise de notícias e sentimento.

    Responsabilidades:
    - Coletar notícias dos feeds RSS
    - Analisar sentimento de cada notícia
    - Calcular score de impacto do conjunto
    - Identificar as notícias mais relevantes
    """

    def __init__(self, nome: str = "NewsAgent"):
        self.nome = nome
        logger.info(f"[{self.nome}] Inicializado!")

    def executar(self, ticker: str) -> dict:
        """
        Executa o fluxo completo de análise de notícias para um ticker.

        Parâmetros:
            ticker: código da ação (ex: 'VALE3')

        Retorna:
            dict com análise completa das notícias
        """
        logger.info(f"[{self.nome}] Iniciando análise de notícias para {ticker}")

        # ---- RACIOCÍNIO (Reasoning) ----
        # Antes de agir, o agente "pensa" sobre o que precisa fazer
        pensamento = self._raciocinar(ticker)
        logger.info(f"[{self.nome}] Raciocínio: {pensamento}")

        # ---- AÇÃO (Acting) ----
        # Agora executa as ações necessárias

        # Passo 1: Buscar notícias
        logger.info(f"[{self.nome}] Buscando notícias para {ticker}...")
        noticias = buscar_noticias(ticker, max_noticias=10)

        # Passo 2: Analisar sentimento de todas as notícias
        logger.info(f"[{self.nome}] Analisando sentimento de {len(noticias)} notícias...")
        analise = analisar_conjunto_noticias(noticias)

        # Passo 3: Identificar as notícias mais impactantes
        noticias_destaque = self._identificar_destaques(analise.get("detalhes", []))

        # ---- OBSERVAÇÃO (Observe) ----
        # Processa e estrutura o resultado
        resultado = {
            "agente": self.nome,
            "ticker": ticker,
            "raciocinio": pensamento,
            "analise_sentimento": analise,
            "noticias_destaque": noticias_destaque,
            "resumo": self._gerar_resumo(ticker, analise, noticias_destaque),
        }

        logger.info(f"[{self.nome}] Análise concluída! Sentimento: {analise['label_geral']}")
        return resultado

    def _raciocinar(self, ticker: str) -> str:
        """
        Simula o raciocínio do agente antes de agir.
        No LangGraph real, isso seria feito pelo LLM.
        """
        return (
            f"Para analisar {ticker}, preciso: "
            f"(1) buscar notícias recentes sobre o ativo, "
            f"(2) analisar o sentimento de cada notícia, "
            f"(3) calcular o impacto geral no mercado."
        )

    def _identificar_destaques(self, detalhes: list) -> list:
        """
        Identifica as notícias mais impactantes (maior score absoluto).
        """
        # Ordena por intensidade do score (mais longe do zero = mais impactante)
        ordenadas = sorted(detalhes, key=lambda x: abs(x.get("score", 0)), reverse=True)
        return ordenadas[:3]  # retorna as top 3

    def _gerar_resumo(self, ticker: str, analise: dict, destaques: list) -> str:
        """
        Gera um resumo textual da análise de notícias.
        """
        total = analise.get("total_noticias", 0)
        label = analise.get("label_geral", "NEUTRO")
        score = analise.get("score_medio", 0)

        resumo = (
            f"Análise de {total} notícias sobre {ticker}: "
            f"sentimento geral {label} (score: {score:+.3f}). "
        )

        if destaques:
            titulo_destaque = destaques[0].get("titulo", "")
            resumo += f"Notícia mais impactante: '{titulo_destaque[:60]}...'"

        return resumo
