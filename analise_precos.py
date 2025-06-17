from flask import Flask, render_template_string, request

app = Flask(__name__)

def obter_precos_alvo(ticker):
    # Dados simulados para demonstração — substitua por scraping ou API real
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
        # Pode adicionar outros tickers aqui
    }
    return dados.get(ticker.upper(), [])

def calcular_media(valores):
    precos = [item["preco_alvo"] for item in valores if item["preco_alvo"]]
    return round(sum(precos) / len(precos), 2) if precos else 0.0

TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Preço-Alvo de Ações</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        input[type=text] { padding: 6px; width: 150px; }
        button { padding: 6px 12px; }
    </style>
</head>
<body>
    <h1>Consulta de Preço-Alvo</h1>
    <form method="get">
        <label for="ticker">Digite o Ticker:</label>
        <input type="text" name="ticker" id="ticker" required value="{{ ticker }}">
        <button type="submit">Buscar</button>
    </form>

    {% if resultados %}
        <h2>Resultados para {{ ticker.upper() }}</h2>
        <table>
            <tr>
                <th>Fonte</th>
                <th>Preço-Alvo (R$)</th>
                <th>Data</th>
            </tr>
            {% for item in resultados %}
            <tr>
                <td>{{ item.fonte }}</td>
                <td>R$ {{ '%.2f'|format(item.preco_alvo) }}</td>
                <td>{{ item.data }}</td>
            </tr>
            {% endfor %}
            <tr>
                <td colspan="3"><strong>Média: R$ {{ media }}</strong></td>
            </tr>
        </table>
    {% elif ticker %}
        <p><em>Nenhum dado encontrado para o ticker informado.</em></p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    ticker = request.args.get("ticker", "").strip()
    resultados = obter_precos_alvo(ticker) if ticker else []
    media = calcular_media(resultados) if resultados else 0.0
    return render_template_string(TEMPLATE, ticker=ticker, resultados=resultados, media=media)

if __name__ == "__main__":
    app.run(debug=True)
