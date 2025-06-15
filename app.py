from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime
import os

app = Flask(__name__)

# Arquivo com o HTML salvo da página do Investidor10
DATA_FILE = "investidor10_dividendos.txt"

# Leitura segura do arquivo
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    html = ""
    print(f"Arquivo não encontrado: {DATA_FILE}")

# Parsing do HTML
soup = BeautifulSoup(html, "html.parser")
tabela = soup.find("table")
proventos = []

# Função para converter data
def parse_data(data_str):
    try:
        return datetime.strptime(data_str, "%d/%m/%y")
    except:
        return None

# Data atual
hoje = datetime.today()

# Coleta dos dados e ordenação
if tabela:
    for row in tabela.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            data_com = parse_data(cols[2].text.strip())
            pagamento = parse_data(cols[3].text.strip())
            valor_str = cols[4].text.strip().replace("R$", "").replace(",", ".")
            try:
                valor = float(valor_str)
            except:
                valor = 0.0
            if data_com and data_com >= hoje:
                proventos.append({
                    "ticker": cols[0].text.strip(),
                    "tipo": cols[1].text.strip(),
                    "data_com": cols[2].text.strip(),
                    "pagamento": cols[3].text.strip(),
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor,
                })

    # Ordena por menor intervalo e maior valor
    proventos = sorted(
        proventos,
        key=lambda x: (
            (parse_data(x['pagamento']) - parse_data(x['data_com'])).days if parse_data(x['pagamento']) and parse_data(x['data_com']) else 9999,
            -x['valor_num']
        )
    )

@app.route("/")
def index():
    if not proventos:
        return "<h2>Nenhum dado carregado. Verifique o arquivo investidor10_dividendos.txt</h2>"

    linhas = ""
    for i, p in enumerate(proventos):
        destaque = "table-success" if i < 5 else ""
        selo = " <span class='badge bg-success'>TOP</span>" if i < 5 else ""
        linhas += f"<tr class='{destaque}'><td>{p['ticker']}{selo}</td><td>{p['tipo']}</td><td>{p['data_com']}</td><td>{p['pagamento']}</td><td>{p['valor']}</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset='utf-8'>
    <title>LEVERAGE IA - MELHORES OPORTUNIDADES DO MERCADO</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
    </head><body class='container py-4'>
    <h1 class='mb-4'>LEVERAGE IA - MELHORES OPORTUNIDADES DO MERCADO</h1>

    <a href="/relatorio_xp" class="btn btn-primary mb-4">📊 Ver Preços-Alvo da XP (Compra)</a>

    <table class='table table-bordered table-striped'>
        <thead class='table-dark'><tr>
            <th>Ticker</th><th>Tipo</th><th>Data Com</th><th>Pagamento</th><th>Valor</th>
        </tr></thead>
        <tbody>{linhas}</tbody>
    </table>
    </body></html>
    """
    return html

# Rota do relatório da XP (exemplo de retorno estático)
@app.route("/relatorio_xp")
def relatorio_xp():
    return "<h2>Relatório XP em construção ou carregamento dinâmico aqui...</h2>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Usando porta:", port)
    app.run(host="0.0.0.0", port=port)



