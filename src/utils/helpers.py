# ============================================================
# helpers.py — Funções auxiliares do projeto
# Aqui ficam funções pequenas que vários módulos usam
# ============================================================

import os
import json
import logging
from datetime import datetime

# Configura o logging pra gente ver o que tá acontecendo no console
# É tipo um print mais organizado que mostra a hora e o nível do log
def configurar_logging(nivel=logging.INFO):
    """
    Configura o sistema de logs da aplicação.
    Vai aparecer no console com data/hora e o nível (INFO, ERROR, etc.)
    """
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("QuantumFinance")


# Logger global que outros módulos podem importar
logger = configurar_logging()


def salvar_json(dados: dict, nome_arquivo: str, pasta: str = "data"):
    """
    Salva um dicionário como arquivo JSON.
    Útil pra guardar os resultados das análises.

    Parâmetros:
        dados: o dicionário que queremos salvar
        nome_arquivo: nome do arquivo (sem .json)
        pasta: onde salvar (padrão: pasta data/)
    """
    # Cria a pasta se não existir
    os.makedirs(pasta, exist_ok=True)

    # Monta o caminho completo do arquivo
    caminho = os.path.join(pasta, f"{nome_arquivo}.json")

    # Salva o arquivo
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    logger.info(f"Dados salvos em: {caminho}")
    return caminho


def carregar_json(caminho: str) -> dict:
    """
    Carrega um arquivo JSON e retorna como dicionário.
    Retorna None se o arquivo não existir.
    """
    if not os.path.exists(caminho):
        logger.warning(f"Arquivo não encontrado: {caminho}")
        return None

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    return dados


def formatar_porcentagem(valor: float) -> str:
    """
    Formata um número como porcentagem com 2 casas decimais.
    Ex: 0.1523 → '+15.23%'
    """
    if valor >= 0:
        return f"+{valor * 100:.2f}%"
    else:
        return f"{valor * 100:.2f}%"


def calcular_variacao(preco_anterior: float, preco_atual: float) -> float:
    """
    Calcula a variação percentual entre dois preços.
    Retorna um float (ex: 0.05 = +5%)
    """
    if preco_anterior == 0:
        return 0.0
    return (preco_atual - preco_anterior) / preco_anterior


def timestamp_agora() -> str:
    """
    Retorna o timestamp atual formatado como string.
    Útil pra nomear arquivos de relatório.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def limpar_texto(texto: str) -> str:
    """
    Remove caracteres especiais e espaços extras de um texto.
    Importante antes de mandar pro analisador de sentimento.
    """
    import re
    # Remove HTML tags se tiver
    texto = re.sub(r'<[^>]+>', '', texto)
    # Remove espaços duplos
    texto = re.sub(r'\s+', ' ', texto)
    # Remove espaços no início e fim
    texto = texto.strip()
    return texto


def interpretar_rsi(rsi: float) -> str:
    """
    Interpreta o valor do RSI em linguagem natural.
    RSI > 70 = sobrecomprado (possível queda)
    RSI < 30 = sobrevendido (possível subida)
    """
    if rsi >= 70:
        return "SOBRECOMPRADO (possível pressão de venda)"
    elif rsi <= 30:
        return "SOBREVENDIDO (possível oportunidade de compra)"
    elif rsi >= 60:
        return "FORTE (tendência de alta)"
    elif rsi <= 40:
        return "FRACO (tendência de baixa)"
    else:
        return "NEUTRO (sem tendência clara)"


def interpretar_macd(macd: float, signal: float) -> str:
    """
    Interpreta o sinal do MACD.
    Quando MACD cruza pra cima do Signal = sinal de compra (bullish)
    Quando MACD cruza pra baixo do Signal = sinal de venda (bearish)
    """
    if macd > signal:
        diferenca = macd - signal
        if diferenca > 0.5:
            return "BULLISH FORTE (MACD bem acima do Signal)"
        return "BULLISH (MACD acima do Signal - sinal de compra)"
    else:
        diferenca = signal - macd
        if diferenca > 0.5:
            return "BEARISH FORTE (MACD bem abaixo do Signal)"
        return "BEARISH (MACD abaixo do Signal - sinal de venda)"


def score_para_confianca(score: float) -> str:
    """
    Converte um score numérico em nível de confiança.
    """
    if score >= 0.8:
        return "MUITO ALTA"
    elif score >= 0.6:
        return "ALTA"
    elif score >= 0.4:
        return "MÉDIA"
    elif score >= 0.2:
        return "BAIXA"
    else:
        return "MUITO BAIXA"
