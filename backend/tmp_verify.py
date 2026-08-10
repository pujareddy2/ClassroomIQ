from pathlib import Path
from app.services.document_extractor.service import DocumentExtractionService
p = Path('tmp_sample.txt')
p.write_text('Hello\n\nWorld\n', encoding='utf-8')
service = DocumentExtractionService()
result = service.extract_text_from_path(p)
print('TEXT:', result.text)
print('METADATA:', result.metadata)
p.unlink(missing_ok=True)
