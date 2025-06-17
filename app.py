from flask import Flask
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re
import json

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
            valor = parse_valor(extrair_span(cols[4]))
            data_com = parse_data(data_com_str)
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

def gerar_widget(tickers):
    symbols = []
    for t in tickers[:5]:
        symbol = t["ticker"].upper()
        if "." in symbol:
            symbols.append({"description": symbol, "proName": f"BMFBOVESPA:{symbol.replace('.', '')}"})
        else:
            symbols.append({"description": symbol, "proName": f"BMFBOVESPA:{symbol}"})
    config = {
        "symbols": symbols,
        "showSymbolLogo": True,
        "colorTheme": "light",
        "isTransparent": False,
        "displayMode": "adaptive",
        "locale": "pt"
    }
    return f"""
    <div class="tradingview-widget-container mb-4">
        <div id="ticker-widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
        {json.dumps(config)}
        </script>
    </div>
    """

def gerar_html(proventos, titulo, rota_oposta=None, texto_botao=None, widget_html=""):
    if not proventos:
        corpo = "<div class='alert alert-warning'>Não existem opções no momento!</div>"
    else:
        linhas = ""
        for i, p in enumerate(proventos):
            destaque = "table-success fw-semibold" if i < 5 else ""
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            linhas += (
                f"<tr class='{destaque}'>"
                f"<td>{p['ticker']}{selo}</td>"
                f"<td>{p['data_com']}</td>"
                f"<td>{p['pagamento']}</td>"
                f"<td>{p['tipo']}</td>"
                f"<td>{p['valor']}</td>"
                "</tr>"
            )
        corpo = (
            "<div class='table-responsive'>"
            "<table class='table table-bordered table-hover'>"
            "<thead class='table-primary text-center'><tr>"
            "<th>Ticker</th><th>Data Com</th><th>Data Pgto</th><th>Tipo</th><th>Valor</th>"
            "</tr></thead>"
            f"<tbody>{linhas}</tbody>"
            "</table></div>"
        )

    botao = ""
    if rota_oposta and texto_botao:
        botao = f"<a href='{rota_oposta}' class='btn btn-outline-primary mb-3'>{texto_botao}</a>"

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
      <meta charset="utf-8">
      <title>{titulo}</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-3">

      {widget_html}

      <h1 class='text-center mb-4 text-primary'>LEVERAGE IA</h1>
      <p class='text-center text-muted mb-3'>{titulo}</p>
      <div class="text-center">{botao}</div>
      {corpo}
    </body>
    </html>
    """

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt")
    widget = gerar_widget(proventos) if proventos else ""
    return gerar_html(proventos,
        "Melhores oportunidades do mercado brasileiro com Data Com futura",
        "/bdrs", "Ver BDRs",
        widget
    )

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt")
    widget = gerar_widget(proventos) if proventos else ""
    return gerar_html(proventos,
        "BDRs em destaque com Data Com futura",
        "/", "Voltar às Ações",
        widget
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
