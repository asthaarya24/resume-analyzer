from PyPDF2 import PdfReader


def extract_text_from_pdf(file_stream):
    """Extract and clean all text from a PDF stream."""
    text = ""
    try:
        reader = PdfReader(file_stream)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
        text = " ".join(text.split()).strip()
        print(f"      Pages: {len(reader.pages)} | Chars: {len(text)}")
        return text
    except Exception as e:
        print(f"      PDF error: {e}")
        return ""
