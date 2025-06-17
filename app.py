from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

app = Flask(__name__)

def parse_data(data_str):
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(data_str.strip(), fmt)
        except:
            continue
    return None

def parse_valor(valor_str):
    limpo = re.sub(r"[^\d,\.]", "", valor_str.replace(",", "."))
    try:
        return float(limpo)
    except:
        return 0.0

def extrair_span(td):
    span = td.find("span", class_="table-field")
    return span.text.strip() if span else td.text.strip()

def carregar_proventos(nome_arquivo, usar_data_com=True):
    proventos = []
    hoje = datetime.now().date()

    try:
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tabela = soup.find("table")

    if not tabela:
        return []

    for row in tabela.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 5:
            ticker = extrair_span(cols[0])
            data_com_str = extrair_span(cols[1])
            pagamento_str = extrair_span(cols[2])
            tipo = extrair_span(cols[3])
            valor_str = extrair_span(cols[4])

            data_com = parse_data(data_com_str)
            data_pgto = parse_data(pagamento_str)
            valor = parse_valor(valor_str)

            if not usar_data_com or (data_com and data_com.date() > hoje):
                proventos.append({
                    "ticker": ticker,
                    "data_com": data_com_str,
                    "pagamento": pagamento_str,
                    "data_pgto_dt": data_pgto,
                    "tipo": tipo,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor
                })

    if not usar_data_com:
        proventos = sorted(proventos, key=lambda x: (x["data_pgto_dt"] or datetime.max.date(), -x["valor_num"]))
    else:
        proventos = sorted(proventos, key=lambda x: -x["valor_num"])

    return proventos

def gerar_widget_header():
    return """
    <div class='tradingview-widget-container mb-4'>
      <div class='tradingview-widget-container__widget'></div>
      <script type='text/javascript' src='https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js' async>
      {
        "symbols": [
          {"proName": "BMFBOVESPA:PETR4", "title": "PETR4"},
          {"proName": "BMFBOVESPA:VALE3", "title": "VALE3"},
          {"proName": "BMFBOVESPA:ITUB4", "title": "ITUB4"},
          {"proName": "BMFBOVESPA:B3SA3", "title": "B3SA3"},
          {"proName": "BMFBOVESPA:WEGE3", "title": "WEGE3"}
        ],
        "colorTheme": "light",
        "isTransparent": false,
        "displayMode": "adaptive",
        "locale": "pt"
      }
      </script>
    </div>
    """

def gerar_html(proventos, titulo, rota_oposta=None, texto_botao=None, incluir_iframe=False):
    widget_header = gerar_widget_header()

    if not proventos:
        corpo_tabela = """
        <div class='alert alert-warning text-center'>
            Não existem opções no momento!
        </div>"""
    else:
        corpo_tabela = ""
        for i, p in enumerate(proventos):
            destaque = "table-success fw-semibold" if i < 5 else ""
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            corpo_tabela += f"""
            <tr class='{destaque}'>
                <td>{p['ticker']}{selo}</td>
                <td>{p['data_com']}</td>
                <td>{p['pagamento']}</td>
                <td>{p['tipo']}</td>
                <td>{p['valor']}</td>
            </tr>"""

        corpo_tabela = f"""
        <div class="table-responsive">
            <table class="table table-bordered table-hover shadow-sm rounded">
                <thead class="table-primary text-center">
                    <tr>
                        <th>Ticker</th>
                        <th>Data Com</th>
                        <th>Data Pgto</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>{corpo_tabela}</tbody>
            </table>
        </div>
        """

    botoes = """
    <div class="d-flex justify-content-center gap-3 mb-4">
        <a href="/bdrs" class="btn btn-outline-primary">Ver BDRs</a>
        <a href="/fiis" class="btn btn-outline-success">Ver FIIs</a>
    </div>
    """

    iframe = """
    <div class="mt-5">
        <h3 class="text-center text-secondary">Consulta de Preço-Alvo</h3>
        <iframe src="http://localhost:5001" width="100%" height="400" frameborder="0" style="border:1px solid #ccc;"></iframe>
    </div>
    """ if incluir_iframe else ""

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        {widget_header}
        <div class="container py-4">
            <h1 class="text-center mb-4 text-primary">LEVERAGE IA</h1>
            <p class="text-center text-muted">{titulo}</p>
            {botoes}
            {corpo_tabela}
            {iframe}
        </div>
    </body>
    </html>
    """

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt", usar_data_com=True)
    return gerar_html(
        proventos,
        "Melhores oportunidades do mercado brasileiro com Data Com futura",
        incluir_iframe=True
    )

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt", usar_data_com=True)
    return gerar_html(
        proventos,
        "BDRs em destaque com Data Com futura",
        rota_oposta="/",
        texto_botao="Voltar às Ações"
    )

@app.route("/fiis")
def fiis():
    proventos = carregar_proventos("melhoresfiis.txt", usar_data_com=False)
    return gerar_html(
        proventos,
        "FIIs com maiores pagamentos próximos",
        rota_oposta="/",
        texto_botao="Voltar às Ações"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
