from pathlib import Path
from app.services.document_extractor.pdf_extractor import PdfExtractor

# Test with a PDF file
pdf_path = Path("../uploads/science/2023-2024/6/syllabus/joining_report.pdf")
print(f"PDF file exists: {pdf_path.exists()}")
print(f"PDF file size: {pdf_path.stat().st_size} bytes")

extractor = PdfExtractor()
try:
    text, library_used = extractor.extract(pdf_path)
    print(f"Extracted text length: {len(text)}")
    print(f"Library used: {library_used}")
    print(f"First 200 chars: {repr(text[:200])}")
except Exception as e:
    print(f"Error extracting PDF: {e}")
    import traceback
    traceback.print_exc()
