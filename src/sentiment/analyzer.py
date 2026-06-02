# ============================================================
# analyzer.py — Análise de Sentimento das Notícias
#
# Aqui a gente analisa o "humor" das notícias financeiras.
# Usamos o VADER que funciona offline (sem precisar de API).
# O score vai de -1 (muito negativo) a +1 (muito positivo).
# ============================================================

import feedparser
import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from src.utils.helpers import logger, limpar_texto


# ============================================================
# FEEDS RSS dos portais financeiros brasileiros
# RSS é tipo um feed de notícias em formato XML estruturado
# ============================================================
FEEDS_RSS = {
    "infomoney": "https://www.infomoney.com.br/feed/",
    "reuters_brasil": "https://feeds.reuters.com/reuters/BRbusinessNews",
    "valor_economico": "https://valor.globo.com/rss/home",
    "money_times": "https://www.moneytimes.com.br/feed/",
}

# Palavras-chave associadas a cada ticker
# Usamos isso pra filtrar notícias relevantes
KEYWORDS_TICKER = {
    "VALE3": ["vale", "minério", "ferro", "mineração", "pedreiras", "BHP", "minério de ferro"],
    "PETR4": ["petrobras", "petróleo", "combustível", "refinaria", "pré-sal", "oil"],
    "BBAS3": ["banco do brasil", "BB", "agrobanco", "crédito rural"],
    "ITUB4": ["itaú", "itaú unibanco", "itau", "banco itau"],
}


def buscar_noticias(ticker: str, max_noticias: int = 10) -> list:
    """
    Busca notícias relacionadas a um ticker nos feeds RSS.

    Parâmetros:
        ticker: código da ação (ex: "VALE3")
        max_noticias: número máximo de notícias pra retornar

    Retorna uma lista de dicionários com título, resumo e data.
    """
    logger.info(f"Buscando notícias para {ticker}...")

    # Pega as palavras-chave do ticker
    keywords = KEYWORDS_TICKER.get(ticker, [ticker.lower()])
    noticias_encontradas = []

    # Percorre cada feed RSS
    for fonte, url in FEEDS_RSS.items():
        try:
            # feedparser lê o RSS e estrutura as entradas
            feed = feedparser.parse(url)

            for entry in feed.entries:
                # Pega título e resumo da notícia
                titulo = entry.get("title", "")
                resumo = entry.get("summary", entry.get("description", ""))

                # Verifica se a notícia é sobre o ticker que nos interessa
                texto_completo = (titulo + " " + resumo).lower()
                relevante = any(kw.lower() in texto_completo for kw in keywords)

                if relevante:
                    # Tenta pegar a data da publicação
                    data_pub = entry.get("published", str(datetime.now()))

                    noticias_encontradas.append({
                        "titulo": limpar_texto(titulo),
                        "resumo": limpar_texto(resumo[:300]),  # limita o tamanho
                        "fonte": fonte,
                        "data": data_pub,
                        "link": entry.get("link", ""),
                    })

            logger.info(f"  Feed {fonte}: OK")

        except Exception as e:
            # Se um feed falhar, continua pros outros
            logger.warning(f"  Erro no feed {fonte}: {e}")
            continue

    # Se não achou nada nos feeds, cria notícias fictícias pra demonstração
    # (isso é útil quando rodamos offline ou os feeds estão fora do ar)
    if len(noticias_encontradas) == 0:
        logger.warning(f"Nenhuma notícia encontrada para {ticker}. Usando dados simulados.")
        noticias_encontradas = _gerar_noticias_simuladas(ticker)

    logger.info(f"Total de notícias encontradas para {ticker}: {len(noticias_encontradas)}")
    return noticias_encontradas[:max_noticias]


def _gerar_noticias_simuladas(ticker: str) -> list:
    """
    Gera notícias simuladas quando os feeds estão indisponíveis.
    Útil pra testes e demonstrações offline.
    """
    templates = {
        "VALE3": [
            {"titulo": "Vale reporta aumento na produção de minério de ferro no trimestre",
             "resumo": "A mineradora divulgou resultados acima das expectativas do mercado, com alta na produção."},
            {"titulo": "Demanda chinesa por aço impulsiona ações da Vale",
             "resumo": "Analistas apontam crescimento da construção civil na China como fator positivo para a Vale."},
            {"titulo": "Vale anuncia dividendos acima do esperado",
             "resumo": "Empresa distribui R$ 4,50 por ação em dividendos, superando estimativas dos analistas."},
        ],
        "PETR4": [
            {"titulo": "Petrobras eleva estimativa de produção para o próximo ano",
             "resumo": "A estatal revisou para cima suas metas de produção de petróleo no pré-sal."},
            {"titulo": "Variação do câmbio afeta resultados da Petrobras",
             "resumo": "Dólar forte pressiona custos da empresa, mas exportações de petróleo compensam."},
            {"titulo": "Petrobras investe em energia renovável como diversificação",
             "resumo": "Empresa anuncia plano de investimentos em energia eólica offshore."},
        ],
        "BBAS3": [
            {"titulo": "Banco do Brasil registra lucro recorde no trimestre",
             "resumo": "Resultado impulsionado pelo crédito rural e queda na inadimplência."},
            {"titulo": "BB amplia crédito para o agronegócio",
             "resumo": "Banco anuncia R$ 50 bilhões em linhas de crédito rural para a safra 2024/2025."},
        ],
        "ITUB4": [
            {"titulo": "Itaú apresenta crescimento em carteira de crédito",
             "resumo": "Banco reporta expansão de 12% no crédito total com queda na inadimplência."},
            {"titulo": "Itaú Unibanco supera expectativas com resultado do 3T",
             "resumo": "Lucro líquido recorrente cresce 15% na comparação anual, superando consenso."},
        ],
    }

    noticias = templates.get(ticker, [
        {"titulo": f"Ação {ticker} em destaque no mercado",
         "resumo": f"Investidores acompanham movimentos de {ticker} nesta sessão."},
    ])

    # Adiciona metadados às notícias simuladas
    return [
        {
            "titulo": n["titulo"],
            "resumo": n["resumo"],
            "fonte": "simulado",
            "data": str(datetime.now()),
            "link": "",
        }
        for n in noticias
    ]


