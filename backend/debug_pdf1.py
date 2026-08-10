from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber

# Test with the first PDF file that wasn't working
pdf_path = Path("../uploads/science/2023-2024/6/syllabus/joining_report.pdf")
print(f"PDF file exists: {pdf_path.exists()}")
print(f"PDF file size: {pdf_path.stat().st_size} bytes")

# Try PyMuPDF directly
print("\n--- Trying PyMuPDF ---")
try:
    document = fitz.open(pdf_path)
    print(f"Number of pages: {document.page_count}")
    parts = []
    total_chars = 0
    for page_num in range(document.page_count):
        page = document[page_num]
        text = page.get_text()
        print(f"Page {page_num+1}: {len(text)} characters")
        total_chars += len(text)
        if text.strip():
            parts.append(text)
        else:
            print(f"  Page {page_num+1} is empty or whitespace only")
    document.close()
    text = "\n\n".join(part for part in parts if part)
    print(f"Total extracted text length: {len(text)}")
    print(f"Total characters from all pages: {total_chars}")
    if text:
        print(f"First 200 chars: {repr(text[:200])}")
    else:
        print("No text extracted")
except Exception as e:
    print(f"Error with PyMuPDF: {e}")
    import traceback
    traceback.print_exc()

# Try pdfplumber directly
print("\n--- Trying pdfplumber ---")
try:
    with pdfplumber.open(pdf_path) as document:
        print(f"Number of pages: {len(document.pages)}")
        parts = []
        total_chars = 0
        for page_num, page in enumerate(document.pages):
            text = page.extract_text() or ""
            print(f"Page {page_num+1}: {len(text)} characters")
            total_chars += len(text)
            if text.strip():
                parts.append(text)
            else:
                print(f"  Page {page_num+1} is empty or whitespace only")
        text = "\n\n".join(part for part in parts if part)
        print(f"Total extracted text length: {len(text)}")
        print(f"Total characters from all pages: {total_chars}")
        if text:
            print(f"First 200 chars: {repr(text[:200])}")
        else:
            print("No text extracted")
except Exception as e:
    print(f"Error with pdfplumber: {e}")
    import traceback
    traceback.print_exc()
