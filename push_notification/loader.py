from PyPDF2 import PdfReader

def load_resume(pdf_path="resume.pdf"):
    reader = PdfReader(pdf_path)
    text_content = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_content += text
    return text_content


def load_summary(file_path="summary.txt"):
    with open(file_path, "r") as f:
        return f.read()
