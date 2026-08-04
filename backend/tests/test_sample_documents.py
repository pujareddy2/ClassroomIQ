import os
from app.services.text_preprocessor.service import TextPreprocessingService

def test_sample_documents():
    service = TextPreprocessingService()
    # Note: we are in the tests directory, so we need to go up one level to get to the base
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_dir = os.path.join(base_dir, 'tests', 'sample_documents', 'raw')
    expected_dir = os.path.join(base_dir, 'tests', 'sample_documents', 'expected_output')
    results_dir = os.path.join(base_dir, 'tests', 'sample_documents', 'results')
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Iterate over all files in raw directory
    for filename in os.listdir(raw_dir):
        if filename.endswith('.raw'):
            # Read raw content
            raw_path = os.path.join(raw_dir, filename)
            with open(raw_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            # Process
            processed_text = service.preprocess(raw_text)
            
            # Write to results
            result_filename = filename.replace('.raw', '.result')
            result_path = os.path.join(results_dir, result_filename)
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            # Read expected
            expected_filename = filename.replace('.raw', '.expected')
            expected_path = os.path.join(expected_dir, expected_filename)
            if not os.path.exists(expected_path):
                raise FileNotFoundError(f"Expected file not found: {expected_path}")
            with open(expected_path, 'r', encoding='utf-8') as f:
                expected_text = f.read()
            
            # Compare
            assert processed_text == expected_text, f"Mismatch for file {filename}"
            
    print(f"All {len(os.listdir(raw_dir))} samples passed.")

if __name__ == '__main__':
    test_sample_documents()
