#!/usr/bin/env python3
"""
Executa todas as automações de inteligência competitiva:
1. Busca de concorrentes da GA Distribuidora de Tintas
2. Monitoramento de preços SUVINIL
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from busca_concorrentes import main as busca_concorrentes
from busca_precos_suvinil import main as busca_precos

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  GA DISTRIBUIDORA DE TINTAS — AUTOMAÇÃO DE INTELIGÊNCIA COMPETITIVA")
    print("=" * 70)

    print("\n>>> ETAPA 1: Mapeamento de Concorrentes B2B em São Paulo\n")
    busca_concorrentes()

    print("\n\n>>> ETAPA 2: Monitoramento de Preços SUVINIL\n")
    busca_precos()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    print("\n" + "=" * 70)
    print("  TODAS AS AUTOMAÇÕES CONCLUÍDAS!")
    print(f"  Relatórios salvos em: {output_dir}/")
    print("    → concorrentes_ga_tintas.xlsx")
    print("    → precos_suvinil.xlsx")
    print("=" * 70)
