from pathlib import Path
import pytest

# Import the service from the correct location
import sys
sys.path.append('..')

from app.services.document_extractor.service import DocumentExtractionService


def test_extracts_text_from_pdf():
    # Use an existing PDF from the uploads directory
    pdf_path = Path("../uploads/science/2023-2024/6/syllabus/UML_Diagrams_All_Systems.pdf")
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF file not found: {pdf_path}")

    service = DocumentExtractionService(db=None)  # Don't update the database in the test
    result = service.extract_text_from_path(pdf_path)
    
    # Check that we got some text
    assert result.text.strip() != "", "Extracted text should not be empty"
    # Check metadata
    assert result.metadata["file_name"] == pdf_path.name
    assert result.metadata["document_type"] == "pdf"
    assert result.metadata["library_used"] in ("pymupdf", "pdfplumber")
    assert result.metadata["character_count"] > 0
    assert result.metadata["word_count"] > 0


def test_extracts_text_from_docx():
    # Use an existing DOCX from the uploads directory
    docx_path = Path("../uploads/science/2023-2024/6/syllabus/UNIT_II_BUSINESS_IDEAS_AND_OPPORTUNITY_IDENTIFICATION.docx")
    if not docx_path.exists():
        pytest.skip(f"Sample DOCX file not found: {docx_path}")

    service = DocumentExtractionService(db=None)
    result = service.extract_text_from_path(docx_path)
    
    # Check that we got some text
    assert result.text.strip() != "", "Extracted text should not be empty"
    # Check metadata
    assert result.metadata["file_name"] == docx_path.name
    assert result.metadata["document_type"] == "docx"
    assert result.metadata["library_used"] == "python-docx"  # We don't have a fallback for docx
    assert result.metadata["character_count"] > 0
    assert result.metadata["word_count"] > 0


def test_extracts_text_from_txt(tmp_path: Path):
    # Test with a temporary TXT file
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Hello\nWorld\n", encoding="utf-8")

    service = DocumentExtractionService(db=None)
    result = service.extract_text_from_path(txt_path)
    
    # The text cleaner will normalize the newlines
    assert result.text.strip() == "Hello\nWorld"
    assert result.metadata["file_name"] == txt_path.name
    assert result.metadata["document_type"] == "txt"
    # We don't have a specific library for txt, so it uses the default
    assert result.metadata["library_used"] == "default"
    assert result.metadata["character_count"] == len("Hello\nWorld")
    assert result.metadata["word_count"] == 2


def test_extracts_text_from_pptx():
    # We don't have a PPTX file in the uploads, so we skip this test for now.
    pytest.skip("No PPTX file available for testing")
    
    # If we had a PPTX file, we would do:
    # pptx_path = Path("path/to/file.pptx")
    # assert pptx_path.exists()
    # service = DocumentExtractionService(db=None)
    # result = service.extract_text_from_path(pptx_path)
    # assert result.text.strip() != ""
    # assert result.metadata["file_name"] == pptx_path.name
    # assert result.metadata["document_type"] == "pptx"
    # assert result.metadata["library_used"] == "python-pptx"
