from src.sentiment.analyzer import buscar_noticias, analisar_conjunto_noticias


class NewsAgent:
    def __init__(self):
        self.nome = "NewsAgent"

    def executar(self, ticker):
        noticias = buscar_noticias(ticker, max_noticias=10)
        analise = analisar_conjunto_noticias(noticias)
        destaques = sorted(analise.get("detalhes", []),
                           key=lambda x: abs(x.get("score", 0)), reverse=True)[:3]
        return {
            "ticker": ticker,
            "analise_sentimento": analise,
            "noticias_destaque": destaques,
        }
