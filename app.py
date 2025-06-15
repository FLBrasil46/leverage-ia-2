from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime

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
    try:
        return datetime.strptime(data_str, "%d/%m/%Y")
    except:
        return None

if tabela:
    for row in tabela.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            data_com_str = cols[2].text.strip()
            pagamento_str = cols[3].text.strip()
            data_com = parse_data(data_com_str)
            pagamento = parse_data(pagamento_str)
            valor_str = cols[4].text.strip().replace("R$", "").replace(",", ".")
            try:
                valor = float(valor_str)
            except:
                valor = 0.0
            dias_entre = (pagamento - data_com).days if data_com and pagamento else None

            if dias_entre is not None and dias_entre >= 0:
                proventos.append({
                    "ticker": cols[0].text.strip(),
                    "tipo": cols[1].text.strip(),
                    "data_com": data_com_str,
                    "pagamento": pagamento_str,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor,
                    "dias_entre": dias_entre
                })

    proventos = sorted(proventos, key=lambda x: (x['dias_entre'], -x['valor_num']))

@app.route("/")
def index():
    if not proventos:
        return "<h2>Nenhum dado carregado. Verifique o arquivo investidor10_dividendos.txt</h2>"

    linhas = ""
    for i, p in enumerate(proventos):
        destaque = "table-success" if i < 5 else ""
        selo = " <span class='badge bg-success'>TOP</span>" if i < 5 else ""
        linhas += f"<tr class='{destaque}'><td>{p['ticker']}{selo}</td><td>{p['tipo']}</td><td>{p['data_com']}</td><td>{p['pagamento']}</td><td>{p['valor']}</td><td>{p['dias_entre']} dias</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset='utf-8'>
    <title>Proventos - Investidor10</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
    </head><body class='container py-4'>
    <h1 class='mb-4'>Proventos priorizados por intervalo e valor</h1>
    <table class='table table-bordered table-striped'>
        <thead class='table-dark'><tr>
            <th>Ticker</th><th>Tipo</th><th>Data COM</th><th>Pagamento</th><th>Valor</th><th>Intervalo</th>
        </tr></thead>
        <tbody>{linhas}</tbody>
    </table>
    </body></html>
    """
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Usando porta:", port)
    app.run(host="0.0.0.0", port=port)
