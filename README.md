# 🤖 QuantumFinance — AI Agent para Recomendação de Investimentos

> Projeto acadêmico desenvolvido para a pós-graduação em AI for Devs — FIAP  
> Tema: Construção de AI Agents autônomos aplicados ao mercado financeiro brasileiro

---

## 📌 Sobre o Projeto

O **QuantumFinance** é um assistente de investimentos baseado em **AI Agents** que analisa ações da B3 e gera recomendações de **COMPRAR**, **VENDER** ou **AGUARDAR** de forma autônoma e explicável.

O agente combina:
- 📰 Análise de notícias e sentimento de mercado em tempo real
- 📊 Indicadores técnicos (RSI, MACD, Médias Móveis, Bollinger Bands)
- 🧠 Raciocínio no padrão ReAct (Reasoning + Acting)
- 💬 Interface conversacional para o usuário

---

## 📈 Ações Monitoradas

| Ticker | Empresa     | Setor      |
|--------|-------------|------------|
| VALE3  | Vale S.A.   | Mineração  |
| PETR4  | Petrobras   | Energia    |
| BBAS3  | Banco do Brasil | Financeiro |
| ITUB4  | Itaú Unibanco | Financeiro |

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    QUANTUM FINANCE AGENT                     │
├──────────────────┬──────────────────┬───────────────────────┤
│   NEWS AGENT     │ TECHNICAL AGENT  │   DECISION AGENT      │
│                  │                  │                        │
│ • Busca RSS      │ • Preços (yfinance│ • Consolida análises  │
│ • Sentimento     │ • RSI / MACD     │ • Gera recomendação    │
│ • Score impacto  │ • Bollinger      │ • Explica raciocínio   │
│                  │ • Volume         │ • Nível de confiança   │
└──────────────────┴──────────────────┴───────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  RECOMENDAÇÃO     │
                    │  COMPRAR / VENDER │
                    │  / AGUARDAR       │
                    └───────────────────┘
```

---

## 📂 Estrutura do Projeto

```
quantum_finance/
├── data/                        # Dados coletados (CSVs, JSONs)
├── notebooks/
│   └── quantum_finance.ipynb   # Notebook completo com análises
├── reports/                     # Relatórios gerados pelo agente
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── news_agent.py        # Agente responsável por notícias
│   │   ├── technical_agent.py   # Agente responsável por indicadores
│   │   └── decision_agent.py    # Agente de decisão final
│   ├── tools/
│   │   ├── __init__.py
│   │   └── financial_tools.py   # Ferramentas do agente (LangChain tools)
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── technical.py         # RSI, MACD, Médias, Bollinger
│   ├── sentiment/
│   │   ├── __init__.py
│   │   └── analyzer.py          # Análise de sentimento (VADER)
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── engine.py            # Motor de recomendação
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Funções auxiliares
├── main.py                      # Ponto de entrada da aplicação
├── requirements.txt             # Dependências
└── README.md                    # Este arquivo
```

---

## 🚀 Como Executar Localmente

### 1. Clone o repositório (ou descompacte o zip)

```bash
git clone https://github.com/RaulRamoss/quantum-finance.git
cd quantum-finance
```

### 2. Crie um ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o agente principal

```bash
python main.py
```

### 5. (Opcional) Abra o Notebook

```bash
jupyter notebook notebooks/quantum_finance.ipynb
```

---

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto (opcional, para uso com OpenAI):

```env
OPENAI_API_KEY=sua_chave_aqui
```

> **Nota:** O projeto funciona sem chave de API! A análise de sentimento usa VADER (offline) e os dados de mercado vêm do Yahoo Finance (gratuito).

---

## 🔧 Componentes Explicados

### 📰 News Agent
Responsável por coletar notícias dos principais portais financeiros via RSS (InfoMoney, Reuters, Valor Econômico). Extrai o sentimento de cada notícia usando VADER e calcula um score de impacto.

### 📊 Technical Agent
Coleta o histórico de preços via `yfinance` e calcula todos os indicadores técnicos: RSI, MACD, SMA/EMA 20 e 50, Bandas de Bollinger e análise de volume.

### 🧠 Decision Agent
Consolida as análises dos dois agentes anteriores e aplica a lógica de decisão para gerar a recomendação final com justificativa em linguagem natural.

### 🛠️ Tools (Ferramentas LangChain)
Funções registradas como ferramentas do agente LangChain:
- `search_news(ticker)` — busca notícias do ativo
- `get_price_data(ticker, period)` — obtém histórico de preços
- `calculate_indicators(data)` — calcula indicadores técnicos
- `analyze_sentiment(news)` — classifica sentimento
- `generate_recommendation(analysis)` — gera recomendação final

---

## 📊 Exemplo de Saída

```json
{
  "ticker": "VALE3",
  "recommendation": "COMPRAR",
  "confidence": 0.82,
  "sentiment_score": 0.45,
  "sentiment_label": "POSITIVO",
  "reasoning": "RSI em 42 (zona neutra/favorável), MACD com cruzamento bullish, notícias majoritariamente positivas sobre demanda por minério de ferro na China.",
  "indicators": {
    "RSI": 42.3,
    "MACD": "BULLISH",
    "SMA20_vs_SMA50": "SMA20 acima da SMA50",
    "Bollinger": "Preço próximo da banda inferior (oportunidade de compra)",
    "Volume": "Volume acima da média (confirmação)"
  }
}
```

---
