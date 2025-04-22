import os
import json
from pathlib import Path
from typing import List, Dict, Any

def load_filings(directory_path: str) -> List[Dict[str, Any]]:
    """Load SEC 8-K filings and create a dataset with filename and text keys."""
    filings_data = []
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory {directory_path} does not exist or is not a directory")
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                
                filing_entry = {
                    "filename": file_path.name,
                    "text": text
                }
                
                filings_data.append(filing_entry)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
    
    return filings_data

def save_to_json(data: List[Dict[str, Any]], output_file: str) -> None:
    """Save data to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main() -> None:
    input_directory = "sec-8ks/sec_8k_filings"
    output_file = "sec-8ks/sec_8k_dataset.json"
    
    filings_data = load_filings(input_directory)
    save_to_json(filings_data, output_file)
    
    print(f"Processed {len(filings_data)} filings and saved to {output_file}")

if __name__ == "__main__":
    main()
