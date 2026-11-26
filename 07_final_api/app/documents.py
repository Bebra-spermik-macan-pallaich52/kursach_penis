from app.errors import log_error
from io import BytesIO
from docx import Document


def make_docx(title, event_title, text):
    try:
        document = Document()
        document.add_heading(title, 0)
        document.add_paragraph(event_title)
        document.add_paragraph(text)
        stream = BytesIO()
        document.save(stream)
        return stream.getvalue()
    except Exception as error:
        log_error(error, "make_docx")
        raise
