#!/usr/bin/env python3
"""
Gera um dashboard HTML interativo com os dados de concorrentes e preços SUVINIL.
"""

import os
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "output")
DASHBOARD_FILE = os.path.join(OUTPUT_DIR, "dashboard.html")

# Importa dados dos outros scripts
import sys
sys.path.insert(0, SCRIPT_DIR)
from busca_concorrentes import CONCORRENTES_BASE
from busca_precos_suvinil import CATALOGO_SUVINIL


def build_dashboard():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Prepara dados de concorrentes
    concorrentes_diretos = [c for c in CONCORRENTES_BASE if "DIRETO" in c.get("tipo", "") and "INDIRETO" not in c.get("tipo", "") and "REFERÊNCIA" not in c.get("tipo", "")]
    concorrentes_indiretos = [c for c in CONCORRENTES_BASE if "INDIRETO" in c.get("tipo", "")]
    referencia = [c for c in CONCORRENTES_BASE if "REFERÊNCIA" in c.get("tipo", "")]

    # Prepara dados de preços agrupados por produto+volume
    produtos_precos = []
    for p in CATALOGO_SUVINIL:
        precos_list = [info["preco"] for info in p["precos"].values()]
        lojas = list(p["precos"].keys())
        produtos_precos.append({
            "linha": p["linha"],
            "produto": p["produto"],
            "volume": p["volume"],
            "rendimento": p["rendimento"],
            "aplicacao": p["aplicacao"],
            "menor": min(precos_list),
            "maior": max(precos_list),
            "media": round(sum(precos_list) / len(precos_list), 2),
            "num_lojas": len(precos_list),
            "melhor_loja": min(p["precos"].items(), key=lambda x: x[1]["preco"])[0],
            "precos_detalhe": {loja: info["preco"] for loja, info in p["precos"].items()},
        })

    # Agrupa por produto (sem volume) para gráfico comparativo
    produtos_unicos = {}
    for p in produtos_precos:
        key = p["produto"]
        if key not in produtos_unicos:
            produtos_unicos[key] = {"linha": p["linha"], "volumes": []}
        produtos_unicos[key]["volumes"].append(p)

    # Todas as lojas
    todas_lojas = set()
    for p in CATALOGO_SUVINIL:
        todas_lojas.update(p["precos"].keys())
    todas_lojas = sorted(todas_lojas)

    # Dados para gráficos (JSON)
    chart_produtos_18l = [p for p in produtos_precos if p["volume"] == "18L"]
    chart_produtos_36l = [p for p in produtos_precos if p["volume"] == "3.6L"]

    data_json = json.dumps({
        "concorrentes": {
            "diretos": len(concorrentes_diretos),
            "indiretos": len(concorrentes_indiretos),
            "total": len(CONCORRENTES_BASE) - len(referencia),
        },
        "precos_18l": [{"nome": p["produto"].replace("Suvinil ", ""), "menor": p["menor"], "maior": p["maior"], "media": p["media"]} for p in chart_produtos_18l],
        "precos_36l": [{"nome": p["produto"].replace("Suvinil ", ""), "menor": p["menor"], "maior": p["maior"], "media": p["media"]} for p in chart_produtos_36l],
        "por_loja": {loja: sum(1 for p in CATALOGO_SUVINIL if loja in p["precos"]) for loja in todas_lojas},
    }, ensure_ascii=False)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Gera tabela de concorrentes
    conc_rows = ""
    for c in CONCORRENTES_BASE:
        tipo = c.get("tipo", "")
        if "REFERÊNCIA" in tipo:
            badge_class = "badge-ref"
            badge_text = "Referência"
        elif "INDIRETO" in tipo:
            badge_class = "badge-indireto"
            badge_text = "Indireto"
        else:
            badge_class = "badge-direto"
            badge_text = "Direto"

        conc_rows += f"""<tr>
            <td><strong>{c['nome_fantasia']}</strong><br><small style="color:#888">{c['razao_social']}</small></td>
            <td>{c.get('cnpj','N/D')}</td>
            <td>{c.get('endereco','N/D')}</td>
            <td><span class="badge {badge_class}">{badge_text}</span></td>
            <td>{c.get('segmento','')}</td>
            <td>{c.get('marcas_trabalhadas','N/D')}</td>
        </tr>"""

    # Gera tabela de preços
    preco_rows = ""
    linha_colors = {
        "Standard": "#e8f5e9",
        "Premium": "#fff3e0",
        "Select": "#e3f2fd",
        "Esmaltes": "#fce4ec",
        "Especiais": "#fce4ec",
        "Econômica": "#f1f8e9",
        "Pisos": "#e0f7fa",
        "Preparação": "#f3e5f5",
    }
    for p in produtos_precos:
        bg = linha_colors.get(p["linha"], "#fff")
        variacao = ((p["maior"] - p["menor"]) / p["menor"] * 100) if p["menor"] > 0 and p["maior"] != p["menor"] else 0
        var_color = "#e53935" if variacao > 30 else "#ff9800" if variacao > 15 else "#4caf50"

        lojas_detail = ", ".join([f"{loja}: R$ {preco:.2f}" for loja, preco in p["precos_detalhe"].items()])

        preco_rows += f"""<tr style="background:{bg}">
            <td><span class="badge-linha">{p['linha']}</span></td>
            <td><strong>{p['produto']}</strong></td>
            <td class="center">{p['volume']}</td>
            <td class="money">R$ {p['menor']:.2f}</td>
            <td class="money">R$ {p['maior']:.2f}</td>
            <td class="money">R$ {p['media']:.2f}</td>
            <td class="center" style="color:{var_color};font-weight:bold">{variacao:.0f}%</td>
            <td>{p['melhor_loja']}</td>
            <td><small>{lojas_detail}</small></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — GA Distribuidora de Tintas</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif; background:#f0f2f5; color:#1a1a2e; }}
.header {{ background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%); color:#fff; padding:24px 32px; }}
.header h1 {{ font-size:24px; font-weight:700; }}
.header p {{ opacity:.7; margin-top:4px; font-size:14px; }}
.container {{ max-width:1400px; margin:0 auto; padding:20px; }}

/* KPI Cards */
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }}
.kpi-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.06); text-align:center; }}
.kpi-card .number {{ font-size:36px; font-weight:800; color:#0f3460; }}
.kpi-card .label {{ font-size:13px; color:#666; margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }}
.kpi-card.green .number {{ color:#2e7d32; }}
.kpi-card.orange .number {{ color:#e65100; }}
.kpi-card.blue .number {{ color:#1565c0; }}
.kpi-card.red .number {{ color:#c62828; }}

/* Sections */
.section {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:24px; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.section h2 {{ font-size:18px; font-weight:700; color:#1a1a2e; margin-bottom:16px; padding-bottom:8px; border-bottom:2px solid #e0e0e0; }}

/* Tables */
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:#1a1a2e; color:#fff; padding:10px 12px; text-align:left; font-weight:600; position:sticky; top:0; }}
td {{ padding:8px 12px; border-bottom:1px solid #eee; vertical-align:top; }}
tr:hover {{ background:#f5f5f5 !important; }}
.money {{ text-align:right; font-family:'Courier New',monospace; font-weight:600; }}
.center {{ text-align:center; }}

/* Badges */
.badge {{ padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
.badge-direto {{ background:#ffebee; color:#c62828; }}
.badge-indireto {{ background:#e3f2fd; color:#1565c0; }}
.badge-ref {{ background:#e8f5e9; color:#2e7d32; }}
.badge-linha {{ background:#f3e5f5; color:#6a1b9a; padding:2px 8px; border-radius:8px; font-size:11px; font-weight:600; }}

/* Charts */
.chart-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px; }}
.chart-container {{ position:relative; height:350px; }}
@media(max-width:900px) {{ .chart-grid {{ grid-template-columns:1fr; }} }}

/* Tabs */
.tabs {{ display:flex; gap:4px; margin-bottom:16px; }}
.tab {{ padding:8px 20px; border:none; background:#e0e0e0; color:#666; border-radius:8px 8px 0 0; cursor:pointer; font-size:14px; font-weight:600; }}
.tab.active {{ background:#1a1a2e; color:#fff; }}
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}

/* Search */
.search {{ padding:8px 16px; border:1px solid #ddd; border-radius:8px; width:300px; font-size:14px; margin-bottom:12px; }}
.search:focus {{ outline:none; border-color:#0f3460; box-shadow:0 0 0 3px rgba(15,52,96,.1); }}

/* Scroll */
.table-scroll {{ max-height:500px; overflow-y:auto; border-radius:8px; border:1px solid #e0e0e0; }}

/* Footer */
.footer {{ text-align:center; padding:20px; color:#999; font-size:12px; }}
</style>
</head>
<body>

<div class="header">
    <h1>GA Distribuidora de Tintas LTDA</h1>
    <p>Dashboard de Inteligencia Competitiva — Mercado B2B Tintas Sao Paulo | Atualizado em {now}</p>
</div>

<div class="container">

<!-- KPI Cards -->
<div class="kpi-grid">
    <div class="kpi-card blue">
        <div class="number">{len(CONCORRENTES_BASE) - len(referencia)}</div>
        <div class="label">Concorrentes Mapeados</div>
    </div>
    <div class="kpi-card red">
        <div class="number">{len(concorrentes_diretos)}</div>
        <div class="label">Concorrentes Diretos</div>
    </div>
    <div class="kpi-card orange">
        <div class="number">{len(concorrentes_indiretos)}</div>
        <div class="label">Concorrentes Indiretos</div>
    </div>
    <div class="kpi-card green">
        <div class="number">{len(CATALOGO_SUVINIL)}</div>
        <div class="label">Produtos Monitorados</div>
    </div>
    <div class="kpi-card">
        <div class="number">{sum(len(p['precos']) for p in CATALOGO_SUVINIL)}</div>
        <div class="label">Pontos de Preco</div>
    </div>
    <div class="kpi-card">
        <div class="number">{len(todas_lojas)}</div>
        <div class="label">Fontes de Preco</div>
    </div>
</div>

<!-- Charts -->
<div class="section">
    <h2>Comparativo de Precos SUVINIL</h2>
    <div class="chart-grid">
        <div>
            <h3 style="text-align:center;margin-bottom:8px;color:#666;font-size:14px">Latas 18L — Faixa de Preco</h3>
            <div class="chart-container"><canvas id="chart18L"></canvas></div>
        </div>
        <div>
            <h3 style="text-align:center;margin-bottom:8px;color:#666;font-size:14px">Galoes 3.6L — Faixa de Preco</h3>
            <div class="chart-container"><canvas id="chart36L"></canvas></div>
        </div>
    </div>
    <div class="chart-grid">
        <div>
            <h3 style="text-align:center;margin-bottom:8px;color:#666;font-size:14px">Distribuicao por Tipo de Concorrente</h3>
            <div class="chart-container"><canvas id="chartConc"></canvas></div>
        </div>
        <div>
            <h3 style="text-align:center;margin-bottom:8px;color:#666;font-size:14px">Produtos por Fonte de Preco</h3>
            <div class="chart-container"><canvas id="chartLojas"></canvas></div>
        </div>
    </div>
</div>

<!-- Tabs -->
<div class="section">
    <div class="tabs">
        <button class="tab active" onclick="showTab('tab-precos',this)">Precos SUVINIL</button>
        <button class="tab" onclick="showTab('tab-concorrentes',this)">Concorrentes</button>
    </div>

    <div id="tab-precos" class="tab-content active">
        <input type="text" class="search" id="searchPrecos" placeholder="Buscar produto, linha, loja..." oninput="filterTable('tblPrecos','searchPrecos')">
        <div class="table-scroll">
        <table id="tblPrecos">
            <thead>
                <tr>
                    <th>Linha</th>
                    <th>Produto</th>
                    <th>Volume</th>
                    <th>Menor Preco</th>
                    <th>Maior Preco</th>
                    <th>Preco Medio</th>
                    <th>Variacao</th>
                    <th>Melhor Loja</th>
                    <th>Detalhes</th>
                </tr>
            </thead>
            <tbody>
                {preco_rows}
            </tbody>
        </table>
        </div>
    </div>

    <div id="tab-concorrentes" class="tab-content">
        <input type="text" class="search" id="searchConc" placeholder="Buscar empresa, CNPJ, segmento..." oninput="filterTable('tblConc','searchConc')">
        <div class="table-scroll">
        <table id="tblConc">
            <thead>
                <tr>
                    <th>Empresa</th>
                    <th>CNPJ</th>
                    <th>Endereco</th>
                    <th>Tipo</th>
                    <th>Segmento</th>
                    <th>Marcas</th>
                </tr>
            </thead>
            <tbody>
                {conc_rows}
            </tbody>
        </table>
        </div>
    </div>
</div>

</div>

<div class="footer">
    GA Distribuidora de Tintas LTDA — Dashboard de Inteligencia Competitiva — Gerado automaticamente em {now}
</div>

<script>
const DATA = {data_json};

// Tabs
function showTab(id, btn) {{
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
}}

// Search
function filterTable(tableId, inputId) {{
    const q = document.getElementById(inputId).value.toLowerCase();
    const rows = document.getElementById(tableId).querySelectorAll('tbody tr');
    rows.forEach(r => {{
        r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    }});
}}

// Charts
const colors = {{
    blue: 'rgba(21,101,192,0.7)',
    red: 'rgba(198,40,40,0.7)',
    green: 'rgba(46,125,50,0.7)',
    orange: 'rgba(230,81,0,0.7)',
    purple: 'rgba(106,27,154,0.7)',
    teal: 'rgba(0,137,123,0.7)',
}};

// 18L Chart
if (DATA.precos_18l.length) {{
    new Chart(document.getElementById('chart18L'), {{
        type: 'bar',
        data: {{
            labels: DATA.precos_18l.map(p => p.nome),
            datasets: [
                {{ label: 'Menor', data: DATA.precos_18l.map(p => p.menor), backgroundColor: colors.green }},
                {{ label: 'Medio', data: DATA.precos_18l.map(p => p.media), backgroundColor: colors.blue }},
                {{ label: 'Maior', data: DATA.precos_18l.map(p => p.maior), backgroundColor: colors.red }},
            ]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }},
            scales: {{ y: {{ beginAtZero: true, ticks: {{ callback: v => 'R$ ' + v }} }},
                       x: {{ ticks: {{ maxRotation: 45 }} }} }}
        }}
    }});
}}

// 3.6L Chart
if (DATA.precos_36l.length) {{
    new Chart(document.getElementById('chart36L'), {{
        type: 'bar',
        data: {{
            labels: DATA.precos_36l.map(p => p.nome),
            datasets: [
                {{ label: 'Menor', data: DATA.precos_36l.map(p => p.menor), backgroundColor: colors.green }},
                {{ label: 'Medio', data: DATA.precos_36l.map(p => p.media), backgroundColor: colors.blue }},
                {{ label: 'Maior', data: DATA.precos_36l.map(p => p.maior), backgroundColor: colors.red }},
            ]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }},
            scales: {{ y: {{ beginAtZero: true, ticks: {{ callback: v => 'R$ ' + v }} }},
                       x: {{ ticks: {{ maxRotation: 45 }} }} }}
        }}
    }});
}}

// Concorrentes Pie
new Chart(document.getElementById('chartConc'), {{
    type: 'doughnut',
    data: {{
        labels: ['Diretos', 'Indiretos'],
        datasets: [{{ data: [DATA.concorrentes.diretos, DATA.concorrentes.indiretos], backgroundColor: [colors.red, colors.blue] }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'bottom' }} }}
    }}
}});

// Lojas Bar
const lojaLabels = Object.keys(DATA.por_loja).sort((a,b) => DATA.por_loja[b] - DATA.por_loja[a]);
const lojaValues = lojaLabels.map(l => DATA.por_loja[l]);
new Chart(document.getElementById('chartLojas'), {{
    type: 'bar',
    data: {{
        labels: lojaLabels,
        datasets: [{{ label: 'Produtos', data: lojaValues, backgroundColor: colors.teal }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ beginAtZero: true }} }}
    }}
}});
</script>
</body>
</html>"""

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard gerado: {DASHBOARD_FILE}")
    return DASHBOARD_FILE


if __name__ == "__main__":
    print("Gerando dashboard...")
    path = build_dashboard()
    print(f"Abra no navegador: file://{path}")
