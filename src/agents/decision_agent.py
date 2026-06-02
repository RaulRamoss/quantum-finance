import os
import json
from datetime import datetime
from src.agents.news_agent import NewsAgent
from src.agents.technical_agent import TechnicalAgent
from src.recommendation.engine import gerar_recomendacao
from src.utils.helpers import timestamp_agora

TICKERS_MONITORADOS = ["VALE3", "PETR4", "BBAS3", "ITUB4"]


class DecisionAgent:
    def __init__(self):
        self.news_agent = NewsAgent()
        self.technical_agent = TechnicalAgent()

    def analisar_ativo(self, ticker):
        print(f"\n--- {ticker} ---")

        print("buscando noticias...", end=" ", flush=True)
        resultado_news = self.news_agent.executar(ticker)
        sentimento = resultado_news.get("analise_sentimento", {})
        print(f"sentimento: {sentimento.get('label_geral')} ({sentimento.get('score_medio', 0):+.3f})")

        print("calculando indicadores...", end=" ", flush=True)
        resultado_tecnico = self.technical_agent.executar(ticker)
        indicadores = resultado_tecnico.get("indicadores", {})
        print(f"tendencia: {resultado_tecnico.get('tendencia_geral')}")

        recomendacao = gerar_recomendacao(ticker, indicadores, sentimento)
        recomendacao["tendencia_tecnica"] = resultado_tecnico.get("tendencia_geral")

        emojis = {"COMPRAR": "verde", "VENDER": "vermelho", "AGUARDAR": "amarelo"}
        emoji_map = {"COMPRAR": "COMPRAR", "VENDER": "VENDER", "AGUARDAR": "AGUARDAR"}
        e = {"COMPRAR": "🟢", "VENDER": "🔴", "AGUARDAR": "🟡"}.get(recomendacao["recommendation"], "⚪")
        print(f"\n{e} RECOMENDACAO: {recomendacao['recommendation']}")
        print(f"   confianca: {recomendacao['confidence']:.0%}")
        print(f"   {recomendacao['reasoning'][:120]}...")

        self._salvar(ticker, recomendacao)
        return recomendacao

    def analisar_todos(self):
        print(f"\nIniciando analise de {len(TICKERS_MONITORADOS)} acoes...")
        resultados = []
        for ticker in TICKERS_MONITORADOS:
            try:
                r = self.analisar_ativo(ticker)
                resultados.append(r)
            except Exception as e:
                print(f"erro ao analisar {ticker}: {e}")
                resultados.append({"ticker": ticker, "recommendation": "ERRO", "confidence": 0})

        print(f"\n{'='*45}")
        print("  RESUMO FINAL")
        print(f"{'='*45}")
        for r in resultados:
            e = {"COMPRAR": "🟢", "VENDER": "🔴", "AGUARDAR": "🟡"}.get(r.get("recommendation", ""), "⚪")
            print(f"  {r.get('ticker'):<6} {e} {r.get('recommendation'):<10} {r.get('confidence', 0):.0%} de confianca")
        print(f"{'='*45}\n")
        return resultados

    def _salvar(self, ticker, recomendacao):
        try:
            os.makedirs("reports", exist_ok=True)
            nome = f"reports/relatorio_{ticker}_{timestamp_agora()}.json"
            dados = {k: v for k, v in recomendacao.items() if k != "series"}
            with open(nome, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            pass
