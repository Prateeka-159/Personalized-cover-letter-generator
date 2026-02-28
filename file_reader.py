import docx
import PyPDF2
import numpy as np
from PIL import Image
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR

# Initialize PaddleOCR once (important)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text_with_ocr(image_array):
    result = ocr.ocr(image_array)

    extracted_text = ""

    if result:
        for line in result:
            if line:
                for word_info in line:
                    extracted_text += word_info[1][0] + "\n"

    return extracted_text


def read_file(uploaded_file):

    file_type = uploaded_file.type

    # -------- TXT --------
    if file_type == "text/plain":
        return uploaded_file.read().decode("utf-8")

    # -------- DOCX --------
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])

    # -------- PDF --------
    elif file_type == "application/pdf":

        # Try normal PDF extraction first
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        extracted_text = ""

        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text

        # If PDF contains selectable text, return it
        if extracted_text.strip():
            return extracted_text

        # Otherwise use OCR for scanned PDF
        uploaded_file.seek(0)
        images = convert_from_bytes(uploaded_file.read())

        ocr_text = ""
        for image in images:
            image_array = np.array(image)
            ocr_text += extract_text_with_ocr(image_array)

        return ocr_text

    # -------- IMAGE FILES --------
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        image = Image.open(uploaded_file)
        image_array = np.array(image)
        return extract_text_with_ocr(image_array)

    else:
        return "Unsupported file type."
