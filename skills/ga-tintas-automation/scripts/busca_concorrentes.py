#!/usr/bin/env python3
"""
Automação de busca de concorrentes diretos da GA Distribuidora de Tintas LTDA
Foco: Distribuidoras B2B de tintas em São Paulo capital
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Instalando openpyxl...")
    os.system("pip install openpyxl")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "concorrentes_ga_tintas.xlsx")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Base de dados de concorrentes conhecidos (pesquisa realizada em fontes públicas)
CONCORRENTES_BASE = [
    {
        "razao_social": "GAMA DISTRIBUIDORA DE TINTAS LTDA (Referência)",
        "nome_fantasia": "Gama Tintas",
        "cnpj": "07.161.840/0001-85",
        "endereco": "Estrada Vovó Carolina, 1821 – Guaianazes, São Paulo – SP, CEP 08473-370",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Demais",
        "capital_social": "R$ 145.000,00",
        "segmento": "Distribuição B2B - Tintas e acessórios para pintura",
        "marcas_trabalhadas": "Diversas marcas nacionais",
        "tipo": "REFERÊNCIA (Própria empresa)",
        "fonte": "Receita Federal / Econodata",
    },
    {
        "razao_social": "MIRAL TINTAS LTDA",
        "nome_fantasia": "Miral Distribuidora",
        "cnpj": "02.344.515/0001-34",
        "endereco": "Rua Antonio Mariano, 357 – Jardim Ipanema (Zona Sul), São Paulo – SP",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Médio",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B - Tintas Suvinil, ferramentas e acessórios",
        "marcas_trabalhadas": "Suvinil",
        "tipo": "CONCORRENTE DIRETO",
        "fonte": "miraldistribuidora.com.br",
    },
    {
        "razao_social": "B1 DISTRIBUIDORA DE TINTAS LTDA",
        "nome_fantasia": "B1 Tintas",
        "cnpj": "N/D",
        "endereco": "São Paulo – SP",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Pequeno/Médio",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B - Tintas residenciais, industriais, marítimas, automotivas",
        "marcas_trabalhadas": "Múltiplas marcas internacionais e nacionais",
        "tipo": "CONCORRENTE DIRETO",
        "fonte": "b1tintas.com.br",
    },
    {
        "razao_social": "CIA DISTRIBUIDORA DE TINTAS LTDA",
        "nome_fantasia": "CIA Distribuidora",
        "cnpj": "N/D",
        "endereco": "São Paulo – SP",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Médio",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B - Tintas, ferramentas e acessórios",
        "marcas_trabalhadas": "Coral, Tigre, Tramontina, International, Sil, Henkel",
        "tipo": "CONCORRENTE DIRETO",
        "fonte": "ciadistribuidora.com.br",
    },
    {
        "razao_social": "TINTAS MC LTDA",
        "nome_fantasia": "Tintas MC",
        "cnpj": "N/D",
        "endereco": "Diversas lojas em São Paulo – SP",
        "cnae": "47.41-5/00 - Comércio varejista de tintas e materiais para pintura",
        "porte": "Grande",
        "capital_social": "N/D",
        "segmento": "Varejo e distribuição - Maior rede de lojas de tintas do Brasil",
        "marcas_trabalhadas": "Múltiplas marcas",
        "tipo": "CONCORRENTE INDIRETO (Varejo/Atacado)",
        "fonte": "Econodata",
    },
    {
        "razao_social": "PREMA TINTAS E PRESERVAÇÃO DE MADEIRAS S.A.",
        "nome_fantasia": "Prema Tintas",
        "cnpj": "N/D",
        "endereco": "São Paulo – SP",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Grande",
        "capital_social": "N/D",
        "segmento": "Fabricação e distribuição B2B",
        "marcas_trabalhadas": "Marca própria Prema",
        "tipo": "CONCORRENTE INDIRETO (Fabricante/Distribuidor)",
        "fonte": "Econodata",
    },
    {
        "razao_social": "TINTAS JD LTDA",
        "nome_fantasia": "Tintas JD",
        "cnpj": "N/D",
        "endereco": "São Paulo – SP",
        "cnae": "47.41-5/00 - Comércio varejista de tintas",
        "porte": "Médio",
        "capital_social": "N/D",
        "segmento": "Varejo e distribuição de tintas",
        "marcas_trabalhadas": "Múltiplas marcas",
        "tipo": "CONCORRENTE INDIRETO",
        "fonte": "Econodata",
    },
    {
        "razao_social": "J E TINTAS CIA LTDA",
        "nome_fantasia": "JE Tintas",
        "cnpj": "56.932.175/0001-91",
        "endereco": "Rua Alexandre Giusti, 182 – Jardim dos Manacás, São Paulo – SP",
        "cnae": "46.74-5/00 - Comércio atacadista de cimento",
        "porte": "Médio",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B - Materiais de construção e tintas",
        "marcas_trabalhadas": "N/D",
        "tipo": "CONCORRENTE DIRETO",
        "fonte": "Econodata",
    },
    {
        "razao_social": "BIADOLA COMÉRCIO DE TINTAS EM GERAL E REPRESENTAÇÃO COMERCIAL",
        "nome_fantasia": "Biadola Tintas",
        "cnpj": "06.060.908/0001-77",
        "endereco": "São Paulo – SP",
        "cnae": "46.79-6/01 - Comércio atacadista de tintas, vernizes e similares",
        "porte": "Pequeno",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B e representação comercial de tintas",
        "marcas_trabalhadas": "N/D",
        "tipo": "CONCORRENTE DIRETO",
        "fonte": "Econodata",
    },
    {
        "razao_social": "INDÚSTRIA QUÍMICA IRAJÁ LTDA",
        "nome_fantasia": "Tintas Irajá",
        "cnpj": "60.910.023/0001-65",
        "endereco": "Rua Forte do Rio Branco, 619 – Parque São Lourenço, São Paulo – SP",
        "cnae": "20.71-1/00 - Fabricação de tintas, vernizes, esmaltes e lacas",
        "porte": "Médio/Grande",
        "capital_social": "N/D",
        "segmento": "Fabricação e distribuição B2B de tintas",
        "marcas_trabalhadas": "Marca própria Irajá",
        "tipo": "CONCORRENTE INDIRETO (Fabricante)",
        "fonte": "Econodata",
    },
    {
        "razao_social": "AGILE ATACADISTA LTDA",
        "nome_fantasia": "Agile Atacadista",
        "cnpj": "N/D",
        "endereco": "São Paulo – Zona Leste, SP",
        "cnae": "46.79-6/01 - Comércio atacadista",
        "porte": "Médio",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B - Tintas automotivas e produtos automotivos",
        "marcas_trabalhadas": "Brazilian Color e outras",
        "tipo": "CONCORRENTE DIRETO (Segmento automotivo)",
        "fonte": "agileatacadista.com.br",
    },
    {
        "razao_social": "MARTINS COMÉRCIO E SERVIÇOS DE DISTRIBUIÇÃO S.A.",
        "nome_fantasia": "Martins Atacado",
        "cnpj": "43.214.055/0001-07",
        "endereco": "Uberlândia – MG (atuação nacional incluindo SP)",
        "cnae": "46.93-1/00 - Comércio atacadista de mercadorias em geral",
        "porte": "Grande",
        "capital_social": "N/D",
        "segmento": "Distribuição B2B generalista com linha de tintas",
        "marcas_trabalhadas": "Pratik, Tekbond, Thompson, Xadrez, Condor",
        "tipo": "CONCORRENTE INDIRETO (Atacadista generalista)",
        "fonte": "martinsatacado.com.br",
    },
]


def buscar_cnpj_info(cnpj_limpo):
    """Tenta buscar informações adicionais do CNPJ via API pública."""
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def enriquecer_dados(concorrentes):
    """Enriquece dados dos concorrentes com informações de APIs públicas."""
    enriched = []
    for c in concorrentes:
        cnpj = c.get("cnpj", "N/D")
        if cnpj != "N/D":
            cnpj_limpo = re.sub(r"[^0-9]", "", cnpj)
            if len(cnpj_limpo) == 14:
                print(f"  Buscando dados de {c['razao_social']}...")
                info = buscar_cnpj_info(cnpj_limpo)
                if info:
                    c["situacao_cadastral"] = info.get("descricao_situacao_cadastral", "N/D")
                    c["data_abertura"] = info.get("data_inicio_atividade", "N/D")
                    if info.get("capital_social"):
                        c["capital_social"] = f"R$ {info['capital_social']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                time.sleep(1)  # Rate limiting
        enriched.append(c)
    return enriched


def gerar_excel(concorrentes):
    """Gera relatório Excel com dados dos concorrentes."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    wb = Workbook()

    # === ABA 1: Lista de Concorrentes ===
    ws = wb.active
    ws.title = "Concorrentes"

    # Estilos
    header_font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="1F4E79")
    ref_fill = PatternFill("solid", fgColor="E2EFDA")
    direto_fill = PatternFill("solid", fgColor="FCE4D6")
    indireto_fill = PatternFill("solid", fgColor="D6E4F0")
    title_font = Font(name="Arial", bold=True, size=14, color="1F4E79")
    subtitle_font = Font(name="Arial", italic=True, size=10, color="666666")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Título
    ws.merge_cells("A1:K1")
    ws["A1"] = "ANÁLISE DE CONCORRENTES — GA DISTRIBUIDORA DE TINTAS LTDA"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:K2")
    ws["A2"] = f"Mercado B2B de Tintas — São Paulo, SP | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center")

    # Cabeçalhos
    headers = [
        "Razão Social", "Nome Fantasia", "CNPJ", "Endereço",
        "CNAE", "Porte", "Capital Social", "Segmento",
        "Marcas Trabalhadas", "Classificação", "Fonte"
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    # Dados
    for row, c in enumerate(concorrentes, 5):
        values = [
            c.get("razao_social", ""),
            c.get("nome_fantasia", ""),
            c.get("cnpj", "N/D"),
            c.get("endereco", ""),
            c.get("cnae", ""),
            c.get("porte", "N/D"),
            c.get("capital_social", "N/D"),
            c.get("segmento", ""),
            c.get("marcas_trabalhadas", "N/D"),
            c.get("tipo", ""),
            c.get("fonte", ""),
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            tipo = c.get("tipo", "")
            if "REFERÊNCIA" in tipo:
                cell.fill = ref_fill
            elif "DIRETO" in tipo:
                cell.fill = direto_fill
            elif "INDIRETO" in tipo:
                cell.fill = indireto_fill

    # Largura das colunas
    widths = [45, 22, 22, 50, 45, 12, 18, 45, 35, 30, 25]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Filtros
    ws.auto_filter.ref = f"A4:K{4 + len(concorrentes)}"

    # === ABA 2: Resumo Analítico ===
    ws2 = wb.create_sheet("Resumo Analítico")
    ws2.merge_cells("A1:D1")
    ws2["A1"] = "RESUMO DA ANÁLISE COMPETITIVA"
    ws2["A1"].font = title_font

    diretos = [c for c in concorrentes if "DIRETO" in c.get("tipo", "") and "INDIRETO" not in c.get("tipo", "")]
    indiretos = [c for c in concorrentes if "INDIRETO" in c.get("tipo", "")]

    resumo_data = [
        ["Métrica", "Valor"],
        ["Data da Análise", datetime.now().strftime("%d/%m/%Y")],
        ["Mercado Alvo", "Distribuição B2B de Tintas - São Paulo, SP"],
        ["Empresa de Referência", "GA Distribuidora de Tintas LTDA (GAMA)"],
        ["CNPJ Referência", "07.161.840/0001-85"],
        ["Total de Concorrentes Mapeados", len(concorrentes) - 1],
        ["Concorrentes Diretos", len(diretos)],
        ["Concorrentes Indiretos", len(indiretos)],
        ["CNAE Principal do Setor", "46.79-6/01 - Comércio atacadista de tintas"],
        [""],
        ["CONCORRENTES DIRETOS (mesma atividade e região)"],
    ]
    for d in diretos:
        resumo_data.append(["  → " + d["nome_fantasia"], d.get("cnpj", "N/D")])

    resumo_data.append([""])
    resumo_data.append(["CONCORRENTES INDIRETOS (overlap parcial)"])
    for ind in indiretos:
        resumo_data.append(["  → " + ind["nome_fantasia"], ind.get("cnpj", "N/D")])

    for row, data in enumerate(resumo_data, 3):
        if isinstance(data, list) and len(data) >= 2:
            ws2.cell(row=row, column=1, value=data[0]).font = Font(name="Arial", bold=True, size=10)
            ws2.cell(row=row, column=2, value=data[1])
        elif isinstance(data, list) and len(data) == 1 and data[0]:
            ws2.cell(row=row, column=1, value=data[0]).font = Font(name="Arial", bold=True, size=11, color="1F4E79")

    ws2.column_dimensions["A"].width = 50
    ws2.column_dimensions["B"].width = 40

    # === ABA 3: Fontes de Pesquisa ===
    ws3 = wb.create_sheet("Fontes")
    ws3["A1"] = "FONTES DE PESQUISA UTILIZADAS"
    ws3["A1"].font = title_font

    fontes = [
        ["Fonte", "URL", "Tipo de Dado"],
        ["Econodata", "https://www.econodata.com.br/maiores-empresas/sp-sao-paulo/tinta", "Ranking empresas / CNPJ"],
        ["Brasil API", "https://brasilapi.com.br/", "Dados CNPJ (enriquecimento)"],
        ["Receita Federal", "https://www.gov.br/receitafederal/", "Cadastro empresarial"],
        ["Miral Distribuidora", "https://www.miraldistribuidora.com.br", "Dados comerciais"],
        ["B1 Tintas", "https://b1tintas.com.br/", "Dados comerciais"],
        ["CIA Distribuidora", "https://ciadistribuidora.com.br/", "Dados comerciais"],
        ["Arena Tintas", "https://arenatintas.com/", "Preços de referência"],
        ["Leroy Merlin", "https://www.leroymerlin.com.br/tintas/marca/Suvinil", "Preços varejo"],
        ["Telhanorte", "https://www.telhanorte.com.br/suvinil", "Preços varejo"],
        ["Mercado Livre", "https://lista.mercadolivre.com.br/tinta-suvinil-18-litros", "Preços marketplace"],
        ["Montar o Negócio", "https://montaronegocio.com/fornecedores-de-tintas/", "Lista fornecedores"],
    ]
    for row, data in enumerate(fontes, 3):
        for col, val in enumerate(data, 1):
            cell = ws3.cell(row=row, column=col, value=val)
            if row == 3:
                cell.font = header_font
                cell.fill = header_fill
            cell.border = thin_border

    ws3.column_dimensions["A"].width = 25
    ws3.column_dimensions["B"].width = 65
    ws3.column_dimensions["C"].width = 30

    wb.save(OUTPUT_FILE)
    print(f"\nRelatório salvo em: {OUTPUT_FILE}")
    return OUTPUT_FILE


def main():
    print("=" * 60)
    print("AUTOMAÇÃO: Busca de Concorrentes - GA Distribuidora de Tintas")
    print("Mercado: B2B Tintas | Região: São Paulo, SP")
    print("=" * 60)

    print("\n[1/3] Carregando base de concorrentes conhecidos...")
    concorrentes = CONCORRENTES_BASE.copy()
    print(f"  → {len(concorrentes)} empresas na base")

    print("\n[2/3] Enriquecendo dados via APIs públicas...")
    concorrentes = enriquecer_dados(concorrentes)

    print("\n[3/3] Gerando relatório Excel...")
    filepath = gerar_excel(concorrentes)

    print("\n" + "=" * 60)
    print("CONCLUÍDO!")
    print(f"  Concorrentes mapeados: {len(concorrentes)}")
    diretos = len([c for c in concorrentes if "DIRETO" in c.get("tipo", "") and "INDIRETO" not in c.get("tipo", "")])
    indiretos = len([c for c in concorrentes if "INDIRETO" in c.get("tipo", "")])
    print(f"  Diretos: {diretos} | Indiretos: {indiretos}")
    print(f"  Arquivo: {filepath}")
    print("=" * 60)


if __name__ == "__main__":
    main()
