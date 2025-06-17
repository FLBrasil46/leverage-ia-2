from flask import Flask, render_template_string, request
from bs4 import BeautifulSoup
from datetime import datetime
import os
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

def carregar_proventos(nome_arquivo, tipo="acoes"):
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
            tipo_str = extrair_span(cols[3])
            valor_str = extrair_span(cols[4])

            data_com = parse_data(data_com_str)
            data_pgto = parse_data(pagamento_str)
            valor = parse_valor(valor_str)

            if tipo == "acoes":
                if data_com and data_com.date() > hoje:
                    proventos.append({
                        "ticker": ticker,
                        "data_com": data_com_str,
                        "pagamento": pagamento_str,
                        "tipo": tipo_str,
                        "valor": f"R$ {valor:.2f}",
                        "valor_num": valor
                    })
            elif tipo == "fiis":
                if data_pgto and data_pgto.date() >= hoje:
                    proventos.append({
                        "ticker": ticker,
                        "data_com": data_com_str,
                        "pagamento": pagamento_str,
                        "tipo": tipo_str,
                        "valor": f"R$ {valor:.2f}",
                        "valor_num": valor,
                        "data_pagamento_obj": data_pgto
                    })

    if tipo == "fiis":
        proventos.sort(key=lambda x: (x["data_pagamento_obj"], -x["valor_num"]))
    else:
        proventos.sort(key=lambda x: -x["valor_num"])

    return proventos[:5]

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

def gerar_html(proventos, titulo, rota_oposta=None, texto_botao=None):
    widget_header = gerar_widget_header()

    botoes_extra = f"""
    <div class="d-flex justify-content-center gap-3 mb-3">
        <a href="/" class="btn btn-outline-primary">Ações</a>
        <a href="/bdrs" class="btn btn-outline-success">BDRs</a>
        <a href="/fiis" class="btn btn-outline-warning">FIIs</a>
        <a href="/preco-alvo" class="btn btn-outline-dark">Preço-Alvo</a>
    </div>"""

    if not proventos:
        corpo_tabela = "<div class='alert alert-warning text-center'>Não existem opções no momento!</div>"
    else:
        linhas = ""
        for i, p in enumerate(proventos):
            linhas += f"""
            <tr class="{'table-success fw-semibold' if i < 5 else ''}">
                <td>{p['ticker']}</td>
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
                <tbody>{linhas}</tbody>
            </table>
        </div>"""

    iframe = ""
    if rota_oposta is None:
        iframe = """
        <div class="mt-4">
            <h4 class="text-center text-muted">Consulta de Preço-Alvo</h4>
            <iframe src="/preco-alvo" width="100%" height="500" style="border:none;"></iframe>
        </div>"""

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
            {botoes_extra}
            {corpo_tabela}
            {iframe}
        </div>
    </body>
    </html>
    """

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt", tipo="acoes")
    return gerar_html(proventos, "Melhores oportunidades do mercado brasileiro com Data Com futura")

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt", tipo="acoes")
    return gerar_html(proventos, "BDRs em destaque com Data Com futura")

@app.route("/fiis")
def fiis():
    proventos = carregar_proventos("melhoresfiis.txt", tipo="fiis")
    return gerar_html(proventos, "FIIs com pagamentos mais próximos")

# ----------- Rota de Preço-Alvo ----------------

def obter_precos_alvo(ticker):
    dados = {
        "BBAS3": [
            {"fonte": "XP Investimentos", "preco_alvo": 41.00, "data": "11/04/2025"},
            {"fonte": "BTG Pactual", "preco_alvo": 35.00, "data": "23/01/2025"},
            {"fonte": "Genial Analisa", "preco_alvo": 34.00, "data": "2025"},
            {"fonte": "Investing.com (consenso)", "preco_alvo": 30.63, "data": "2025"},
            {"fonte": "UBS BB", "preco_alvo": 36.00, "data": "2025"},
            {"fonte": "Santander", "preco_alvo": 33.00, "data": "2025"},
            {"fonte": "Goldman Sachs", "preco_alvo": 32.50, "data": "2025"}
        ]
    }
    return dados.get(ticker.upper(), [])

def calcular_media(valores):
    precos = [item["preco_alvo"] for item in valores if item["preco_alvo"]]
    return round(sum(precos) / len(precos), 2) if precos else 0.0

@app.route("/preco-alvo", methods=["GET"])
def preco_alvo():
    ticker = request.args.get("ticker", "").strip()
    resultados = obter_precos_alvo(ticker) if ticker else []
    media = calcular_media(resultados) if resultados else 0.0

    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Preço-Alvo</title>
        <style>
            body {{ font-family: Arial; padding: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <form method="get">
            <label for="ticker">Ticker:</label>
            <input type="text" id="ticker" name="ticker" value="{ticker}" required>
            <button type="submit">Buscar</button>
        </form>
        {resultado_tabela}
    </body>
    </html>
    """

    if resultados:
        linhas = "".join(
            f"<tr><td>{r['fonte']}</td><td>R$ {r['preco_alvo']:.2f}</td><td>{r['data']}</td></tr>"
            for r in resultados
        )
        resultado_tabela = f"""
        <h2>Resultado para {ticker.upper()}</h2>
        <table>
            <tr><th>Fonte</th><th>Preço-Alvo</th><th>Data</th></tr>
            {linhas}
            <tr><td colspan="3"><strong>Média: R$ {media:.2f}</strong></td></tr>
        </table>
        """
    elif ticker:
        resultado_tabela = f"<p><em>Nenhum dado encontrado para o ticker {ticker.upper()}.</em></p>"
    else:
        resultado_tabela = ""

    return html.format(ticker=ticker, resultado_tabela=resultado_tabela)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
