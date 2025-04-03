import os
from pathlib import Path
import logging
from utils.load_and_chunk_documents import chunking_documents_local
from utils.chunk_to_embeddings import convert_chunk_into_embeddings, save_chunks_metadata
from utils.upload_local_database import add_to_faiss, is_file_processed

def process_documents(file_path: str, db_name: str = "General") -> bool:
    """
    Process a document by:
    1. Converting it to chunks
    2. Creating embeddings
    3. Adding to FAISS database
    
    Args:
        file_path (str): Path to the document to process
        db_name (str): Name of the database to use (default: "General")
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return False

        # Check if file has already been processed
        is_processed, _ = is_file_processed(file_path, db_name)
        if is_processed:
            print(f"File already processed: {file_path}")
            return True

        # Step 1: Create chunks from the document
        print(f"Creating chunks from {file_path}")
        chunks = chunking_documents_local(file_path)
        if not chunks:
            print(f"ERROR: No chunks created from {file_path}")
            return False

        # Step 2: Convert chunks to embeddings
        print("Converting chunks to embeddings")
        embeddings_list = convert_chunk_into_embeddings(chunks)
        if not embeddings_list:
            print("ERROR: Failed to create embeddings")
            return False

        # Save chunks metadata for future reference
        save_chunks_metadata(chunks, file_path, db_name)

        # Step 3: Add embeddings to FAISS database
        print(f"Adding embeddings to FAISS database: {db_name}")
        success = add_to_faiss(embeddings_list, chunks, db_name)
        
        if success:
            print(f"Successfully processed {file_path}")
            return True
        else:
            print(f"ERROR: Failed to add embeddings to database for {file_path}")
            return False

    except Exception as e:
        print(f"ERROR: Error processing document {file_path}: {str(e)}")
        return False

def process_directory(directory_path: str, db_name: str = "General") -> bool:
    """
    Process all PDF files in a directory
    
    Args:
        directory_path (str): Path to directory containing documents
        db_name (str): Name of the database to use (default: "General")
        
    Returns:
        bool: True if all files were processed successfully, False if any failed
    """
    try:
        success = True
        directory = Path(directory_path)
        
        # Process all PDF files in directory
        for file_path in directory.glob('*.pdf'):
            file_success = process_documents(str(file_path), db_name)
            if not file_success:
                logging.warning(f"Failed to process {file_path}")
                success = False
                
        return success
    
    except Exception as e:
        logging.error(f"Error processing directory {directory_path}: {str(e)}")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    # success = process_documents("path/to/your/document.pdf")
    # print(f"Processing successful: {success}")
