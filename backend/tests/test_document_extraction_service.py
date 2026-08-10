from pathlib import Path

from app.services.document_extractor.service import DocumentExtractionService


def test_extracts_plain_text_from_txt(tmp_path: Path) -> None:
    sample = tmp_path / "notes.txt"
    sample.write_text("Hello\n\nWorld\n", encoding="utf-8")

    service = DocumentExtractionService()
    result = service.extract_text_from_path(sample)

    assert result.text.strip() == "Hello\nWorld"
    assert result.metadata["file_name"] == sample.name
