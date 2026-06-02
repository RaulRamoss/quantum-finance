# ============================================================
# main.py — Ponto de Entrada do QuantumFinance
#
# Este é o arquivo principal. Ao rodar "python main.py",
# o usuário pode interagir com o agente via terminal.
#
# Modos disponíveis:
# 1. Análise completa de todos os tickers
# 2. Análise de um ticker específico
# 3. Interface conversacional (LangChain Agent)
# ============================================================

import sys
import os

# Adiciona a pasta raiz ao path pra poder importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.decision_agent import DecisionAgent, TICKERS_MONITORADOS
from src.utils.helpers import logger


def modo_analise_completa():
    """Analisa todos os 4 tickers monitorados."""
    agente = DecisionAgent()
    resultados = agente.analisar_todos()
    return resultados


def modo_analise_ticker(ticker: str):
    """Analisa um ticker específico."""
    ticker = ticker.upper().strip()
    if ticker not in TICKERS_MONITORADOS:
        print(f"⚠️  Ticker {ticker} não está na lista monitorada.")
        print(f"   Tickers disponíveis: {', '.join(TICKERS_MONITORADOS)}")
        ticker_input = input("   Continuar mesmo assim? (s/n): ")
        if ticker_input.lower() != "s":
            return None

    agente = DecisionAgent()
    resultado = agente.analisar_ativo(ticker)
    return resultado


def modo_conversacional():
    """
    Interface conversacional usando LangChain Agent com ReAct.

    O agente usa as ferramentas (tools) para responder perguntas
    sobre ações de forma autônoma, seguindo o padrão ReAct:
    Thought → Action → Observation → Thought → ...
    """
    print("\n" + "="*60)
    print("  QUANTUM FINANCE — MODO CONVERSACIONAL")
    print("  Powered by LangChain + ReAct")
    print("="*60)
    print("\nExemplos de perguntas:")
    print("  • 'Qual sua recomendação para VALE3?'")
    print("  • 'Como estão as notícias da Petrobras?'")
    print("  • 'Analise tecnicamente o ITUB4'")
    print("  • 'exit' para sair\n")

    # Tenta importar o LangChain
    # Se não tiver configurado, cai pra modo simples
    try:
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain_core.prompts import PromptTemplate
        from src.tools.financial_tools import TODAS_FERRAMENTAS

        # Prompt do agente ReAct
        # O {tools} e {tool_names} são preenchidos automaticamente
        # O {input} é a pergunta do usuário
        # O {agent_scratchpad} é onde o agente registra seu raciocínio
        template_prompt = """
Você é o QuantumFinance, um assistente especializado em análise de investimentos na B3.
Você analisa ações brasileiras usando indicadores técnicos e notícias do mercado.

Tickers que você monitora: VALE3, PETR4, BBAS3, ITUB4

Você tem acesso às seguintes ferramentas:
{tools}

Responda SEMPRE em português. Seja objetivo e claro nas suas análises.

Use o seguinte formato:
Question: a pergunta do usuário
Thought: o que você precisa fazer pra responder
Action: o nome da ferramenta a usar
Action Input: o input pra ferramenta
Observation: o resultado da ferramenta
... (repita Thought/Action/Action Input/Observation quantas vezes precisar)
Thought: Agora sei a resposta final
Final Answer: a resposta final para o usuário

Question: {input}
{agent_scratchpad}
"""
        prompt = PromptTemplate.from_template(template_prompt)

        # Tenta usar OpenAI se tiver API key configurada
        # Senão usa um modelo local ou fallback
        try:
            from langchain_openai import ChatOpenAI
            from dotenv import load_dotenv
            load_dotenv()

            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
                agent = create_react_agent(llm, TODAS_FERRAMENTAS, prompt)
                agente_executor = AgentExecutor(
                    agent=agent,
                    tools=TODAS_FERRAMENTAS,
                    verbose=True,  # Mostra o raciocínio do agente
                    max_iterations=5,
                    handle_parsing_errors=True
                )

                print("✅ Modo LangChain ReAct ativado (OpenAI GPT-3.5)")
                _loop_conversa(agente_executor)
                return
        except Exception:
            pass

        # Fallback: modo simples sem LLM
        print("ℹ️  API key não configurada. Usando modo simples.")
        _modo_simples_interativo()

    except ImportError as e:
        print(f"⚠️  LangChain não disponível: {e}")
        print("   Usando modo simples interativo...")
        _modo_simples_interativo()


def _loop_conversa(agente_executor):
    """Loop principal de conversa com o agente LangChain."""
    while True:
        pergunta = input("\n💬 Você: ").strip()
        if pergunta.lower() in ["exit", "sair", "quit", ""]:
            print("\n👋 Até logo! Bons investimentos!")
            break
        try:
            resposta = agente_executor.invoke({"input": pergunta})
            print(f"\n🤖 QuantumFinance: {resposta.get('output', 'Não consegui processar sua pergunta.')}")
        except Exception as e:
            print(f"\n❌ Erro: {e}")


def _modo_simples_interativo():
    """
    Modo interativo simples sem LLM.
    Responde comandos diretos do usuário.
    """
    agente = DecisionAgent()

    print("Comandos disponíveis:")
    print("  VALE3 / PETR4 / BBAS3 / ITUB4 — analisar ticker")
    print("  TODOS — analisar todos os tickers")
    print("  SAIR — encerrar\n")

    while True:
        comando = input("💬 Comando: ").strip().upper()

        if comando in ["SAIR", "EXIT", "QUIT", ""]:
            print("\n👋 Até logo!")
            break
        elif comando == "TODOS":
            agente.analisar_todos()
        elif comando in TICKERS_MONITORADOS or len(comando) <= 6:
            agente.analisar_ativo(comando)
        else:
            print(f"  Comando não reconhecido: '{comando}'")
            print(f"  Use um dos tickers: {', '.join(TICKERS_MONITORADOS)} ou TODOS")


def menu_principal():
    """Menu principal da aplicação."""
    print("\n" + "🚀 "*20)
    print("\n  QUANTUM FINANCE — AI Agent para Investimentos")
    print("  Projeto Acadêmico — FIAP Pós Tech AI for Devs\n")
    print("  Tickers monitorados:", ", ".join(TICKERS_MONITORADOS))
    print("\n" + "─"*50)
    print("  [1] Análise completa (todos os tickers)")
    print("  [2] Analisar um ticker específico")
    print("  [3] Modo conversacional (LangChain Agent)")
    print("  [4] Sair")
    print("─"*50)

    escolha = input("\nEscolha uma opção (1-4): ").strip()

    if escolha == "1":
        modo_analise_completa()
    elif escolha == "2":
        ticker = input("Digite o ticker (ex: VALE3): ").strip()
        modo_analise_ticker(ticker)
    elif escolha == "3":
        modo_conversacional()
    elif escolha == "4":
        print("\n👋 Até logo!")
        sys.exit(0)
    else:
        print("Opção inválida!")
        menu_principal()


# ============================================================
# Ponto de entrada: só executa se rodar diretamente
# (não executa se importado por outro arquivo)
# ============================================================
if __name__ == "__main__":
    # Cria as pastas necessárias se não existirem
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Verifica se passou um ticker como argumento na linha de comando
    # Ex: python main.py VALE3
    if len(sys.argv) > 1:
        ticker_arg = sys.argv[1].upper()
        if ticker_arg == "TODOS":
            modo_analise_completa()
        else:
            modo_analise_ticker(ticker_arg)
    else:
        # Sem argumentos: abre o menu interativo
        menu_principal()
