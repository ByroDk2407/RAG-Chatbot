# 1. Step One

from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from dotenv import load_dotenv
import os
load_dotenv()

import logging

#DATA_PATH = "data"
#DATA_PATH = "../mh5.pdf"
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')



# CURRENTLY BEING USED
def chunking_documents_local(file_path):
    """
    Load and chunk a document (PDF or TXT)
    """
    try:
        # Determine file type and use appropriate loader
        if file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
        elif file_path.lower().endswith('.txt'):
            loader = TextLoader(file_path)
            # TextLoader loads the entire file as one document
            document = loader.load()[0]
            # Create a page-like structure for consistency
            pages = [Document(
                page_content=document.page_content,
                metadata={'source': file_path, 'page': 1}
            )]
        else:
            print(f"Unsupported file type: {file_path}")
            return None
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Split documents and ensure page numbers are integers
        chunks = text_splitter.split_documents(pages)
        
        # Ensure page numbers are integers
        for chunk in chunks:
            if 'page' in chunk.metadata:
                try:
                    chunk.metadata['page'] = int(chunk.metadata['page'])
                except (ValueError, TypeError):
                    chunk.metadata['page'] = 1  # Default to page 1 for text files
            
            # Add page_number if not present
            if 'page_number' not in chunk.metadata:
                chunk.metadata['page_number'] = chunk.metadata.get('page', 1)
        
        print(f"Created {len(chunks)} chunks from {file_path}")
        return chunks
        
    except Exception as e:
        print(f"Error in chunking_documents_local: {str(e)}")
        return None



# Example use case
if __name__ == "__main__":
    # Example use case
    chunks = chunking_documents_local(file_path="data/mh5.pdf")
    print(len(chunks))
    for i, chunk in enumerate(chunks[:8]):
        print(f"Chunk {i + 1}:\n{chunk}\n")
