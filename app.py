from flask import Flask, request
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re
import yfinance as yf

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

def dias_entre(data1, data2):
    try:
        return abs((data2 - data1).days)
    except:
        return 9999

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

            if usar_data_com:
                if data_com and data_pgto and data_com.date() > hoje:
                    proventos.append({
                        "ticker": ticker,
                        "data_com": data_com_str,
                        "data_com_val": data_com.date(),
                        "pagamento": pagamento_str,
                        "data_pgto_val": data_pgto.date(),
                        "dias_intervalo": dias_entre(data_com.date(), data_pgto.date()),
                        "tipo": tipo,
                        "valor": f"R$ {valor:.2f}",
                        "valor_num": valor
                    })
            else:
                if data_pgto and data_pgto.date() >= hoje:
                    proventos.append({
                        "ticker": ticker,
                        "data_pgto": pagamento_str,
                        "data_pgto_val": data_pgto.date(),
                        "tipo": tipo,
                        "valor": f"R$ {valor:.2f}",
                        "valor_num": valor
                    })

    if usar_data_com:
        return sorted(proventos, key=lambda x: (x["data_com_val"], x["dias_intervalo"], -x["valor_num"]))
    else:
        return sorted(proventos, key=lambda x: (x["data_pgto_val"], -x["valor_num"]))

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

def buscar_yfinance(ticker):
    try:
        info = yf.Ticker(ticker + ".SA").info
        preco = info.get("currentPrice")
        alvo = info.get("targetMeanPrice")
        return preco, alvo
    except:
        return None, None

def gerar_bloco_precos(tickers):
    linhas = ""
    for t in tickers:
        preco, alvo = buscar_yfinance(t)
        if preco and alvo:
            linhas += f"<tr><td>{t}</td><td>R$ {preco:.2f}</td><td>R$ {alvo:.2f}</td></tr>"

    if not linhas:
        return ""

    return f"""
    <div class='mt-5'>
        <h5 class='text-primary'>Preço atual e preço-alvo dos TOP 5:</h5>
        <div class='table-responsive'>
            <table class='table table-bordered'>
                <thead><tr><th>Ticker</th><th>Cotação Atual</th><th>Preço-Alvo</th></tr></thead>
                <tbody>{linhas}</tbody>
            </table>
        </div>
    </div>"""

def gerar_bloco_busca():
    return """
    <div class='mt-5'>
        <h5 class='text-primary'>Buscar cotação e preço-alvo manualmente</h5>
        <form method='get'>
            <div class='input-group mb-3'>
                <input type='text' name='busca' class='form-control' placeholder='Ex: BBAS3' required>
                <button class='btn btn-primary' type='submit'>Buscar</button>
            </div>
        </form>
    </div>
    """

def gerar_resultado_busca(ticker):
    preco, alvo = buscar_yfinance(ticker)
    if preco and alvo:
        return f"""
        <div class='alert alert-info'>
            <strong>{ticker.upper()}</strong> - Cotação: R$ {preco:.2f} | Preço-Alvo: R$ {alvo:.2f}
        </div>
        """
    return "<div class='alert alert-warning'>Não encontrado ou sem dados suficientes.</div>"

def gerar_html(proventos, titulo):
    widget = gerar_widget_header()
    corpo = ""

    for i, p in enumerate(proventos):
        destaque = "table-success fw-semibold" if i < 5 else ""
        selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
        if "data_com" in p:
            corpo += f"""
            <tr class='{destaque}'>
                <td>{p['ticker']}{selo}</td>
                <td>{p['data_com']}</td>
                <td>{p['pagamento']}</td>
                <td>{p['dias_intervalo']} dias</td>
                <td>{p['tipo']}</td>
                <td>{p['valor']}</td>
            </tr>"""
        else:
            corpo += f"""
            <tr class='{destaque}'>
                <td>{p['ticker']}{selo}</td>
                <td>{p['data_pgto']}</td>
                <td>{p['tipo']}</td>
                <td>{p['valor']}</td>
            </tr>"""

    cabecalho = (
        "<th>Ticker</th><th>Data Com</th><th>Data Pgto</th><th>Intervalo</th><th>Tipo</th><th>Valor</th>"
        if "data_com" in proventos[0]
        else "<th>Ticker</th><th>Data Pgto</th><th>Tipo</th><th>Valor</th>"
    )

    tabela = f"""
    <div class='table-responsive'>
        <table class='table table-bordered table-hover'>
            <thead class='table-primary text-center'><tr>{cabecalho}</tr></thead>
            <tbody>{corpo}</tbody>
        </table>
    </div>"""

    top5 = [p['ticker'] for p in proventos[:5]]
    bloco_precos = gerar_bloco_precos(top5)
    bloco_busca = gerar_bloco_busca()
    resultado = gerar_resultado_busca(request.args.get("busca", "").strip()) if request.args.get("busca") else ""

    botoes = """
    <div class="d-flex flex-wrap justify-content-center gap-3 mb-4">
        <a href="/" class="btn btn-outline-primary">Ações Julho</a>
        <a href="/fiis" class="btn btn-outline-success">FIIs</a>
        <a href="/bdrs" class="btn btn-outline-secondary">BDRs</a>
    </div>"""

    return f"""
    <html lang='pt-br'>
    <head>
        <meta charset='utf-8'>
        <title>{titulo}</title>
        <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
    </head>
    <body>
        {widget}
        <div class='container py-4'>
            <h1 class='text-center text-primary mb-4'>LEVERAGE IA</h1>
            <p class='text-center text-muted'>{titulo}</p>
            {botoes}
            {tabela}
            {bloco_precos}
            {bloco_busca}
            {resultado}
        </div>
    </body>
    </html>"""

@app.route("/")
def acoes_julho():
    proventos = carregar_proventos("acoes_julho_25.txt", usar_data_com=True)
    return gerar_html(proventos, "Ações de julho/2025 com melhor oportunidade")

@app.route("/fiis")
def fiis():
    proventos = carregar_proventos("melhoresfiis.txt", usar_data_com=False)
    return gerar_html(proventos, "FIIs com pagamentos mais próximos e maior valor")

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt", usar_data_com=True)
    return gerar_html(proventos, "BDRs com data COM futura e maior retorno")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
