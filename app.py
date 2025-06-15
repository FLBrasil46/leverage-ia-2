from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime
import calendar
import re

app = Flask(__name__)

DATA_FILE = "investidor10_dividendos.txt"

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    html = ""
    print(f"Arquivo não encontrado: {DATA_FILE}")

soup = BeautifulSoup(html, "html.parser")
tabela = soup.find("table")
proventos = []

def parse_data(data_str):
    data_str = data_str.strip().replace("\xa0", "").replace("&nbsp;", "")
    try:
        return datetime.strptime(data_str, "%d/%m/%Y")
    except Exception as e:
        print(f"Erro ao converter data: '{data_str}' → {e}")
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

    com_dia = data_com.day
    pgto_dia = pagamento.day

    if pgto_dia >= com_dia:
        intervalo = pgto_dia - com_dia
    else:
        # Se for janeiro, o mês anterior é dezembro do ano anterior
        if pagamento.month == 1:
            mes_anterior = 12
            ano_anterior = pagamento.year - 1
        else:
            mes_anterior = pagamento.month - 1
            ano_anterior = pagamento.year
        dias_mes_anterior = calendar.monthrange(ano_anterior, mes_anterior)[1]
        intervalo = (dias_mes_anterior - com_dia) + pgto_dia

    return intervalo, f"{intervalo} dias"

if tabela:
    for row in tabela.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            data_com = parse_data(cols[2].text)
            pagamento = parse_data(cols[3].text)
            valor = parse_valor(cols[4].text)

            dias_entre, dias_entre_str = calcular_intervalo_dias(data_com, pagamento)

            proventos.append({
                "ticker": cols[0].text.strip(),
                "tipo": cols[1].text.strip(),
                "data_com": cols[2].text.strip(),
                "pagamento": cols[3].text.strip(),
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
