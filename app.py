from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from googletrans import Translator
from io import BytesIO
from flask_cors import CORS
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
translator = Translator()

@app.route('/extract', methods=['POST'])
def extract_pdf():
    try:
        if 'file' not in request.files:
            logger.warning("No file uploaded in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only PDF files are supported'}), 400
        
        logger.info(f"Processing PDF file: {file.filename}")
        pdf_bytes = file.read()
        
        if len(pdf_bytes) == 0:
            logger.warning("Empty PDF file uploaded")
            return jsonify({'error': 'Empty PDF file'}), 400
        
        reader = PdfReader(BytesIO(pdf_bytes))
        pages = []
        
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ''
                pages.append(text)
                logger.info(f"Extracted text from page {i+1}: {len(text)} characters")
            except Exception as e:
                logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                pages.append(f"[Error extracting page {i+1}]")
        
        logger.info(f"Successfully extracted {len(pages)} pages")
        return jsonify({
            'pages': pages, 
            'num_pages': len(pages),
            'total_chars': sum(len(page) for page in pages)
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in extract_pdf: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.json
        if not data:
            logger.warning("No JSON data provided")
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '')
        src = data.get('src', 'auto')
        dest = data.get('dest', 'vi')
        
        if not text:
            logger.warning("Empty text provided for translation")
            return jsonify({'error': 'No text provided'}), 400
        
        logger.info(f"Translating text from {src} to {dest}, length: {len(text)} characters")
        
        # Split long text into chunks to avoid API limits
        max_chunk_size = 5000  # Google Translate limit
        if len(text) > max_chunk_size:
            logger.info(f"Text too long ({len(text)} chars), splitting into chunks")
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    translated = translator.translate(chunk, src=src, dest=dest)
                    translated_chunks.append(translated.text)
                    logger.info(f"Translated chunk {i+1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Error translating chunk {i+1}: {str(e)}")
                    translated_chunks.append(f"[Translation error in chunk {i+1}]")
            
            final_text = ' '.join(translated_chunks)
        else:
            translated = translator.translate(text, src=src, dest=dest)
            final_text = translated.text
        
        logger.info(f"Translation completed successfully")
        return jsonify({'translated': final_text})
        
    except Exception as e:
        logger.error(f"Error in translate_text: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
def summarize_text():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        logger.info(f"Summarizing text of length: {len(text)} characters")
        
        # Simple summarization: take first 2 sentences or first 200 characters
        lines = text.split('\n')
        summary_lines = []
        char_count = 0
        
        for line in lines:
            if char_count >= 200:
                break
            if line.strip():
                summary_lines.append(line)
                char_count += len(line)
        
        summary = '\n'.join(summary_lines)
        if len(summary) < len(text):
            summary += "\n\n[Summary truncated...]"
        
        logger.info(f"Summary created: {len(summary)} characters")
        return jsonify({'summary': summary})
        
    except Exception as e:
        logger.error(f"Error in summarize_text: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'NZAOO PDF Translate API'})

if __name__ == '__main__':
    logger.info("Starting NZAOO PDF Translate API server...")
    app.run(host='0.0.0.0', port=10000, debug=True) 