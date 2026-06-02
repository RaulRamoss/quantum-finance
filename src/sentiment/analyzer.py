import feedparser
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

FEEDS_RSS = {
    "infomoney": "https://www.infomoney.com.br/feed/",
    "reuters": "https://feeds.reuters.com/reuters/BRbusinessNews",
    "valor": "https://valor.globo.com/rss/home",
}

KEYWORDS = {
    "VALE3": ["vale", "minerio", "mineracao", "ferro"],
    "PETR4": ["petrobras", "petroleo", "combustivel", "pre-sal"],
    "BBAS3": ["banco do brasil", "agrobanco", "credito rural"],
    "ITUB4": ["itau", "itau unibanco", "banco itau"],
}

vader = SentimentIntensityAnalyzer()
vader.lexicon.update({
    "lucro": 2.5, "crescimento": 2.0, "alta": 1.5,
    "dividendo": 2.0, "superou": 2.5, "recorde": 2.5,
    "queda": -1.5, "perda": -2.0, "prejuizo": -2.5,
    "crise": -2.5, "risco": -1.5, "inadimplencia": -2.0,
})


def buscar_noticias(ticker, max_noticias=10):
    keywords = KEYWORDS.get(ticker, [ticker.lower()])
    noticias = []
    for fonte, url in FEEDS_RSS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                titulo = entry.get("title", "")
                resumo = entry.get("summary", "")
                if any(kw in (titulo + resumo).lower() for kw in keywords):
                    noticias.append({
                        "titulo": titulo, "resumo": resumo[:300],
                        "fonte": fonte,
                        "data": entry.get("published", str(datetime.now())),
                        "link": entry.get("link", ""),
                    })
        except:
            continue
    if not noticias:
        noticias = _noticias_simuladas(ticker)
    return noticias[:max_noticias]


def _noticias_simuladas(ticker):
    exemplos = {
        "VALE3": [
            {"titulo": "Vale reporta aumento na producao de minerio de ferro",
             "resumo": "Resultados acima das expectativas com alta na producao."},
            {"titulo": "Demanda chinesa impulsiona acoes da Vale",
             "resumo": "Crescimento da construcao civil na China beneficia a Vale."},
        ],
        "PETR4": [
            {"titulo": "Petrobras eleva estimativa de producao",
             "resumo": "Empresa revisa para cima suas metas no pre-sal."},
            {"titulo": "Variacao do cambio afeta resultados da Petrobras",
             "resumo": "Dolar forte pressiona custos mas exportacoes compensam."},
        ],
        "BBAS3": [
            {"titulo": "Banco do Brasil registra lucro recorde no trimestre",
             "resumo": "Resultado impulsionado pelo credito rural."},
        ],
        "ITUB4": [
            {"titulo": "Itau apresenta crescimento em carteira de credito",
             "resumo": "Banco reporta expansao de 12% no credito total."},
        ],
    }
    base = exemplos.get(ticker, [{"titulo": f"Acao {ticker} em destaque", "resumo": "Sem noticias recentes."}])
    return [{**n, "fonte": "simulado", "data": str(datetime.now()), "link": ""} for n in base]


def analisar_sentimento(texto):
    if not texto:
        return {"score": 0.0, "label": "NEUTRO"}
    scores = vader.polarity_scores(texto)
    compound = scores["compound"]
    label = "POSITIVO" if compound >= 0.05 else "NEGATIVO" if compound <= -0.05 else "NEUTRO"
    return {"score": round(compound, 3), "label": label,
            "positivo": round(scores["pos"], 3),
            "negativo": round(scores["neg"], 3),
            "neutro": round(scores["neu"], 3)}


def analisar_conjunto_noticias(noticias):
    if not noticias:
        return {"score_medio": 0.0, "label_geral": "NEUTRO", "total_noticias": 0,
                "noticias_positivas": 0, "noticias_negativas": 0, "noticias_neutras": 0, "detalhes": []}
    scores = []
    contagem = {"POSITIVO": 0, "NEGATIVO": 0, "NEUTRO": 0}
    detalhes = []
    for n in noticias:
        s = analisar_sentimento(n["titulo"] + ". " + n.get("resumo", ""))
        scores.append(s["score"])
        contagem[s["label"]] += 1
        detalhes.append({"titulo": n["titulo"][:80], "fonte": n.get("fonte", "?"),
                         "sentimento": s["label"], "score": s["score"]})
    score_medio = sum(scores) / len(scores)
    label_geral = "POSITIVO" if score_medio >= 0.05 else "NEGATIVO" if score_medio <= -0.05 else "NEUTRO"
    return {"score_medio": round(score_medio, 3), "label_geral": label_geral,
            "total_noticias": len(noticias),
            "noticias_positivas": contagem["POSITIVO"],
            "noticias_negativas": contagem["NEGATIVO"],
            "noticias_neutras": contagem["NEUTRO"],
            "detalhes": detalhes}
