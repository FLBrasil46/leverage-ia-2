from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime
import calendar
import re

app = Flask(__name__)
DATA_FILE = "investidor10_dividendos.txt"

# Leitura do HTML
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    html = ""
    print(f"Arquivo não encontrado: {DATA_FILE}")

soup = BeautifulSoup(html, "html.parser")
tabela = soup.find("table")
proventos = []

def extrair_texto_span(td):
    span = td.find("span", class_="table-field")
    return span.text.strip() if span else td.text.strip()

def parse_data(data_str):
    try:
        return datetime.strptime(data_str, "%d/%m/%y")
    except Exception:
        return None

def parse_valor(valor_str):
    limpo = re.sub(r"[^\d,\.]", "", valor_str.replace(",", "."))
    try:
        return float(limpo)
    except:
        return 0.0

def calcular_intervalo_dias(data_com, pagamento):
    if not data_com or not pagamento:
        return 9999, "-"

    # Subtrai diretamente as datas completas
    intervalo = (pagamento - data_com).days
    if intervalo < 0:
        return 9999, "-"
    return intervalo, f"{intervalo} dias"

# Coleta dos dados da tabela
if tabela:
    for row in tabela.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            ticker = extrair_texto_span(cols[0])
            tipo = extrair_texto_span(cols[1])
            data_com_str = extrair_texto_span(cols[2])
            pagamento_str = extrair_texto_span(cols[3])
            valor_str = extrair_texto_span(cols[4])

            data_com = parse_data(data_com_str)
            pagamento = parse_data(pagamento_str)
            valor = parse_valor(valor_str)
            dias_entre, dias_entre_str = calcular_intervalo_dias(data_com, pagamento)

            proventos.append({
                "ticker": ticker,
                "tipo": tipo,
                "data_com": data_com_str,
                "pagamento": pagamento_str,
                "valor": f"R$ {valor:.2f}",
                "valor_num": valor,
                "dias_entre": dias_entre,
                "dias_entre_str": dias_entre_str
            })

    proventos = sorted(proventos, key=lambda x: (x['dias_entre'], -x['valor_num']))

@app.route("/")
def index():
    if not proventos:
        return "<h2 class='text-center mt-5'>Nenhum dado carregado. Verifique o arquivo investidor10_dividendos.txt</h2>"

    linhas = ""
    for i, p in enumerate(proventos):
        destaque = "table-success fw-semibold" if i < 5 else ""
        selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
        linhas += f"""
        <tr class='{destaque}'>
            <td>{p['ticker']}{selo}</td>
            <td>{p['tipo']}</td>
            <td>{p['data_com']}</td>
            <td>{p['pagamento']}</td>
            <td>{p['valor']}</td>
            <td>{p['dias_entre_str']}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>LEVERAGE IA - MELHORES OPORTUNIDADES DO MERCADO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f8f9fa;
            }}
            .titulo {{
                font-weight: 700;
                font-size: 1.8rem;
                color: #0d6efd;
            }}
            .subtitulo {{
                color: #6c757d;
            }}
            table {{
                background-color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="text-center mb-4">
                <div class="titulo">LEVERAGE IA</div>
                <div class="subtitulo">Melhores oportunidades do mercado</div>
            </div>
            <div class="table-responsive">
                <table class="table table-bordered table-hover shadow-sm rounded">
                    <thead class="table-primary text-center">
                        <tr>
                            <th>Ticker</th>
                            <th>Tipo</th>
                            <th>Data COM</th>
                            <th>Pagamento</th>
                            <th>Valor</th>
                            <th>Intervalo</th>
                        </tr>
                    </thead>
                    <tbody>{linhas}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Usando porta:", port)
    app.run(host="0.0.0.0", port=port)
