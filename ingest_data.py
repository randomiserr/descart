import os
import json
import uuid
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Paths
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
OUTPUT_LAWS_PATH = os.path.join(BASE_DIR, 'data', 'laws_extracted.json')

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file."""
    if not PdfReader:
        print("Warning: pypdf not installed, skipping PDF.")
        return ""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Failed to read {pdf_path}: {e}")
        return ""

def extract_text_from_xml(xml_path: str) -> str:
    """Simple XML text extraction (naive)."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Extract all text recursively
        return "".join(root.itertext())
    except Exception as e:
        print(f"Failed to read XML {xml_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Simple text chunking by characters."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks

def process_files():
    """Reads files from data/raw (including ZIPs) and converts them to the laws JSON schema."""
    if not os.path.exists(RAW_DIR):
        print(f"Directory not found: {RAW_DIR}")
        return

    # 1. Handle ZIP files
    for item in os.listdir(RAW_DIR):
        if item.lower().endswith('.zip'):
            zip_path = os.path.join(RAW_DIR, item)
            print(f"Unzipping {item}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(RAW_DIR)
            except Exception as e:
                print(f"Failed to unzip {item}: {e}")

    # 2. Group files by basename to avoid duplicates
    file_groups = {}
    for root, dirs, files in os.walk(RAW_DIR):
        for filename in files:
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower().lstrip('.')
            if ext not in ['json', 'xml', 'pdf']:
                continue
            
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, RAW_DIR)
            
            # Key by directory + basename to handle same filenames in different folders
            key = os.path.join(os.path.relpath(root, RAW_DIR), base_name)
            
            if key not in file_groups:
                file_groups[key] = {}
            file_groups[key][ext] = full_path

    # 3. Process best format for each group
    extracted_data = []
    
    for key, formats in file_groups.items():
        # Priority: JSON > XML > PDF
        if 'json' in formats:
            filepath = formats['json']
            ext = 'json'
        elif 'xml' in formats:
            filepath = formats['xml']
            ext = 'xml'
        elif 'pdf' in formats:
            filepath = formats['pdf']
            ext = 'pdf'
        else:
            continue

        print(f"Processing {ext.upper()} for {key}...")
        
        content = ""
        try:
            if ext == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = json.dumps(data, ensure_ascii=False)
            elif ext == 'xml':
                content = extract_text_from_xml(filepath)
            elif ext == 'pdf':
                content = extract_text_from_pdf(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

        if not content:
            continue

        # Calculate relative path for source_document
        rel_path = os.path.relpath(filepath, RAW_DIR)
        
        # Use parent folder as a tag
        parent_folder = os.path.basename(os.path.dirname(filepath))
        tags = ["imported", ext]
        if parent_folder and parent_folder != 'raw':
            tags.append(parent_folder)

        # Chunk and add to dataset
        chunks = chunk_text(content)
        for chunk in chunks:
            entry = {
                "id": str(uuid.uuid4()),
                "source_document": rel_path,
                "content_chunk": chunk.strip(),
                "valid_from": "2024-01-01", 
                "valid_to": None,
                "domain_tags": tags
            }
            extracted_data.append(entry)

    # Save to JSON
    with open(OUTPUT_LAWS_PATH, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully extracted {len(extracted_data)} chunks to {OUTPUT_LAWS_PATH}")

if __name__ == "__main__":
    process_files()
