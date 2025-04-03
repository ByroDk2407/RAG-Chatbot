# 2. Step Two


from transformers import AutoTokenizer, AutoModel
import torch
import sys
import numpy as np
import faiss
import json
import os
from sentence_transformers import SentenceTransformer

# Calling in Chunking Functions
from utils.load_and_chunk_documents import chunking_documents_local
from utils.upload_local_database import is_duplicate, compute_hash, add_to_faiss

# Initialising Vector Database (Pinecone)
from pinecone import Pinecone

# Imports for API Keys
from dotenv import load_dotenv

# Intiialising Pinecone Vector Database
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("subsystem-document-index")


def convert_chunk_into_embeddings(chunks):
    """
    Convert document chunks into embeddings
    """
    try:
        # Initialize the model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create embeddings
        embeddings = []
        for chunk in chunks:
            # Ensure metadata values are the correct type
            if 'page' in chunk.metadata:
                chunk.metadata['page'] = int(str(chunk.metadata['page']).replace('page_', '').strip())
            if 'page_number' in chunk.metadata:
                chunk.metadata['page_number'] = int(str(chunk.metadata['page_number']).strip())
                
            embedding = model.encode(chunk.page_content)
            embeddings.append(embedding)
            
        return embeddings
        
    except Exception as e:
        print(f"Error in convert_chunk_into_embeddings: {str(e)}")
        return None


def save_chunks_metadata(chunks, file_path, db_name):
    """
    Save chunk metadata to a JSON file
    """
    try:
        # Create metadata directory if it doesn't exist
        os.makedirs(f"data/databases/{db_name}", exist_ok=True)
        
        metadata_path = f"data/databases/{db_name}/chunk_metadata.json"
        
        # Load existing metadata if it exists
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Add new chunks metadata
        for i, chunk in enumerate(chunks):
            # Clean and validate metadata
            clean_metadata = {
                'text': chunk.page_content,
                'metadata': {
                    'filename': os.path.basename(file_path),
                    'page_number': int(str(chunk.metadata.get('page_number', 0)).strip()),
                    'source': file_path
                }
            }
            metadata[str(len(metadata) + i)] = clean_metadata
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    except Exception as e:
        print(f"Error in save_chunks_metadata: {str(e)}")

if __name__ == "__main__":
    # Example use case (OLD)
    chunk_data = chunking_documents_local(document_filepath="uploaded_files/mh5.pdf")
    embeddings = convert_chunk_into_embeddings(chunk_data)

    print(f"Embeddings shape: {np.array(embeddings).shape}")
    embeddings = np.array(embeddings, dtype=np.float32)
    print(f"Embeddings array shape: {embeddings.shape}")
    add_to_faiss(embeddings)
    print(embeddings)
    print("Added to FAISS!")

    # After creating your embeddings
    dimension = len(embeddings[0])  # Get dimension of your embeddings
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # Save the index
    faiss.write_index(index, "data/faiss_index.idx")

    # Save metadata
    save_chunks_metadata(chunk_data, "mh5.pdf", "General")
