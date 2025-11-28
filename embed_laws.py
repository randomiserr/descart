import os
import json
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LAWS_PATH = os.path.join(DATA_DIR, 'laws_extracted.json')
DB_PATH = os.path.join(DATA_DIR, 'vectordb')

def embed_laws():
    print("Initializing Vector DB...")
    
    # Ensure data directory exists
    if not os.path.exists(LAWS_PATH):
        print(f"Error: {LAWS_PATH} not found.")
        return

    # Load Laws
    with open(LAWS_PATH, 'r', encoding='utf-8') as f:
        laws = json.load(f)
    
    print(f"Loaded {len(laws)} law chunks.")

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Use a standard embedding model
    # We can use the built-in one or specify sentence-transformers
    # Using the default all-MiniLM-L6-v2 is good for general purpose
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(
        name="laws_collection",
        embedding_function=ef
    )
    
    print("Generating embeddings and indexing...")
    
    ids = []
    documents = []
    metadatas = []
    
    for i, law in enumerate(laws):
        # Create a unique ID if not present
        doc_id = law.get('id', f"law_{i}")
        
        # Prepare metadata (flat dict)
        meta = {
            "source_document": law.get('source_document', 'unknown'),
            "valid_from": law.get('valid_from', ''),
            "domain_tags": ",".join(law.get('domain_tags', []))
        }
        
        ids.append(doc_id)
        documents.append(law.get('content_chunk', ''))
        metadatas.append(meta)
        
        # Batch add every 100 items
        if len(ids) >= 100:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            print(f"Indexed {i+1}/{len(laws)}...")
            ids = []
            documents = []
            metadatas = []
            
    # Add remaining
    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"Indexed {len(laws)}/{len(laws)}...")

    print(f"Success! Vector DB saved to {DB_PATH}")

if __name__ == "__main__":
    embed_laws()
