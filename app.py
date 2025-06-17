from flask import Flask
from bs4 import BeautifulSoup
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

def parse_valor(v):
    limpa = re.sub(r"[^\d,\.]", "", v.replace(",", "."))
    return float(limpa) if limpa else 0.0

def extrair_span(td):
    span = td.find("span", class_="table-field")
    return span.text.strip() if span else td.text.strip()

def carregar_proventos(arq):
    hoje = datetime.now().date()
    proventos = []
    try:
        html = open(arq, encoding="utf-8").read()
    except:
        return []
    soup = BeautifulSoup(html, "html.parser")
    t = soup.find("table")
    if not t: return []
    for row in t.find_all("tr")[1:]:
        c = row.find_all("td")
        if len(c) >= 5:
            data_com = parse_data(extrair_span(c[1]))
            if data_com and data_com.date() > hoje:
                proventos.append({
                    "ticker": extrair_span(c[0]).upper(),
                    "data_com": extrair_span(c[1]),
                    "pagamento": extrair_span(c[2]),
                    "tipo": extrair_span(c[3]),
                    "valor_num": parse_valor(extrair_span(c[4])),
                    "valor": f"R$ {parse_valor(extrair_span(c[4])):.2f}"
                })
    return sorted(proventos, key=lambda x: -x["valor_num"])

def gerar_ticker_iframe(proventos):
    top = proventos[:5]
    symbols = ",".join([
      f'{{"proName":"BMFBOVESPA:{p["ticker"]}","description":""}}'
      for p in top
    ])
    config = (
        "%7B"
        f"%22symbols%22%3A%5B{symbols}%5D,"
        "%22showSymbolLogo%22%3Atrue,"
        "%22colorTheme%22%3A%22light%22,"
        "%22displayMode%22%3A%22regular%22,"
        "%22locale%22%3A%22pt%22"
        "%7D"
    )
    return (
        '<iframe style="width:100%;height:45px;border:0;" '
        'src="https://s.tradingview.com/embed-widget/ticker-tape/?locale=pt#'
        + config +
        '"></iframe>'  # :contentReference[oaicite:1]{index=1}
    )

def gerar_html(provs, title, rota=None, bot_text=""):
    widget = gerar_ticker_iframe(provs) if provs else ""
    body = ""
    if not provs:
        body = "<div class='alert alert-warning'>Não existem opções!</div>"
    else:
        rows = ""
        for i, p in enumerate(provs):
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            rows += (
                f"<tr><td>{p['ticker']}{selo}</td>"
                f"<td>{p['data_com']}</td>"
                f"<td>{p['pagamento']}</td>"
                f"<td>{p['tipo']}</td>"
                f"<td>{p['valor']}</td></tr>"
            )
        body = (
            "<div class='table-responsive'>"
            "<table class='table table-bordered table-hover'>"
            "<thead class='table-primary text-center'><tr>"
            "<th>Ticker</th><th>Data Com</th><th>Data Pgto</th><th>Tipo</th><th>Valor</th>"
            "</tr></thead><tbody>"
            + rows +
            "</tbody></table></div>"
        )
    btn = f"<a href='{rota}' class='btn btn-outline-primary mb-3'>{bot_text}</a>" if rota else ""
    return f"""
    <!DOCTYPE html><html lang="pt-br"><head>
    <meta charset="utf-8"><title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="container py-3">
      {widget}
      <h1 class="text-center mb-4 text-primary">LEVERAGE IA</h1>
      <p class="text-center text-muted mb-3">{title}</p>
      <div class="text-center">{btn}</div>
      {body}
    </body></html>
    """

@app.route("/")
def index():
    prov = carregar_proventos("investidor10_dividendos.txt")
    return gerar_html(prov, "Melhores Ações (Data Com futura)", "/bdrs", "Ver BDRs")

@app.route("/bdrs")
def bdrs():
    prov = carregar_proventos("investidor10_bdrs.txt")
    return gerar_html(prov, "Melhores BDRs (Data Com futura)", "/", "Voltar às Ações")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
