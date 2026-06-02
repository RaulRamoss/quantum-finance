# ============================================================
# decision_agent.py — Agente de Decisão Final
#
# Este é o "cérebro" da operação. Ele recebe os resultados
# do NewsAgent e do TechnicalAgent e toma a decisão final.
#
# Também gera:
# - Relatório explicável em linguagem natural
# - Score de confiança na recomendação
# - Registro do raciocínio utilizado
# ============================================================

import os
import json
from datetime import datetime
from src.agents.news_agent import NewsAgent
from src.agents.technical_agent import TechnicalAgent
from src.recommendation.engine import gerar_recomendacao
from src.utils.helpers import logger, salvar_json, timestamp_agora

# Tickers que o sistema monitora
TICKERS_MONITORADOS = ["VALE3", "PETR4", "BBAS3", "ITUB4"]


class DecisionAgent:
    """
    Agente de decisão — orquestra os outros agentes e toma a decisão final.

    No padrão Multi-Agent:
    - Recebe análises do NewsAgent e TechnicalAgent
    - Combina as informações
    - Gera recomendação com justificativa
    - Salva relatório para histórico
    """

    def __init__(self, nome: str = "DecisionAgent"):
        self.nome = nome
        # Instancia os agentes especializados
        self.news_agent = NewsAgent()
        self.technical_agent = TechnicalAgent()
        # Histórico de recomendações desta sessão
        self.historico = []
        logger.info(f"[{self.nome}] Sistema Multi-Agent inicializado!")

    def analisar_ativo(self, ticker: str) -> dict:
        """
        Análise completa de um único ativo.
        Orquestra NewsAgent → TechnicalAgent → Decisão

        Parâmetros:
            ticker: código da ação (ex: 'VALE3')

        Retorna:
            dict com recomendação completa e explicável
        """
        print(f"\n{'='*50}")
        print(f"  ANALISANDO: {ticker}")
        print(f"{'='*50}")

        logger.info(f"[{self.nome}] Iniciando análise completa de {ticker}")

        # ---- PASSO 1: NewsAgent coleta e analisa notícias ----
        print(f"\n📰 [NewsAgent] Coletando notícias...")
        resultado_news = self.news_agent.executar(ticker)
        analise_sentimento = resultado_news.get("analise_sentimento", {})
        print(f"   Sentimento: {analise_sentimento.get('label_geral', 'N/A')} "
              f"(score: {analise_sentimento.get('score_medio', 0):+.3f})")

        # ---- PASSO 2: TechnicalAgent calcula indicadores ----
        print(f"\n📊 [TechnicalAgent] Calculando indicadores técnicos...")
        resultado_tecnico = self.technical_agent.executar(ticker)
        indicadores = resultado_tecnico.get("indicadores", {})
        tendencia = resultado_tecnico.get("tendencia_geral", "NEUTRO")
        print(f"   Tendência técnica: {tendencia}")

        # ---- PASSO 3: DecisionAgent gera a recomendação ----
        print(f"\n🧠 [DecisionAgent] Gerando recomendação...")
        recomendacao = gerar_recomendacao(ticker, indicadores, analise_sentimento)

        # Adiciona contexto extra da análise multi-agent
        recomendacao["tendencia_tecnica"] = tendencia
        recomendacao["resumo_news"] = resultado_news.get("resumo", "")
        recomendacao["resumo_tecnico"] = resultado_tecnico.get("resumo", "")

        # ---- PASSO 4: Gera relatório explicável ----
        relatorio = self._gerar_relatorio_explicavel(ticker, resultado_news,
                                                       resultado_tecnico, recomendacao)
        recomendacao["relatorio_explicavel"] = relatorio

        # Exibe o resultado no console
        self._exibir_resultado(recomendacao)

        # Salva no histórico
        self.historico.append(recomendacao)

        # Salva em arquivo JSON na pasta reports/
        self._salvar_relatorio(ticker, recomendacao)

        return recomendacao

    def analisar_todos(self) -> list:
        """
        Analisa todos os 4 tickers monitorados em sequência.
        Retorna lista com as recomendações de cada um.
        """
        print(f"\n{'#'*60}")
        print(f"  QUANTUM FINANCE — ANÁLISE COMPLETA DO PORTFÓLIO")
        print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"{'#'*60}")

        resultados = []
        for ticker in TICKERS_MONITORADOS:
            try:
                resultado = self.analisar_ativo(ticker)
                resultados.append(resultado)
            except Exception as e:
                logger.error(f"Erro ao analisar {ticker}: {e}")
                resultados.append({
                    "ticker": ticker,
                    "recommendation": "ERRO",
                    "reasoning": str(e)
                })

        # Exibe o resumo do portfólio
        self._exibir_resumo_portfolio(resultados)

        return resultados

    def _gerar_relatorio_explicavel(self, ticker: str,
                                     resultado_news: dict,
                                     resultado_tecnico: dict,
                                     recomendacao: dict) -> str:
        """
        Gera um relatório em linguagem natural explicando
        como a decisão foi tomada. Isso é a EXPLICABILIDADE do AI!
        """
        analise_news = resultado_news.get("analise_sentimento", {})
        destaques = resultado_news.get("noticias_destaque", [])
        indicadores = resultado_tecnico.get("indicadores", {})
        atual = indicadores.get("atual", {})
        interp = indicadores.get("interpretacoes", {})
        tendencia = resultado_tecnico.get("tendencia_geral", "")
        rec = recomendacao.get("recommendation", "")
        confianca = recomendacao.get("confidence", 0)

        relatorio = f"""
RELATÓRIO DE ANÁLISE — {ticker}
Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
{'─'*50}

O QUE ACONTECEU NO MERCADO:
O ativo {ticker} foi analisado com base em dados de mercado dos últimos 6 meses
e notícias coletadas em tempo real dos principais portais financeiros.

ANÁLISE TÉCNICA:
A tendência identificada pelos indicadores técnicos é {tendencia}.

O RSI (Índice de Força Relativa) está em {atual.get('rsi', 0):.1f}, indicando
{interp.get('rsi', 'zona intermediária')}.

O MACD apresenta comportamento {interp.get('macd', 'neutro')}, sugerindo
{"momentum de alta" if "BULLISH" in interp.get('macd','') else "pressão vendedora" if "BEARISH" in interp.get('macd','') else "indefinição de tendência"}.

As médias móveis mostram: {interp.get('tendencia_medias', 'sem tendência clara')}.

ANÁLISE DE NOTÍCIAS:
Foram analisadas {analise_news.get('total_noticias', 0)} notícias recentes.
O sentimento geral foi {analise_news.get('label_geral', 'NEUTRO')}
(score: {analise_news.get('score_medio', 0):+.3f}).
"""

        if destaques:
            relatorio += "\nPRINCIPAIS NOTÍCIAS QUE INFLUENCIARAM A ANÁLISE:\n"
            for i, noticia in enumerate(destaques[:3], 1):
                relatorio += f"  {i}. [{noticia.get('sentimento','?')}] {noticia.get('titulo', '')[:70]}\n"

        relatorio += f"""
POR QUE A RECOMENDAÇÃO FOI {rec}:
{recomendacao.get('reasoning', '')}

NÍVEL DE CONFIANÇA: {confianca:.0%} ({recomendacao.get('confidence_label', '')})

VOTOS DOS INDICADORES:"""

        for detalhe in recomendacao.get("detalhes_votacao", []):
            relatorio += f"\n  • {detalhe}"

        relatorio += f"""

AVISO: Esta análise é meramente acadêmica e não constitui
conselho de investimento. Sempre consulte um profissional
certificado antes de tomar decisões financeiras.
{'─'*50}
"""
        return relatorio

    def _exibir_resultado(self, recomendacao: dict):
        """Exibe o resultado formatado no console."""
        emoji_map = {"COMPRAR": "🟢", "VENDER": "🔴", "AGUARDAR": "🟡", "ERRO": "⚫"}
        emoji = emoji_map.get(recomendacao.get("recommendation", ""), "⚪")

        print(f"\n{emoji} RESULTADO: {recomendacao.get('recommendation')}")
        print(f"   Confiança: {recomendacao.get('confidence', 0):.0%}")
        print(f"   {recomendacao.get('reasoning', '')[:120]}...")

    def _exibir_resumo_portfolio(self, resultados: list):
        """Exibe um resumo de todas as recomendações."""
        print(f"\n{'='*60}")
        print("  RESUMO DO PORTFÓLIO")
        print(f"{'='*60}")
        print(f"  {'TICKER':<8} {'RECOMENDAÇÃO':<12} {'CONFIANÇA':<10} {'SENTIMENTO'}")
        print(f"  {'-'*50}")

        for r in resultados:
            ticker = r.get("ticker", "?")
            rec = r.get("recommendation", "?")
            conf = r.get("confidence", 0)
            sent = r.get("sentiment_label", "?")
            emoji_map = {"COMPRAR": "🟢", "VENDER": "🔴", "AGUARDAR": "🟡"}
            emoji = emoji_map.get(rec, "⚫")
            print(f"  {ticker:<8} {emoji} {rec:<10} {conf:.0%}       {sent}")

        print(f"{'='*60}\n")

    def _salvar_relatorio(self, ticker: str, recomendacao: dict):
        """Salva o relatório em arquivo JSON."""
        try:
            nome_arquivo = f"relatorio_{ticker}_{timestamp_agora()}"
            # Remove as series (não são serializáveis em JSON)
            dados_salvar = {k: v for k, v in recomendacao.items()
                           if k != "series"}
            salvar_json(dados_salvar, nome_arquivo, pasta="reports")
        except Exception as e:
            logger.warning(f"Não foi possível salvar relatório: {e}")
