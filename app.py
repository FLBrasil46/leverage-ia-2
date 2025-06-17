from flask import Flask, render_template_string, request
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re
import requests
import investpy

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
            tipo_provento = extrair_span(cols[3])
            valor_str = extrair_span(cols[4])

            data_com = parse_data(data_com_str)
            data_pgto = parse_data(pagamento_str)
            valor = parse_valor(valor_str)

            incluir = False
            if tipo == "acoes" and data_com and data_com.date() > hoje:
                incluir = True
            elif tipo == "fiis" and data_pgto and data_pgto.date() >= hoje:
                incluir = True

            if incluir:
                proventos.append({
                    "ticker": ticker,
                    "data_com": data_com_str,
                    "pagamento": pagamento_str,
                    "tipo": tipo_provento,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor,
                    "data_pgto_obj": data_pgto
                })

    if tipo == "fiis":
        proventos.sort(key=lambda x: (x["data_pgto_obj"], -x["valor_num"]))
    else:
        proventos.sort(key=lambda x: -x["valor_num"])

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

def gerar_html(proventos, titulo, rota_oposta=None, texto_botao=None, rota_extra=None, texto_extra=None):
    widget_header = gerar_widget_header()

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

    tabela_html = f"""
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
    """ if proventos else "<div class='alert alert-warning text-center'>Não existem opções no momento!</div>"

    botoes = ""
    if rota_oposta:
        botoes += f"<a href='{rota_oposta}' class='btn btn-outline-primary me-2 mb-2'>{texto_botao}</a>"
    if rota_extra:
        botoes += f"<a href='{rota_extra}' class='btn btn-outline-dark mb-2'>{texto_extra}</a>"

    iframe = """
    <div class="mt-5">
        <iframe src="/preco-alvo" width="100%" height="500" style="border:1px solid #ccc;"></iframe>
    </div>
    """ if not rota_oposta else ""

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
            <div class="text-center">{botoes}</div>
            {tabela_html}
            {iframe}
        </div>
    </body>
    </html>
    """

def preco_alvo_genial(ticker):
    try:
        url = f"https://analisa.genialinvestimentos.com.br/acoes/{ticker.lower()}/"
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        el = soup.find("div", text=re.compile(r"Objetivo Final", re.I))
        if el:
            val = el.find_next_sibling("div").get_text(strip=True)
            val = float(val.replace("R$", "").replace(".", "").replace(",", "."))
            return {"fonte": "Genial Analisa", "preco_alvo": val, "data": datetime.today().strftime("%d/%m/%Y")}
    except:
        pass
    return None

def preco_alvo_investing(ticker):
    try:
        data = investpy.get_stock_analyst_rating(stock=ticker, country='brazil')
        if 'Target Price' in data:
            tp = float(data['Target Price'])
            return {"fonte": "Investing.com", "preco_alvo": tp, "data": datetime.today().strftime("%d/%m/%Y")}
    except:
        pass
    return None

def obter_preco_alvo(ticker):
    resultados = []
    for fn in (preco_alvo_genial, preco_alvo_investing):
        dado = fn(ticker)
        if dado:
            resultados.append(dado)
    return resultados

def calcular_media(valores):
    if not valores:
        return 0.0
    return round(sum(v["preco_alvo"] for v in valores) / len(valores), 2)

TEMPLATE_PRECO = """
<!DOCTYPE html><html lang="pt-br"><head><meta charset="UTF-8"><title>Preço-Alvo</title>
<style>table{border:1px solid #ccc;width:100%;border-collapse:collapse}th,td{padding:8px;border:1px solid #ccc}</style>
</head><body>
<h2>Consulta de Preço-Alvo</h2>
<form><input name="ticker" placeholder="Ticker" value="{{ ticker }}"><button>Buscar</button></form>
{% if resultados %}
<table><tr><th>Fonte</th><th>Preço-Alvo (R$)</th><th>Data</th></tr>
{% for r in resultados %}<tr><td>{{r.fonte}}</td><td>R$ {{'%.2f'|format(r.preco_alvo)}}</td><td>{{r.data}}</td></tr>{% endfor %}
<tr><td colspan="3"><strong>Média: R$ {{'%.2f'|format(media)}}</strong></td></tr></table>
{% elif ticker %}<p><em>Nenhum dado encontrado para {{ticker}}</em></p>{% endif %}
</body></html>
"""

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt")
    return gerar_html(proventos, "Melhores oportunidades com Data Com futura", "/bdrs", "Ver BDRs", "/fiis", "Ver FIIs")

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt")
    return gerar_html(proventos, "BDRs em destaque com Data Com futura", "/", "Voltar às Ações")

@app.route("/fiis")
def fiis():
    proventos = carregar_proventos("melhoresfiis.txt", tipo="fiis")
    return gerar_html(proventos, "FIIs com pagamento futuro mais próximos", "/", "Voltar às Ações")

@app.route("/preco-alvo")
def preco_alvo():
    ticker = request.args.get("ticker", "").strip().upper()
    resultados = obter_preco_alvo(ticker) if ticker else []
    media = calcular_media(resultados)
    return render_template_string(TEMPLATE_PRECO, ticker=ticker, resultados=resultados, media=media)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
