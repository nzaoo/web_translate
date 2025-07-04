import streamlit as st
import pdfplumber
from googletrans import Translator, LANGUAGES
from fpdf import FPDF
from docx import Document
import tempfile
import os

# Chuẩn hóa tên ngôn ngữ
LANG_CODE_TO_NAME = {code: name.title() for code, name in LANGUAGES.items()}
LANG_NAME_TO_CODE = {name.title(): code for code, name in LANGUAGES.items()}

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def translate_text(text, source, target):
    translator = Translator()
    lines = text.split('\n')
    translated_lines = []
    for line in lines:
        if line.strip():
            try:
                translated = translator.translate(line, src=source, dest=target)
                translated_lines.append(translated.text)
            except Exception as e:
                translated_lines.append(f"[Lỗi dịch: {e}]")
        else:
            translated_lines.append("")
    return '\n'.join(translated_lines)

def export_to_pdf(text, output_path):
    pdf_out = FPDF()
    pdf_out.add_page()
    pdf_out.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf_out.cell(0, 10, line, ln=True)
    pdf_out.output(output_path)

def export_to_word(text, output_path):
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    doc.save(output_path)

# Giao diện Streamlit
def main():
    st.set_page_config(page_title="Dịch PDF Đa Ngôn Ngữ", layout="wide")
    st.title("🌏 Dịch PDF Đa Ngôn Ngữ - Song Ngữ")

    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stTextArea textarea {
            font-size: 16px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])

    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        source_lang = st.selectbox("Ngôn ngữ gốc", sorted(LANG_NAME_TO_CODE.keys()), index=sorted(LANG_NAME_TO_CODE.keys()).index("English"))
    with col2:
        target_lang = st.selectbox("Dịch sang", sorted(LANG_NAME_TO_CODE.keys()), index=sorted(LANG_NAME_TO_CODE.keys()).index("Vietnamese"))
    with col3:
        output_type = st.radio("Định dạng xuất", ["PDF", "Word (.docx)"])

    output_filename = st.text_input("Tên file đầu ra", value="translated_output.pdf" if output_type=="PDF" else "translated_output.docx")

    if st.button("Dịch và Tải về", use_container_width=True) and uploaded_file:
        with st.spinner("Đang trích xuất và dịch..."):
            # Lưu file tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            # Trích xuất và dịch
            original_text = extract_text_from_pdf(tmp_path)
            if not original_text.strip():
                st.error("Không tìm thấy văn bản trong file PDF!")
            else:
                translated_text = translate_text(original_text, LANG_NAME_TO_CODE[source_lang], LANG_NAME_TO_CODE[target_lang])
                # Hiển thị song song
                st.subheader("So sánh nội dung")
                col_left, col_right = st.columns(2)
                with col_left:
                    st.text_area("Nội dung gốc", original_text, height=400)
                with col_right:
                    st.text_area("Nội dung đã dịch", translated_text, height=400)
                # Xuất file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if output_type=="PDF" else ".docx") as out_tmp:
                    if output_type == "PDF":
                        export_to_pdf(translated_text, out_tmp.name)
                    else:
                        export_to_word(translated_text, out_tmp.name)
                    out_tmp.flush()
                    st.success("Dịch thành công! Bấm để tải về:")
                    with open(out_tmp.name, "rb") as f:
                        st.download_button(
                            label="Tải file đã dịch",
                            data=f,
                            file_name=output_filename,
                            mime="application/pdf" if output_type=="PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            os.remove(tmp_path)

    elif st.button("Dịch và Tải về", use_container_width=True) and not uploaded_file:
        st.warning("Vui lòng chọn file PDF trước khi dịch.")

if __name__ == "__main__":
    main() 