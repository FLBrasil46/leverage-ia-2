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
        if len(cols) >= 4:
            ticker = extrair_span(cols[0])
            pagamento_str = extrair_span(cols[1])
            tipo = extrair_span(cols[2])
            valor_str = extrair_span(cols[3])

            pagamento = parse_data(pagamento_str)
            valor = parse_valor(valor_str)

            if pagamento and pagamento.date() > hoje:
                fiis.append({
                    "ticker": ticker,
                    "pagamento": pagamento_str,
                    "tipo": tipo,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor
                })

    return sorted(fiis, key=lambda x: -x["valor_num"])

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
        corpo_tabela = """
        <div class='alert alert-warning text-center'>
            Não existem opções no momento!
        </div>"""
    else:
        linhas = ""
        for i, p in enumerate(proventos):
            destaque = "table-success fw-semibold" if i < 5 else ""
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            if tipo == "acoes":
                linhas += f"""
                <tr class='{destaque}'>
                    <td>{p['ticker']}{selo}</td>
                    <td>{p['data_com']}</td>
                    <td>{p['pagamento']}</td>
                    <td>{p['tipo']}</td>
                    <td>{p['valor']}</td>
                </tr>"""
            else:  # FIIs
                linhas += f"""
                <tr class='{destaque}'>
                    <td>{p['ticker']}{selo}</td>
                    <td>{p['pagamento']}</td>
                    <td>{p['tipo']}</td>
                    <td>{p['valor']}</td>
                </tr>"""

        headers = (
            "<th>Ticker</th><th>Data Com</th><th>Data Pgto</th><th>Tipo</th><th>Valor</th>"
            if tipo == "acoes"
            else "<th>Ticker</th><th>Pagamento</th><th>Tipo</th><th>Valor</th>"
        )

        corpo_tabela = f"""
        <div class="table-responsive">
            <table class="table table-bordered table-hover shadow-sm rounded">
                <thead class="table-primary text-center">
                    <tr>{headers}</tr>
                </thead>
                <tbody>{linhas}</tbody>
            </table>
        </div>
        """

    botoes = ""
    if rota_oposta and texto_botao:
        botoes += f"""<a href="{rota_oposta}" class="btn btn-outline-primary mb-3 me-2">{texto_botao}</a>"""

    if tipo == "acoes":
        botoes += """
        <a href="/fiis" class="btn btn-outline-success mb-3 me-2">Ver FIIs</a>"""

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
            {corpo_tabela}
        </div>
    </body>
    </html>
    """

@app.route("/")
def index():
    proventos = carregar_proventos("investidor10_dividendos.txt")
    return gerar_html(
        proventos,
        "Melhores oportunidades do mercado brasileiro com Data Com futura",
        "/bdrs",
        "Ver BDRs"
    )

@app.route("/bdrs")
def bdrs():
    proventos = carregar_proventos("investidor10_bdrs.txt")
    return gerar_html(
        proventos,
        "BDRs em destaque com Data Com futura",
        "/",
        "Voltar às Ações"
    )

@app.route("/fiis")
def fiis():
    fiis = carregar_fiis("melhoresfiis.txt")
    return gerar_html(
        fiis,
        "FIIs com maiores pagamentos futuros",
        "/",
        "Voltar às Ações",
        tipo="fiis"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
