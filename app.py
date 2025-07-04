from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from googletrans import Translator
from io import BytesIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
translator = Translator()

@app.route('/extract', methods=['POST'])
def extract_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    pdf_bytes = file.read()
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ''
        pages.append(text)
    return jsonify({'pages': pages, 'num_pages': len(pages)})

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.json
    text = data.get('text', '')
    src = data.get('src', 'auto')
    dest = data.get('dest', 'vi')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        translated = translator.translate(text, src=src, dest=dest)
        return jsonify({'translated': translated.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.json
    text = data.get('text', '')
    # Demo: chỉ trả về 1-2 câu đầu làm tóm tắt
    summary = '\n'.join(text.split('\n')[:2])
    return jsonify({'summary': summary})

if __name__ == '__main__':
    app.run(debug=True) 