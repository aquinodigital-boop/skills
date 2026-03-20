---
name: ga-tintas-automation
description: "Automação de pesquisa de concorrentes da GA Distribuidora de Tintas LTDA (São Paulo, B2B) e monitoramento de preços de produtos SUVINIL. Use esta skill para gerar relatórios de inteligência competitiva e acompanhamento de preços no mercado de tintas."
---

# GA Distribuidora de Tintas - Automação de Inteligência Competitiva

## Funcionalidades

### 1. Pesquisa de Concorrentes (B2B - São Paulo)
- Busca distribuidoras de tintas concorrentes diretas em São Paulo
- Coleta CNPJ, razão social, endereço, CNAE e porte
- Gera relatório Excel com análise competitiva

### 2. Monitoramento de Preços SUVINIL
- Busca preços de venda de produtos SUVINIL em múltiplas fontes
- Compara preços entre varejistas online
- Gera relatório Excel com tabela de preços e análise

## Como Usar

```bash
# Executar pesquisa de concorrentes
python scripts/busca_concorrentes.py

# Executar pesquisa de preços SUVINIL
python scripts/busca_precos_suvinil.py

# Executar ambos
python scripts/run_all.py
```

## Saídas
- `output/concorrentes_ga_tintas.xlsx` — Relatório de concorrentes
- `output/precos_suvinil.xlsx` — Relatório de preços SUVINIL
