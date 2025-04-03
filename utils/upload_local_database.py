# Step Three


import faiss
import numpy as np
import sqlite3
import hashlib
import json
import os
import datetime
import shutil

# Initialize SQLite for tracking duplicates
conn = sqlite3.connect("embeddings_cache.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS embeddings (hash TEXT PRIMARY KEY)")
conn.commit()

def compute_hash(text):
    """Compute a hash for the text content"""
    return hashlib.md5(text.encode()).hexdigest()

def is_duplicate(text, metadata):
    """Check if the text content is already in the database"""
    text_hash = compute_hash(text)
    for chunk_data in metadata.values():
        if compute_hash(chunk_data['text']) == text_hash:
            return True
    return False

# Initialize FAISS index
embedding_size = 384  # Match your model output dimension
index = faiss.IndexFlatL2(embedding_size)  # L2 distance for similarity search

# Example function to add vectors
def add_to_faiss(embeddings_list, chunks=None, db_name="General"):
    """
    Add embeddings to FAISS index
    
    Args:
        embeddings_list: List of embeddings to add
        chunks: Optional list of document chunks (for metadata)
        db_name: Name of the database to use (default: "General")
    """
    try:
        # Convert embeddings to numpy array
        embeddings = np.array(embeddings_list).astype('float32')
        
        # Create database directory if it doesn't exist
        os.makedirs(f"data/databases/{db_name}", exist_ok=True)
        
        # Path to the FAISS index
        index_path = f"data/databases/{db_name}/faiss_index.idx"
        
        # Load or create index
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
        else:
            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        index.add(embeddings)
        
        # Save the updated index
        faiss.write_index(index, index_path)
        
        print(f"Successfully added {len(embeddings)} embeddings to FAISS index")
        return True
        
    except Exception as e:
        print(f"Error in add_to_faiss: {str(e)}")
        return False


# Function to inspect the database
def inspect_faiss_database(db_name="General"):
    """Print information about the FAISS database"""
    faiss_index_path = f"data/databases/{db_name}/faiss_index.idx"
    metadata_path = f"data/databases/{db_name}/chunk_metadata.json"
    
    try:
        # Load FAISS index
        index = faiss.read_index(faiss_index_path)
        print(f"\nFAISS Index Statistics for '{db_name}':")
        print(f"Total vectors: {index.ntotal}")
        print(f"Dimension: {index.d}")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Count documents by source
        sources = {}
        for chunk_data in metadata.values():
            filename = chunk_data['metadata']['filename']
            sources[filename] = sources.get(filename, 0) + 1
        
        print("\nDocuments in database:")
        for filename, chunk_count in sources.items():
            print(f"- {filename}: {chunk_count} chunks")
            
        return {
            "total_vectors": index.ntotal,
            "dimension": index.d,
            "documents": sources
        }
            
    except Exception as e:
        print(f"Error inspecting database: {str(e)}")
        return None

def get_file_hash(filepath):
    """Generate a hash of the file content to uniquely identify it"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def is_file_processed(file_path, db_name="General"):
    """Check if a file has already been processed"""
    metadata_path = f"data/databases/{db_name}/chunk_metadata.json"
    if not os.path.exists(metadata_path):
        return False, {}
        
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    # Check if file exists in any chunk's metadata
    for chunk_data in metadata.values():
        if chunk_data['metadata']['source'] == file_path:
            return True, metadata
            
    return False, metadata

def record_processed_file(file_hash, filepath, db_name="General"):
    """Record a processed file in the tracking system"""
    processed_files_path = f"data/databases/{db_name}/processed_files.json"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(processed_files_path), exist_ok=True)
    
    # Load existing processed files or create new record
    if os.path.exists(processed_files_path):
        with open(processed_files_path, 'r') as f:
            processed_files = json.load(f)
    else:
        processed_files = {}
    
    # Add file to processed files
    filename = os.path.basename(filepath)
    processed_files[file_hash] = {
        'filename': filename,
        'path': filepath,
        'date_processed': datetime.datetime.now().isoformat()
    }
    
    # Save updated processed files
    with open(processed_files_path, 'w') as f:
        json.dump(processed_files, f, indent=2)

def get_available_databases():
    """Get list of available databases"""
    db_root = "data/databases"
    os.makedirs(db_root, exist_ok=True)
    
    # If no databases exist, create default ones
    databases = [d for d in os.listdir(db_root) if os.path.isdir(os.path.join(db_root, d))]
    if not databases:
        create_database("General")
        databases = ["General"]
    
    return databases

def create_database(db_name):
    """Create a new database with the given name"""
    db_path = f"data/databases/{db_name}"
    os.makedirs(db_path, exist_ok=True)
    
    # Use the same dimension as your embedding model
    # For all-MiniLM-L6-v2, dimension is 384
    dimension = 384  # Changed from 768 to 384
    index = faiss.IndexFlatL2(dimension)
    faiss.write_index(index, f"{db_path}/faiss_index.idx")
    
    # Create empty metadata file
    with open(f"{db_path}/chunk_metadata.json", "w") as f:
        json.dump({}, f)
    
    # Create empty processed files record
    with open(f"{db_path}/processed_files.json", "w") as f:
        json.dump({}, f)
    
    return db_name

def reset_database(db_name):
    """Reset a database to empty state"""
    db_path = f"data/databases/{db_name}"
    
    # Check if database exists
    if not os.path.exists(db_path):
        return False
    
    # Use the same dimension as your embedding model
    dimension = 384  # Changed from 768 to 384
    index = faiss.IndexFlatL2(dimension)
    faiss.write_index(index, f"{db_path}/faiss_index.idx")
    
    # Reset metadata file
    with open(f"{db_path}/chunk_metadata.json", "w") as f:
        json.dump({}, f)
    
    # Reset processed files record
    with open(f"{db_path}/processed_files.json", "w") as f:
        json.dump({}, f)
    
    return True

def delete_file_from_database(filename, db_name):
    """Delete a file and its chunks from a database"""
    try:
        metadata_path = f"data/databases/{db_name}/chunk_metadata.json"
        index_path = f"data/databases/{db_name}/faiss_index.idx"
        
        # Load existing metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        # Find chunks to remove
        chunks_to_remove = []
        new_metadata = {}
        
        for chunk_id, chunk_data in metadata.items():
            if chunk_data['metadata']['filename'] == filename:
                chunks_to_remove.append(int(chunk_id))
            else:
                new_metadata[chunk_id] = chunk_data
                
        if not chunks_to_remove:
            return False
            
        # Load and update FAISS index
        index = faiss.read_index(index_path)
        
        # Create a mask for keeping vectors
        keep_mask = np.ones(index.ntotal, dtype=bool)
        for chunk_id in chunks_to_remove:
            keep_mask[chunk_id] = False
            
        # Extract vectors to keep
        vectors = []
        for i in range(index.ntotal):
            if keep_mask[i]:
                vector = index.reconstruct(i)
                vectors.append(vector)
                
        # Create new index
        dimension = index.d
        new_index = faiss.IndexFlatL2(dimension)
        if vectors:
            new_index.add(np.array(vectors))
            
        # Save updated index and metadata
        faiss.write_index(new_index, index_path)
        with open(metadata_path, 'w') as f:
            json.dump(new_metadata, f, indent=2)
            
        return True
        
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return False

def delete_database(db_name):
    """Delete an entire database"""
    try:
        if db_name == "General":
            return False
            
        db_path = f"data/databases/{db_name}"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        return True
        
    except Exception as e:
        print(f"Error deleting database: {str(e)}")
        return False
