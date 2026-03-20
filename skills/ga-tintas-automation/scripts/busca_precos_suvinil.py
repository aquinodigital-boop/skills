#!/usr/bin/env python3
"""
Automação de busca de preços de produtos SUVINIL
Coleta preços de múltiplas fontes online e gera relatório comparativo
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
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference
except ImportError:
    os.system("pip install openpyxl")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "precos_suvinil.xlsx")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# Catálogo de produtos SUVINIL com preços de referência coletados de fontes públicas
CATALOGO_SUVINIL = [
    # === LINHA STANDARD — Rende & Cobre Muito ===
    {
        "linha": "Standard",
        "produto": "Suvinil Rende & Cobre Muito Fosco",
        "tipo": "Tinta Acrílica Standard",
        "acabamento": "Fosco",
        "volume": "0.9L",
        "rendimento": "até 25 m² acabado",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Construtintas": {"preco": 39.90, "preco_original": None, "desconto": None},
            "Hipertintas": {"preco": 39.90, "preco_original": None, "desconto": "5% Pix"},
            "Arena Tintas": {"preco": 35.30, "preco_original": None, "desconto": "Pix"},
            "Magazine Luiza": {"preco": 38.90, "preco_original": None, "desconto": None},
        },
    },
    {
        "linha": "Standard",
        "produto": "Suvinil Rende & Cobre Muito Fosco",
        "tipo": "Tinta Acrílica Standard",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 100 m²/demão",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Hipertintas": {"preco": 115.90, "preco_original": None, "desconto": "5% Pix"},
            "Rei das Tintas": {"preco": 128.00, "preco_original": None, "desconto": None},
            "Casa Costa Tintas": {"preco": 89.90, "preco_original": None, "desconto": None},
            "Telhanorte": {"preco": 95.00, "preco_original": None, "desconto": None},
            "Obramax": {"preco": 79.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Standard",
        "produto": "Suvinil Rende & Cobre Muito Fosco",
        "tipo": "Tinta Acrílica Standard",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 300 m²/demão",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Mercado Livre": {"preco": 339.07, "preco_original": 423.84, "desconto": "20%"},
            "Varejão das Tintas": {"preco": 319.00, "preco_original": 354.44, "desconto": "Pix"},
            "São Geraldo Tintas": {"preco": 284.90, "preco_original": None, "desconto": None},
            "Mercado Livre (2)": {"preco": 207.28, "preco_original": 323.89, "desconto": "36%"},
            "Obramax": {"preco": 299.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Standard",
        "produto": "Suvinil Rende & Cobre Muito Fosco",
        "tipo": "Tinta Acrílica Standard",
        "acabamento": "Fosco",
        "volume": "20L",
        "rendimento": "até 189 m² acabado",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Obramax": {"preco": 329.90, "preco_original": None, "desconto": "Atacado/Varejo"},
            "Mercado Livre": {"preco": 391.69, "preco_original": None, "desconto": None},
        },
    },
    # === LINHA STANDARD — Tetos ===
    {
        "linha": "Standard",
        "produto": "Suvinil Tetos Acrílica Fosca",
        "tipo": "Tinta Acrílica Standard para Tetos",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 23 m² acabado",
        "aplicacao": "Interno e Externo coberto",
        "precos": {
            "Obramax": {"preco": 69.90, "preco_original": None, "desconto": "Atacado/Varejo"},
            "Telhanorte": {"preco": 79.90, "preco_original": None, "desconto": None},
        },
    },
    # === LINHA PREMIUM — Toque Fosco Completo ===
    {
        "linha": "Premium",
        "produto": "Suvinil Toque Fosco Completo",
        "tipo": "Tinta Acrílica Premium",
        "acabamento": "Fosco",
        "volume": "0.9L",
        "rendimento": "até 15 m² acabado",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Hipertintas": {"preco": 47.90, "preco_original": None, "desconto": None},
        },
    },
    {
        "linha": "Premium",
        "produto": "Suvinil Toque Fosco Completo",
        "tipo": "Tinta Acrílica Premium",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 30 m² acabado",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Hipertintas": {"preco": 139.90, "preco_original": None, "desconto": "Branco Neve"},
            "Hipertintas (Areia)": {"preco": 185.90, "preco_original": None, "desconto": None},
            "Telhanorte": {"preco": 109.90, "preco_original": None, "desconto": None},
            "Bela Tintas": {"preco": 115.00, "preco_original": None, "desconto": None},
            "Obramax": {"preco": 99.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Premium",
        "produto": "Suvinil Toque Fosco Completo",
        "tipo": "Tinta Acrílica Premium",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 380 m²/demão",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Mercado Livre": {"preco": 358.80, "preco_original": 478.40, "desconto": "25%"},
            "Telhanorte": {"preco": 419.90, "preco_original": None, "desconto": None},
            "Arena Tintas": {"preco": 399.00, "preco_original": None, "desconto": "Pix"},
            "Obramax": {"preco": 389.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Premium",
        "produto": "Suvinil Toque Fosco Completo",
        "tipo": "Tinta Acrílica Premium",
        "acabamento": "Fosco",
        "volume": "20L",
        "rendimento": "até 167 m² acabado",
        "aplicacao": "Interno e Externo",
        "precos": {
            "Obramax": {"preco": 449.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    # === LINHA SELECT (ALTO PADRÃO) ===
    {
        "linha": "Select",
        "produto": "Suvinil Toque Fosco Select",
        "tipo": "Tinta Acrílica Alto Padrão",
        "acabamento": "Fosco Aveludado",
        "volume": "18L",
        "rendimento": "até 350 m²/demão",
        "aplicacao": "Interno",
        "precos": {
            "Mercado Livre": {"preco": 759.73, "preco_original": 799.72, "desconto": "5%"},
            "Mercado Livre (2)": {"preco": 414.76, "preco_original": 524.94, "desconto": "21%"},
            "Arena Tintas": {"preco": 689.00, "preco_original": None, "desconto": None},
        },
    },
    # === ESMALTES ===
    {
        "linha": "Esmaltes",
        "produto": "Suvinil Esmalte Cor & Proteção Base Água Acetinado",
        "tipo": "Esmalte Base Água",
        "acabamento": "Acetinado",
        "volume": "3.6L",
        "rendimento": "até 60 m²/demão",
        "aplicacao": "Interno e Externo (metal e madeira)",
        "precos": {
            "Arena Tintas": {"preco": 265.16, "preco_original": 294.62, "desconto": "Pix"},
            "Leroy Merlin": {"preco": 289.90, "preco_original": None, "desconto": None},
        },
    },
    {
        "linha": "Esmaltes",
        "produto": "Suvinil Esmalte Cor & Proteção Grafite Fosco",
        "tipo": "Esmalte Anticorrosivo",
        "acabamento": "Grafite Fosco",
        "volume": "3.6L",
        "rendimento": "até 50 m²/demão",
        "aplicacao": "Metal (aplica direto na ferrugem)",
        "precos": {
            "Arena Tintas": {"preco": 308.09, "preco_original": None, "desconto": None},
        },
    },
    # === EPÓXI ===
    {
        "linha": "Especiais",
        "produto": "Suvinil Epóxi",
        "tipo": "Tinta Epóxi",
        "acabamento": "Brilhante",
        "volume": "3.6L",
        "rendimento": "até 45 m²/demão",
        "aplicacao": "Garagens, áreas industriais, cozinhas",
        "precos": {
            "Arena Tintas": {"preco": 327.97, "preco_original": None, "desconto": None},
            "Leroy Merlin": {"preco": 349.90, "preco_original": None, "desconto": None},
        },
    },
    # === ECONÔMICA — Glasu ===
    {
        "linha": "Econômica",
        "produto": "Suvinil Glasu Econômica",
        "tipo": "Tinta Acrílica Econômica",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 20 m² acabado",
        "aplicacao": "Interno",
        "precos": {
            "Obramax": {"preco": 52.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Econômica",
        "produto": "Suvinil Glasu Econômica",
        "tipo": "Tinta Acrílica Econômica",
        "acabamento": "Fosco",
        "volume": "20L",
        "rendimento": "até 200 m²/demão",
        "aplicacao": "Interno",
        "precos": {
            "Obramax": {"preco": 199.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    # === ECONÔMICA — Látex Maxx ===
    {
        "linha": "Econômica",
        "produto": "Suvinil Látex Maxx",
        "tipo": "Tinta Látex Econômica",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 56 m²/demão",
        "aplicacao": "Interno",
        "precos": {
            "Bela Tintas": {"preco": 49.90, "preco_original": None, "desconto": None},
        },
    },
    {
        "linha": "Econômica",
        "produto": "Suvinil Látex Maxx",
        "tipo": "Tinta Látex Econômica",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 280 m²/demão",
        "aplicacao": "Interno",
        "precos": {
            "Bela Tintas": {"preco": 189.90, "preco_original": None, "desconto": None},
            "Mercado Livre": {"preco": 169.90, "preco_original": None, "desconto": None},
        },
    },
    # === ECONÔMICA — Gesso & Drywall ===
    {
        "linha": "Econômica",
        "produto": "Suvinil Gesso & Drywall",
        "tipo": "Tinta Acrílica Econômica para Gesso",
        "acabamento": "Fosco",
        "volume": "3.6L",
        "rendimento": "até 24 m² acabado",
        "aplicacao": "Interno (gesso e drywall)",
        "precos": {
            "Obramax": {"preco": 45.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    {
        "linha": "Econômica",
        "produto": "Suvinil Gesso & Drywall",
        "tipo": "Tinta Acrílica Econômica para Gesso",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 180 m²/demão",
        "aplicacao": "Interno (gesso e drywall)",
        "precos": {
            "Obramax": {"preco": 159.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    # === TINTA PARA PISO ===
    {
        "linha": "Pisos",
        "produto": "Suvinil Piso Acrílica",
        "tipo": "Tinta Acrílica para Pisos",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 250 m²/demão",
        "aplicacao": "Pisos de concreto, cimento, cerâmicos",
        "precos": {
            "Leroy Merlin": {"preco": 339.90, "preco_original": None, "desconto": None},
            "Obramax": {"preco": 329.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    # === PREPARAÇÃO ===
    {
        "linha": "Preparação",
        "produto": "Suvinil Fundo Preparador de Parede",
        "tipo": "Fundo Preparador",
        "acabamento": "Transparente",
        "volume": "3.6L",
        "rendimento": "até 55 m²/demão",
        "aplicacao": "Interno e Externo (preparação de superfície)",
        "precos": {
            "Obramax": {"preco": 59.90, "preco_original": None, "desconto": "Atacado/Varejo"},
        },
    },
    # === INOVA ===
    {
        "linha": "Premium",
        "produto": "Suvinil Inova Fosco Sempre Limpo",
        "tipo": "Tinta Acrílica Premium Anti-Mancha",
        "acabamento": "Fosco",
        "volume": "18L",
        "rendimento": "até 350 m²/demão",
        "aplicacao": "Interno e Externo (lavável)",
        "precos": {
            "Arena Tintas": {"preco": 499.00, "preco_original": None, "desconto": None},
            "Leroy Merlin": {"preco": 529.90, "preco_original": None, "desconto": None},
        },
    },
]


def scrape_precos_online():
    """Tenta coletar preços atualizados de fontes online."""
    precos_atualizados = []

    # Tentativa de scraping em sites que permitem
    fontes_urls = [
        ("Varejão das Tintas", "https://loja.varejaodastintas.com.br/marca/suvinil.html"),
        ("Tintomax", "https://www.tintomax.com.br/suvinil"),
        ("Obramax", "https://www.obramax.com.br/suvinil"),
        ("Cofema Atacadista", "https://www.cofema.com.br/"),
        ("Eletroleste", "https://www.eletroleste.com.br/"),
    ]

    for nome_fonte, url in fontes_urls:
        try:
            print(f"  Tentando coletar de {nome_fonte}...")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Procura por padrões de preço
                price_patterns = soup.find_all(string=re.compile(r"R\$\s*[\d.,]+"))
                product_names = soup.find_all(["h2", "h3", "span"], class_=re.compile(r"product|nome|title", re.I))
                if price_patterns:
                    print(f"    → Encontrados {len(price_patterns)} preços em {nome_fonte}")
                    for i, price_text in enumerate(price_patterns[:10]):
                        match = re.search(r"R\$\s*([\d.,]+)", price_text)
                        if match:
                            preco_str = match.group(1).replace(".", "").replace(",", ".")
                            try:
                                preco = float(preco_str)
                                precos_atualizados.append({
                                    "fonte": nome_fonte,
                                    "preco_texto": price_text.strip(),
                                    "preco": preco,
                                })
                            except ValueError:
                                pass
            else:
                print(f"    → {nome_fonte}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"    → Erro ao acessar {nome_fonte}: {str(e)[:50]}")
        time.sleep(1)

    return precos_atualizados


def gerar_excel(catalogo, precos_extras=None):
    """Gera relatório Excel detalhado de preços SUVINIL."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    wb = Workbook()

    # Estilos
    header_font = Font(name="Arial", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="C00000")
    title_font = Font(name="Arial", bold=True, size=14, color="C00000")
    subtitle_font = Font(name="Arial", italic=True, size=10, color="666666")
    money_format = 'R$ #,##0.00'
    pct_format = '0%'
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    standard_fill = PatternFill("solid", fgColor="E2EFDA")
    premium_fill = PatternFill("solid", fgColor="FCE4D6")
    select_fill = PatternFill("solid", fgColor="D6E4F0")
    esmalte_fill = PatternFill("solid", fgColor="F2DCDB")
    economica_fill = PatternFill("solid", fgColor="EBF1DE")

    fills_by_linha = {
        "Standard": standard_fill,
        "Premium": premium_fill,
        "Select": select_fill,
        "Esmaltes": esmalte_fill,
        "Especiais": esmalte_fill,
        "Econômica": economica_fill,
        "Pisos": standard_fill,
    }

    # === ABA 1: Catálogo Completo ===
    ws = wb.active
    ws.title = "Catálogo de Preços"

    ws.merge_cells("A1:J1")
    ws["A1"] = "MONITORAMENTO DE PREÇOS — PRODUTOS SUVINIL"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:J2")
    ws["A2"] = f"Pesquisa de mercado | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center")

    headers = [
        "Linha", "Produto", "Tipo", "Acabamento", "Volume",
        "Rendimento", "Aplicação", "Loja/Fonte", "Preço (R$)", "Preço Original (R$)"
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    row = 5
    for prod in catalogo:
        for loja, info in prod["precos"].items():
            values = [
                prod["linha"], prod["produto"], prod["tipo"],
                prod["acabamento"], prod["volume"], prod["rendimento"],
                prod["aplicacao"], loja, info["preco"],
                info.get("preco_original"),
            ]
            fill = fills_by_linha.get(prod["linha"], None)
            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = thin_border
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if fill:
                    cell.fill = fill
                if col in (9, 10) and val is not None:
                    cell.number_format = money_format
            row += 1

    widths = [14, 40, 30, 18, 8, 20, 35, 22, 16, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.auto_filter.ref = f"A4:J{row - 1}"

    # === ABA 2: Comparativo por Produto ===
    ws2 = wb.create_sheet("Comparativo")

    ws2.merge_cells("A1:G1")
    ws2["A1"] = "COMPARATIVO DE PREÇOS POR PRODUTO"
    ws2["A1"].font = title_font
    ws2["A1"].alignment = Alignment(horizontal="center")

    comp_headers = ["Produto", "Volume", "Menor Preço", "Maior Preço", "Preço Médio", "Variação (%)", "Melhor Loja"]
    for col, h in enumerate(comp_headers, 1):
        cell = ws2.cell(row=3, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    row2 = 4
    for prod in catalogo:
        precos = [info["preco"] for info in prod["precos"].values()]
        if not precos:
            continue
        menor = min(precos)
        maior = max(precos)
        media = sum(precos) / len(precos)
        variacao = (maior - menor) / menor if menor > 0 else 0
        melhor_loja = min(prod["precos"].items(), key=lambda x: x[1]["preco"])[0]

        values = [prod["produto"], prod["volume"], menor, maior, media, variacao, melhor_loja]
        fill = fills_by_linha.get(prod["linha"], None)
        for col, val in enumerate(values, 1):
            cell = ws2.cell(row=row2, column=col, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(wrap_text=True)
            if fill:
                cell.fill = fill
            if col in (3, 4, 5):
                cell.number_format = money_format
            if col == 6:
                cell.number_format = '0.0%'
        row2 += 1

    ws2.column_dimensions["A"].width = 40
    ws2.column_dimensions["B"].width = 10
    ws2.column_dimensions["C"].width = 16
    ws2.column_dimensions["D"].width = 16
    ws2.column_dimensions["E"].width = 16
    ws2.column_dimensions["F"].width = 14
    ws2.column_dimensions["G"].width = 25

    # Gráfico comparativo
    if row2 > 4:
        chart = BarChart()
        chart.type = "col"
        chart.title = "Comparativo de Preços SUVINIL (Menor vs Maior)"
        chart.y_axis.title = "Preço (R$)"
        chart.x_axis.title = "Produto"
        chart.style = 10

        data_ref = Reference(ws2, min_col=3, min_row=3, max_col=4, max_row=row2 - 1)
        cats = Reference(ws2, min_col=1, min_row=4, max_row=row2 - 1)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats)
        chart.shape = 4
        chart.width = 28
        chart.height = 16
        ws2.add_chart(chart, f"A{row2 + 2}")

    # === ABA 3: Tabela de Preços para Distribuidor ===
    ws3 = wb.create_sheet("Referência Distribuidor")

    ws3.merge_cells("A1:F1")
    ws3["A1"] = "TABELA DE REFERÊNCIA PARA DISTRIBUIDOR B2B"
    ws3["A1"].font = title_font
    ws3["A1"].alignment = Alignment(horizontal="center")

    ws3.merge_cells("A2:F2")
    ws3["A2"] = "Estimativa de margens baseada em preços de varejo (referência de mercado)"
    ws3["A2"].font = subtitle_font
    ws3["A2"].alignment = Alignment(horizontal="center")

    dist_headers = ["Produto", "Volume", "Preço Médio Varejo", "Estimativa Preço Distribuidor (-25%)", "Estimativa Preço Fábrica (-40%)", "Margem Estimada Distribuidor"]
    for col, h in enumerate(dist_headers, 1):
        cell = ws3.cell(row=4, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    row3 = 5
    for prod in catalogo:
        precos = [info["preco"] for info in prod["precos"].values()]
        if not precos:
            continue
        media = sum(precos) / len(precos)

        ws3.cell(row=row3, column=1, value=prod["produto"]).border = thin_border
        ws3.cell(row=row3, column=2, value=prod["volume"]).border = thin_border

        # Preço médio varejo
        cell_media = ws3.cell(row=row3, column=3, value=media)
        cell_media.number_format = money_format
        cell_media.border = thin_border

        # Preço distribuidor (fórmula: -25% do varejo)
        cell_dist = ws3.cell(row=row3, column=4)
        cell_dist.value = f"=C{row3}*0.75"
        cell_dist.number_format = money_format
        cell_dist.border = thin_border

        # Preço fábrica (fórmula: -40% do varejo)
        cell_fab = ws3.cell(row=row3, column=5)
        cell_fab.value = f"=C{row3}*0.60"
        cell_fab.number_format = money_format
        cell_fab.border = thin_border

        # Margem distribuidor (fórmula)
        cell_margem = ws3.cell(row=row3, column=6)
        cell_margem.value = f"=(D{row3}-E{row3})/D{row3}"
        cell_margem.number_format = '0.0%'
        cell_margem.border = thin_border

        fill = fills_by_linha.get(prod["linha"], None)
        if fill:
            for c in range(1, 7):
                ws3.cell(row=row3, column=c).fill = fill

        row3 += 1

    # Disclaimer
    ws3.cell(row=row3 + 2, column=1, value="AVISO: Os preços estimados de distribuidor e fábrica são aproximações baseadas em margens típicas do setor.").font = Font(italic=True, color="FF0000", size=9)
    ws3.cell(row=row3 + 3, column=1, value="Margens reais variam conforme volume, negociação e política comercial de cada fabricante.").font = Font(italic=True, color="FF0000", size=9)

    ws3.column_dimensions["A"].width = 40
    ws3.column_dimensions["B"].width = 10
    ws3.column_dimensions["C"].width = 22
    ws3.column_dimensions["D"].width = 32
    ws3.column_dimensions["E"].width = 32
    ws3.column_dimensions["F"].width = 28

    # === ABA 4: Fontes ===
    ws4 = wb.create_sheet("Fontes")
    ws4["A1"] = "FONTES DE PREÇOS CONSULTADAS"
    ws4["A1"].font = title_font

    fontes = [
        ["Fonte", "URL", "Tipo"],
        ["Loja Suvinil (Oficial)", "https://loja.suvinil.com.br/", "E-commerce oficial"],
        ["Arena Tintas", "https://arenatintas.com/suvinil", "Varejo online"],
        ["Bela Tintas", "https://www.belatintas.com.br/suvinil", "Varejo online"],
        ["Leroy Merlin", "https://www.leroymerlin.com.br/tintas/marca/Suvinil", "Home center"],
        ["Telhanorte", "https://www.telhanorte.com.br/suvinil", "Home center"],
        ["Mercado Livre", "https://lista.mercadolivre.com.br/tinta-suvinil-18-litros", "Marketplace"],
        ["Varejão das Tintas", "https://loja.varejaodastintas.com.br/marca/suvinil.html", "Varejo online"],
        ["Casa Costa Tintas", "https://www.casacostatintas.com.br/", "Varejo online"],
        ["Hipertintas", "https://www.hipertintas.com.br/tintas/parede/suvinil/18", "Varejo online"],
        ["Buscapé", "https://www.buscape.com.br/busca/tinta+suvinil+18+litros", "Comparador de preços"],
        ["Obramax", "https://www.obramax.com.br/suvinil", "Home center atacado/varejo"],
        ["Cofema Atacadista", "https://www.cofema.com.br/", "Atacadista materiais construção"],
        ["Eletroleste", "https://www.eletroleste.com.br/", "Atacadista materiais construção"],
        ["Ismafer", "https://www.ismafer.com.br/", "Varejo ferragens e ferramentas"],
    ]
    for row, data in enumerate(fontes, 3):
        for col, val in enumerate(data, 1):
            cell = ws4.cell(row=row, column=col, value=val)
            if row == 3:
                cell.font = header_font
                cell.fill = header_fill
            cell.border = thin_border

    ws4.column_dimensions["A"].width = 30
    ws4.column_dimensions["B"].width = 65
    ws4.column_dimensions["C"].width = 25

    wb.save(OUTPUT_FILE)
    print(f"\nRelatório salvo em: {OUTPUT_FILE}")
    return OUTPUT_FILE


def main():
    print("=" * 60)
    print("AUTOMAÇÃO: Monitoramento de Preços - Produtos SUVINIL")
    print("=" * 60)

    print("\n[1/3] Carregando catálogo de produtos SUVINIL...")
    catalogo = CATALOGO_SUVINIL.copy()
    total_produtos = len(catalogo)
    total_precos = sum(len(p["precos"]) for p in catalogo)
    print(f"  → {total_produtos} produtos | {total_precos} pontos de preço")

    print("\n[2/3] Buscando preços atualizados online...")
    precos_extras = scrape_precos_online()
    if precos_extras:
        print(f"  → {len(precos_extras)} preços adicionais coletados")

    print("\n[3/3] Gerando relatório Excel...")
    filepath = gerar_excel(catalogo, precos_extras)

    print("\n" + "=" * 60)
    print("CONCLUÍDO!")
    print(f"  Produtos monitorados: {total_produtos}")
    print(f"  Pontos de preço: {total_precos}")
    print(f"  Arquivo: {filepath}")
    print("=" * 60)

    # Resumo rápido
    print("\n--- RESUMO DE PREÇOS ---")
    for prod in catalogo:
        precos = [info["preco"] for info in prod["precos"].values()]
        if precos:
            print(f"  {prod['produto']} ({prod['volume']}): R$ {min(precos):.2f} ~ R$ {max(precos):.2f}")


if __name__ == "__main__":
    main()
