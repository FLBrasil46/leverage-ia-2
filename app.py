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
            valor = parse_valor(extrair_span(cols[3]))
            data_pgto = parse_data(pagamento_str)
            if data_pgto and data_pgto.date() > hoje:
                fiis.append({
                    "ticker": ticker,
                    "pagamento": pagamento_str,
                    "tipo": tipo,
                    "valor": f"R$ {valor:.2f}",
                    "valor_num": valor
                })

    return sorted(fiis, key=lambda x: -x["valor_num"])

def gerar_html_simples(lista, titulo, colunas, rota_oposta=None, texto_botao=None):
    if not lista:
        corpo = "<div class='alert alert-warning'>Não existem opções no momento!</div>"
    else:
        linhas = ""
        for i, item in enumerate(lista):
            destaque = "table-success fw-semibold" if i < 5 else ""
            selo = "<span class='badge bg-success ms-2'>TOP 5</span>" if i < 5 else ""
            linhas += f"<tr class='{destaque}'>"
            for campo in colunas:
                valor = item.get(campo, "")
                if campo == "ticker":
                    valor += selo
                linhas += f"<td>{valor}</td>"
            linhas += "</tr>"

        thead = "".join(f"<th>{c.title()}</th>" for c in colunas)
        corpo = (
            "<div class='table-responsive'>"
            "<table class='table table-bordered table-hover'>"
            f"<thead class='table-primary text-center'><tr>{thead}</tr></thead>"
            f"<tbody>{linhas}</tbody></table></div>"
        )

    botao = f"<a href='{rota_oposta}' class='btn btn-outline-primary mb-3'>{texto_botao}</a>" if rota_oposta else ""

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
      <meta charset="utf-8">
      <title>{titulo}</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container py-4">
      <h1 class='text-center text-primary mb-4'>LEVERAGE IA</h1>
      <p class='text-center text-muted'>{titulo}</p>
      <div class="text-center">{botao}</div>
      {corpo}
    </body>
    </html>
    """

@app.route("/")
def index():
    from_arquivo = carregar_proventos("investidor10_dividendos.txt")
    return gerar_html_simples(
        from_arquivo,
        "Melhores oportunidades do mercado brasileiro com Data Com futura",
        ["ticker", "data_com", "pagamento", "tipo", "valor"],
        "/bdrs", "Ver BDRs"
    )

@app.route("/bdrs")
def bdrs():
    from_arquivo = carregar_proventos("investidor10_bdrs.txt")
    return gerar_html_simples(
        from_arquivo,
        "BDRs em destaque com Data Com futura",
        ["ticker", "data_com", "pagamento", "tipo", "valor"],
        "/", "Voltar às Ações"
    )

@app.route("/fiis")
def fiis():
    fiis_data = carregar_fiis("melhoresfiis.txt")
    return gerar_html_simples(
        fiis_data,
        "Fundos Imobiliários com pagamentos futuros",
        ["ticker", "pagamento", "tipo", "valor"],
        "/", "Voltar às Ações"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
