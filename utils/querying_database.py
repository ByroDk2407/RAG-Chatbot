# Step Four

# Importing Dependencies
import subprocess
import json
from transformers import AutoTokenizer, AutoModel
import torch
import sys
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import logging
import os

# Initialising Vector Database (Pinecone)
from pinecone import Pinecone

# Imports for API Keys
from dotenv import load_dotenv

# Intiialising Pinecone Vector Database
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("legal-index")

# Defining embedding model
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

load_dotenv()

def format_source_reference(filename, page_number):
    return f'Source: {filename} (Page {page_number})'

def querying_faiss_database(query, model_name, db_name="General", top_k=3):
    """
    Queries the FAISS database with a user-provided query text.
    Finds the most similar embeddings stored in the index.
    """
    print(f"Starting query for database {db_name}")
    
    faiss_index_path = f"data/databases/{db_name}/faiss_index.idx"
    metadata_path = f"data/databases/{db_name}/chunk_metadata.json"
    
    # Check if database exists
    if not os.path.exists(faiss_index_path) or not os.path.exists(metadata_path):
        print(f"Database files not found at {faiss_index_path}")
        return f"Database '{db_name}' not found or empty. Please add documents first."
    
    try:
        # Load FAISS index
        print("Loading FAISS index")
        index = faiss.read_index(faiss_index_path)
        
        # Load metadata
        print("Loading metadata")
        with open(metadata_path, 'r') as f:
            chunk_metadata = json.load(f)
        
        # Initialize the model - ensure it matches the one used for creating embeddings
        print("Initializing embedder")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate query embedding
        print("Generating query embedding")
        query_embedding = embedder.encode([query])[0]  # Get first element since we're encoding a single query
        query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
        
        # Verify dimensions match
        if query_embedding.shape[1] != index.d:
            raise ValueError(f"Query embedding dimension ({query_embedding.shape[1]}) does not match index dimension ({index.d})")
        
        # Search the index
        print("Searching index")
        distances, indices = index.search(query_embedding, min(top_k, index.ntotal))
        
        # Format results
        print("Formatting results")
        results = []
        for i in range(len(indices[0])):
            idx = str(indices[0][i])
            if idx in chunk_metadata:
                score = 1 - float(distances[0][i])
                metadata = chunk_metadata[idx]['metadata']
                text = chunk_metadata[idx]['text']
                results.append({
                    'score': score,
                    'page_number': metadata.get('page_number', 'unknown'),
                    'source': metadata.get('filename', 'unknown'),
                    'text': text
                })
        
        if not results:
            return "No relevant information found in the database."
        
        # Format results for Ollama
        formatted_results = "\n\n".join([
            f"Score: {r['score']:.2f}\n"
            f"Page Number: {r['page_number']}\n"
            f"Source: {r['source']}\n"
            f"Text: {r['text']}"
            for r in results
        ])
        
        # Create prompt for Ollama with explicit formatting instructions
        prompt = f"""
        Query: {query}

        Relevant Information:
        {formatted_results}

        Please provide a clear and concise answer to the query using the following formatting:
        - Use **bold** for important terms or key points
        - Use *italics* for emphasis
        - Use `code` for technical terms or specific instructions
        - Use proper line breaks for readability
        - Include source documents and page numbers in your response

        Also please include the source (i.e. file name) document and page number in your response.
        
        Format your response like this example:
        Based on the documentation, the **key steps** are:
        1. First, ensure the *safety protocols* are followed
        2. Use the `power button` to activate the system
        
        

        Now provide your response:
        """
        
        # Use Ollama to generate response
        print("Generating response with Ollama")
        process = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        
        # Check for errors
        if process.returncode != 0:
            print(f"Error from Ollama: {process.stderr}")
            return "Error generating response from the model."
        
        print("Successfully generated response")
        
        # When adding source to the response
        source_text = format_source_reference(results[0]['source'], results[0]['page_number'])
        response = process.stdout.strip() + f"\n\n{source_text}"
        
        return response
        
    except Exception as e:
        print(f"Error in querying_faiss_database: {str(e)}")
        raise

if __name__ == "__main__":
    # Test the function
    try:
        response = querying_faiss_database(
            query="What is the main purpose of this document?",
            model_name="deepseek-r1",
            db_name="General"
        )
        print("Response:", response)
    except Exception as e:
        print("Error:", str(e))