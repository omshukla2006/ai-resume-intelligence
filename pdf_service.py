from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or '')
    text = '\n'.join(pages).strip()
    if not text:
        raise ValueError('No readable text was found in the PDF. If this is a scanned resume, upload a text-based PDF.')
    return text
