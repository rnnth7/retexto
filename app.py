import random
from flask import Flask, render_template, request
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os
from datetime import date
import google.generativeai as genai
import markdown
from vars import *
from dotenv import load_dotenv
from utils import *
import tracemalloc

tracemalloc.start()

load_dotenv()
api = os.getenv('API_KEY')
genai.configure(api_key=api)

pytesseract.pytesseract.tesseract_cmd = "/app/.apt/usr/bin/tesseract"
POPPLER_PATH = "/app/.apt/usr/bin/"

frase = random.choice(citacoes)

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def index():
    resposta = None
    tipoSessao = None
    tipoProjeto = None
    autores = []

    if request.method == "POST":
        if 'pdf' not in request.files:
            return "Nenhum arquivo enviado", 400

        pdf = request.files['pdf']
        if pdf.filename == "":
            return "Nenhum arquivo enviado", 400

        tipoSessao = request.form.get('tipoSessao')
        tipoProjeto = request.form.get('tipoProjeto')

        autoria = request.form.getlist('autoria')
        if autoria == []:
            return "Autoria não escolhida", 400
        autores = autoriaFormatada(autoria)

        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf.save(temp_file.name)
        temp_file.close()  # Fechar arquivo para evitar erro de leitura

        # Converter PDF
        try:
            pdf_convertido = convert_from_path(temp_file.name, poppler_path="/usr/bin", dpi=100)
        except Exception as e:
            return f"Erro ao converter PDF: {e}", 500

        # Extrair texto de todas as páginas
        texto = ""
        for pagina in pdf_convertido:
            texto += pytesseract.image_to_string(pagina) + "\n"

        #Ver se é sessão ordinária ou solene
        if tipoSessao == "Sessão Solene":
            prompt = promptSolene
        else:
            prompt = promptOrdinaria

        # Criar a pergunta para o Gemini
        pergunta = (f"{prompt} a/o {tipoProjeto} foi aprovado(a) na {tipoSessao} de {date.today()}. Os autores foi/foram {autores}. O texto aprovado foi: {texto}.")

        # Gerar resposta com Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(pergunta)
        resposta = markdown.markdown(response.text) if hasattr(response, 'text') else "Erro ao gerar o texto"

        # Remover o arquivo temporário após o processamento
        os.unlink(temp_file.name)

    return render_template('index.html', resposta=resposta,frase=frase)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("filename")

    print("\n[ TOP 10 USO DE MEMÓRIA ]")
    for stat in top_stats[:10]:
        print(stat)
    return render_template('contato.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