# ============================================================
# ANÁLISE DE SENTIMENTO COM VADER
# VADER funciona bem com textos curtos em inglês, mas também
# funciona razoavelmente com textos em português
# ============================================================

# Instancia o analisador VADER (carrega uma vez, usa várias)
_vader = SentimentIntensityAnalyzer()

# Palavras financeiras em português e seus pesos no VADER
# O VADER tem dicionário em inglês, então a gente reforça as palavras em PT
PALAVRAS_FINANCEIRAS_PT = {
    # Palavras positivas
    "lucro": 2.5,
    "crescimento": 2.0,
    "alta": 1.5,
    "valorização": 2.0,
    "dividendo": 2.0,
    "superou": 2.5,
    "recorde": 2.5,
    "expansão": 1.8,
    "positivo": 1.5,
    "aprovação": 1.5,
    # Palavras negativas
    "queda": -1.5,
    "perda": -2.0,
    "prejuízo": -2.5,
    "crise": -2.5,
    "risco": -1.5,
    "inadimplência": -2.0,
    "multa": -2.0,
    "negativo": -1.5,
    "baixa": -1.5,
    "desaceleração": -1.8,
}

# Adiciona as palavras financeiras ao dicionário do VADER
_vader.lexicon.update(PALAVRAS_FINANCEIRAS_PT)


def analisar_sentimento(texto: str) -> dict:
    """
    Analisa o sentimento de um texto e retorna score e classificação.

    Parâmetros:
        texto: string com o texto a ser analisado

    Retorna:
        dict com score (-1 a +1), label e scores individuais
    """
    # Limpa o texto antes de analisar
    texto_limpo = limpar_texto(texto)

    if not texto_limpo:
        return {
            "score": 0.0,
            "label": "NEUTRO",
            "compound": 0.0,
            "positivo": 0.0,
            "negativo": 0.0,
            "neutro": 1.0,
        }

    # VADER calcula 4 scores:
    # pos: proporção de palavras positivas
    # neg: proporção de palavras negativas
    # neu: proporção de palavras neutras
    # compound: score geral de -1 a +1 (este é o que usamos)
    scores = _vader.polarity_scores(texto_limpo)

    compound = scores["compound"]

    # Classifica com base no compound score
    if compound >= 0.05:
        label = "POSITIVO"
    elif compound <= -0.05:
        label = "NEGATIVO"
    else:
        label = "NEUTRO"

    return {
        "score": round(compound, 3),          # Score principal (-1 a +1)
        "label": label,                         # Classificação textual
        "compound": round(compound, 3),
        "positivo": round(scores["pos"], 3),
        "negativo": round(scores["neg"], 3),
        "neutro": round(scores["neu"], 3),
    }


def analisar_conjunto_noticias(noticias: list) -> dict:
    """
    Analisa o sentimento de uma lista de notícias e consolida os resultados.

    Calcula:
    - Score médio de sentimento
    - Score de impacto (considera quantidade e intensidade)
    - Classificação geral
    - Resumo das principais notícias
    """
    if not noticias:
        return {
            "score_medio": 0.0,
            "score_impacto": 0.0,
            "label_geral": "NEUTRO",
            "total_noticias": 0,
            "noticias_positivas": 0,
            "noticias_negativas": 0,
            "noticias_neutras": 0,
            "detalhes": [],
        }

    detalhes = []
    scores = []
    contagem = {"POSITIVO": 0, "NEGATIVO": 0, "NEUTRO": 0}

    for noticia in noticias:
        # Analisa título + resumo juntos
        texto = noticia["titulo"] + ". " + noticia.get("resumo", "")
        sentimento = analisar_sentimento(texto)

        scores.append(sentimento["score"])
        contagem[sentimento["label"]] += 1

        detalhes.append({
            "titulo": noticia["titulo"][:80],  # limita pra não ficar muito longo
            "fonte": noticia.get("fonte", "desconhecida"),
            "sentimento": sentimento["label"],
            "score": sentimento["score"],
        })

    # Calcula o score médio de todas as notícias
    score_medio = sum(scores) / len(scores) if scores else 0.0

    # Score de impacto: considera a intensidade dos sentimentos
    # Damos mais peso às notícias mais fortes (positivas ou negativas)
    score_impacto = sum(abs(s) * (1 if s >= 0 else -1) for s in scores) / len(scores) if scores else 0.0

    # Determina a classificação geral
    if score_medio >= 0.05:
        label_geral = "POSITIVO"
    elif score_medio <= -0.05:
        label_geral = "NEGATIVO"
    else:
        label_geral = "NEUTRO"

    return {
        "score_medio": round(score_medio, 3),
        "score_impacto": round(score_impacto, 3),
        "label_geral": label_geral,
        "total_noticias": len(noticias),
        "noticias_positivas": contagem["POSITIVO"],
        "noticias_negativas": contagem["NEGATIVO"],
        "noticias_neutras": contagem["NEUTRO"],
        "detalhes": detalhes,
    }
