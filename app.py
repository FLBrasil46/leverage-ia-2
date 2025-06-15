from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

app = Flask(__name__)
DATA_FILE = "investidor10_dividendos.txt"

# Leitura do HTML salvo
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
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(data_str, fmt)
        except:
            continue
    return None

def parse_valor(valor_str):
    limpo = re.sub(r"[^\d,\.]", "", valor_str.replace(",", "."))
    try:
        return float(limpo)
    except:
        return 0.0

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

            if data_com and pagamento and data_com < pagamento:
                dias_entre = (pagamento - data_com).days
            else:
                dias_entre = 9999  # Caso inválido

            proventos.append({
                "ticker": ticker,
                "tipo": tipo,
                "data_com": data_com_str,
                "pagamento": pagamento_str,
                "valor": f"R$ {valor:.2f}",
                "valor_num": valor,
                "data_com_date": data_com,
                "dias_entre": dias_entre
            })

# Data atual
hoje = datetime.now().date()

# Filtro: apenas ativos com data COM futura
ativos_validos = [
    p for p in proventos if p["data_com_date"] and p["data_com_date"].date() > hoje
]

# Ordenação: menor intervalo e maior valor
ativos_validos = sorted(ativos_validos, key=lambda x: (x["dias_entre"], -x["valor_num"]))

@app.route("/")
def index():
    if not ativos_validos:
        return "<h2 class='text-center mt-5'>Nenhum provento com data COM futura.</h2>"

    linhas = ""
    for i, p in enumerate(ativos_validos):
        destaque = "table-success fw-semibold" if i < 5 else ""
        selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
        linhas += f"""
        <tr class='{destaque}'>
            <td>{p['ticker']}{selo}</td>
            <td>{p['tipo']}</td>
            <td>{p['data_com']}</td>
            <td>{p['pagamento']}</td>
            <td>{p['valor']}</td>
            <td>{p['dias_entre']} dias</td>
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
