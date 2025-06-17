from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json

app = Flask(__name__)

def parse_data(data_str):
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try: return datetime.strptime(data_str.strip(), fmt)
        except: continue
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

def gerar_widget_top5(proventos):
    top = proventos[:5]
    syms = [{"proName": f"BMFBOVESPA:{p['ticker']}", "title": p['ticker']} for p in top]
    cfg = {
        "symbols": syms,
        "showSymbolLogo": True,
        "colorTheme": "light",
        "displayMode": "adaptive",
        "locale": "pt"
    }
    return f"""
    <div class="tradingview-widget-container mb-4">
      <div class="tradingview-widget-container__widget"></div>
      <script src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {json.dumps(cfg)}
      </script>
    </div>
    """

def gerar_html(provs, title, rota=None, texto=""):
    widget = gerar_widget_top5(provs) if provs else ""
    corpo = ""
    if not provs:
        corpo = "<div class='alert alert-warning'>Não existem opções!</div>"
    else:
        linhas = ""
        for i, p in enumerate(provs):
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i<5 else ""
            linhas += f"<tr><td>{p['ticker']}{selo}</td><td>{p['data_com']}</td><td>{p['pagamento']}</td><td>{p['tipo']}</td><td>{p['valor']}</td></tr>"
        corpo = (
          "<div class='table-responsive'><table class='table table-bordered table-hover'>"
          "<thead class='table-primary text-center'><tr>"
          "<th>Ticker</th><th>Data Com</th><th>Data Pgto</th><th>Tipo</th><th>Valor</th>"
          "</tr></thead><tbody>"
          +linhas+
          "</tbody></table></div>"
        )
    bot = f"<a href='{rota}' class='btn btn-outline-primary mb-3'>{texto}</a>" if rota else ""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br"><head><meta charset="utf-8">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="container py-3">
      {widget}
      <h1 class="text-center mb-4 text-primary">LEVERAGE IA</h1>
      <p class="text-center text-muted mb-3">{title}</p>
      <div class="text-center">{bot}</div>
      {corpo}
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
