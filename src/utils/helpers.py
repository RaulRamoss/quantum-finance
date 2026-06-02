import os
import json
import logging
from datetime import datetime


def configurar_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    return logging.getLogger("QuantumFinance")

logger = configurar_logging()


def salvar_json(dados, nome_arquivo, pasta="data"):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"{nome_arquivo}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    return caminho


def timestamp_agora():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def limpar_texto(texto):
    import re
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def score_para_confianca(score):
    if score >= 0.8:
        return "MUITO ALTA"
    elif score >= 0.6:
        return "ALTA"
    elif score >= 0.4:
        return "MEDIA"
    else:
        return "BAIXA"
