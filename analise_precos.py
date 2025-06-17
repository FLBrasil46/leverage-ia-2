from flask import Flask, render_template_string, request

app = Flask(__name__)

def obter_precos_alvo(ticker):
    dados = {
        "BBAS3": [
            {"fonte": "XP", "preco_alvo": 41.0, "data": "2025"},
            {"fonte": "BTG", "preco_alvo": 35.0, "data": "2025"},
        ]
    }
    return dados.get(ticker.upper(), [])

def calcular_media(valores):
    precos = [v["preco_alvo"] for v in valores]
    return round(sum(precos) / len(precos), 2) if precos else 0.0

TEMPLATE = """
<h1>Consulta Preço-Alvo</h1>
<form method="get">
  <input name="ticker" required>
  <button type="submit">Buscar</button>
</form>
{% if resultados %}
  <table border="1">
    <tr><th>Fonte</th><th>Preço-Alvo</th><th>Data</th></tr>
    {% for r in resultados %}
      <tr><td>{{ r.fonte }}</td><td>{{ r.preco_alvo }}</td><td>{{ r.data }}</td></tr>
    {% endfor %}
  </table>
  <p><b>Média:</b> {{ media }}</p>
{% endif %}
"""

@app.route("/", methods=["GET"])
def index():
    ticker = request.args.get("ticker", "").strip()
    resultados = obter_precos_alvo(ticker) if ticker else []
    media = calcular_media(resultados) if resultados else 0.0
    return render_template_string(TEMPLATE, ticker=ticker, resultados=resultados, media=media)
