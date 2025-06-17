from flask import Flask, render_template_string, request
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

def carregar_proventos(nome_arquivo):
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
            valor = parse_valor(valor_str)
            if data_com and data_com.date() > hoje:
                proventos.append({
                    "ticker": ticker,
                    "data_com": data_com_str,
                    "pagamento": pagamento_str,
                    "tipo": tipo,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor
                })
    return sorted(proventos, key=lambda x: -x["valor_num"])

def carregar_fiis(nome_arquivo):
    fiis = []
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
            pagamento_str = extrair_span(cols[2])
            tipo = extrair_span(cols[3])
            valor_str = extrair_span(cols[4])
            data_pgto = parse_data(pagamento_str)
            valor = parse_valor(valor_str)
            if data_pgto and data_pgto.date() >= hoje:
                fiis.append({
                    "ticker": ticker,
                    "data_pgto": pagamento_str,
                    "tipo": tipo,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor,
                    "data_pgto_val": data_pgto
                })
    return sorted(fiis, key=lambda x: (x["data_pgto_val"], -x["valor_num"]))

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

def gerar_html(proventos, titulo, rota_oposta=None, texto_botao=None, tipo="acoes"):
    widget_header = gerar_widget_header()
    if not proventos:
        corpo = "<div class='alert alert-warning text-center'>Não existem opções no momento!</div>"
    else:
        linhas = ""
        for i, p in enumerate(proventos):
            destaque = "table-success fw-semibold" if i < 5 else ""
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            if tipo == "fiis":
                linhas += f"""
                <tr class='{destaque}'>
                    <td>{p['ticker']}{selo}</td>
                    <td>{p['data_pgto']}</td>
                    <td>{p['tipo']}</td>
                    <td>{p['valor']}</td>
                </tr>"""
            else:
                linhas += f"""
                <tr class='{destaque}'>
                    <td>{p['ticker']}{selo}</td>
                    <td>{p['data_com']}</td>
                    <td>{p['pagamento']}</td>
                    <td>{p['tipo']}</td>
                    <td>{p['valor']}</td>
                </tr>"""
        cabecalho = """
            <tr>
                <th>Ticker</th>
                <th>Data Com</th>
                <th>Data Pgto</th>
                <th>Tipo</th>
                <th>Valor</th>
            </tr>""" if tipo != "fiis" else """
            <tr>
                <th>Ticker</th>
                <th>Data Pgto</th>
                <th>Tipo</th>
                <th>Valor</th>
            </tr>"""
        corpo = f"""
        <div class="table-responsive">
            <table class="table table-bordered table-hover shadow-sm rounded">
                <thead class="table-primary text-center">{cabecalho}</thead>
                <tbody>{linhas}</tbody>
            </table>
        </div>"""
    botao_extra = f"<a href='{rota_oposta}' class='btn btn-outline-secondary mb-3'>{texto_botao}</a>" if rota_oposta and texto_botao else ""
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
            <div class="text-center">{botao_extra}</div>
            {corpo}
        </div>
    </body>
    </html>
    """

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt")
    botoes = """
    <div class="d-flex flex-wrap justify-content-center gap-3 mb-4">
        <a href="/bdrs" class="btn btn-outline-primary px-4 py-2 shadow-sm">BDRs</a>
        <a href="/fiis" class="btn btn-outline-success px-4 py-2 shadow-sm">FIIs</a>
        <a href="/preco-alvo" class="btn btn-outline-warning px-4 py-2 shadow-sm text-dark">Preço-Alvo</a>
    </div>"""
    html = gerar_html(proventos, "Melhores oportunidades do mercado brasileiro com Data Com futura")
    return html.replace('<div class="text-center"></div>', botoes)

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt")
    return gerar_html(proventos, "BDRs em destaque com Data Com futura", "/", "Voltar às Ações")

@app.route("/fiis")
def fiis():
    fiis_data = carregar_fiis("melhoresfiis.txt")
    return gerar_html(fiis_data, "FIIs com pagamentos mais próximos e maior valor", "/", "Voltar às Ações", tipo="fiis")

@app.route("/preco-alvo", methods=["GET"])
def preco_alvo():
    TEMPLATE = """<html><head><title>Preço-Alvo</title><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'></head><body><div class='container py-4'><h1 class='text-center text-primary mb-4'>Consulta de Preço-Alvo</h1><form method='get' class='text-center mb-4'><input type='text' name='ticker' placeholder='Digite o ticker...' required class='form-control d-inline-block w-auto me-2' value='{{ ticker }}'><button type='submit' class='btn btn-primary'>Buscar</button><a href='/' class='btn btn-secondary ms-2'>Voltar</a></form>{% if resultados %}<h5>Resultados para <strong>{{ ticker.upper() }}</strong>:</h5><table class='table table-bordered table-hover'><thead class='table-primary'><tr><th>Fonte</th><th>Preço-Alvo (R$)</th><th>Data</th></tr></thead><tbody>{% for item in resultados %}<tr><td>{{ item.fonte }}</td><td>R$ {{ '%.2f'|format(item.preco_alvo) }}</td><td>{{ item.data }}</td></tr>{% endfor %}<tr class='table-success fw-bold'><td colspan='3'>Média: R$ {{ media }}</td></tr></tbody></table>{% elif ticker %}<div class='alert alert-warning'>Nenhum dado encontrado para o ticker informado.</div>{% endif %}</div></body></html>"""
    def obter_precos_alvo(ticker):
        dados = {
            "BBAS3": [
                {"fonte": "XP Investimentos", "preco_alvo": 41.00, "data": "11/04/2025"},
                {"fonte": "BTG Pactual", "preco_alvo": 35.00, "data": "23/01/2025"},
                {"fonte": "Genial Analisa", "preco_alvo": 34.00, "data": "2025"},
                {"fonte": "Investing.com", "preco_alvo": 30.63, "data": "2025"},
                {"fonte": "UBS BB", "preco_alvo": 36.00, "data": "2025"},
                {"fonte": "Santander", "preco_alvo": 33.00, "data": "2025"},
                {"fonte": "Goldman Sachs", "preco_alvo": 32.50, "data": "2025"}
            ]
        }
        return dados.get(ticker.upper(), [])

    def calcular_media(valores):
        precos = [item["preco_alvo"] for item in valores if item["preco_alvo"]]
        return round(sum(precos) / len(precos), 2) if precos else 0.0

    ticker = request.args.get("ticker", "").strip()
    resultados = obter_precos_alvo(ticker) if ticker else []
    media = calcular_media(resultados) if resultados else 0.0

    return render_template_string(TEMPLATE, ticker=ticker, resultados=resultados, media=media)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
