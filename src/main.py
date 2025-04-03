# PUTTING IT ALL TOGETHER
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import os
from utils.querying_database import querying_faiss_database
from utils.load_and_chunk_documents import chunking_documents_local
from utils.chunk_to_embeddings import convert_chunk_into_embeddings, save_chunks_metadata
from utils.upload_local_database import add_to_faiss, inspect_faiss_database, is_file_processed, record_processed_file
import datetime
import numpy as np

def process_document(document_filepath, db_name="General"):
    """Process a new document and add it to the specified database"""
    # Check if file has already been processed
    is_processed, file_hash = is_file_processed(document_filepath, db_name)
    
    if is_processed:
        print(f"File {os.path.basename(document_filepath)} has already been processed in database '{db_name}'. Skipping...")
        return False
    
    # Get document filename
    filename = os.path.basename(document_filepath)
    print(f"Processing new document: {filename} for database '{db_name}'")
    
    # Load and chunk the document
    chunks = chunking_documents_local(document_filepath)
    
    # Add filename to chunk metadata
    for chunk in chunks:
        chunk.metadata['filename'] = filename
    
    # Create embeddings
    embeddings = convert_chunk_into_embeddings(chunks)
    
    # Add to FAISS index
    add_to_faiss(embeddings, db_name)
    
    # Save metadata (it will automatically append)
    save_chunks_metadata(chunks, db_name)
    
    # Record that this file has been processed
    record_processed_file(file_hash, document_filepath, db_name)
    
    # Show that function is done
    print(f"Document {filename} processed and added to database '{db_name}'!")
    return True

def process_text_input(text, title, db_name="General"):
    """Process text input and add it to the specified database"""
    from langchain.schema import Document
    
    # Create a Document object
    doc = Document(
        page_content=text,
        metadata={
            'page': 1,
            'source': 'user_input',
            'filename': f"{title}.txt"
        }
    )
    
    # Create embeddings
    embeddings = convert_chunk_into_embeddings([doc])
    
    # Debug print
    print(f"Generated embeddings with shape: {np.array(embeddings).shape}")
    
    # Add to FAISS index
    add_to_faiss(embeddings, db_name)
    
    # Save metadata
    save_chunks_metadata([doc], db_name)
    
    print(f"Text '{title}' processed and added to database '{db_name}'!")
    return True

if __name__ == "__main__":
    # Example use case
    process_document("uploaded_files/risk.pdf")
    response = querying_faiss_database("How do i win in risk?", "deepseek-r1:1.5b")
    print(response)