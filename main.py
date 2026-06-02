import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.decision_agent import DecisionAgent, TICKERS_MONITORADOS


def menu():
    print("\n" + "="*50)
    print("  QUANTUM FINANCE - AI Agent de Investimentos")
    print("  FIAP - Pos Tech AI for Devs")
    print("="*50)
    print(f"\n  Tickers monitorados: {', '.join(TICKERS_MONITORADOS)}\n")
    print("  [1] Analisar todos os tickers")
    print("  [2] Analisar um ticker especifico")
    print("  [3] Sair")
    print("="*50)

    escolha = input("\nEscolha uma opcao (1-3): ").strip()

    agente = DecisionAgent()

    if escolha == "1":
        agente.analisar_todos()
    elif escolha == "2":
        ticker = input("Digite o ticker (ex: VALE3): ").strip().upper()
        agente.analisar_ativo(ticker)
    elif escolha == "3":
        print("\nAte logo!")
        sys.exit(0)
    else:
        print("Opcao invalida!")
        menu()


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    if len(sys.argv) > 1:
        agente = DecisionAgent()
        ticker = sys.argv[1].upper()
        if ticker == "TODOS":
            agente.analisar_todos()
        else:
            agente.analisar_ativo(ticker)
    else:
        menu()
