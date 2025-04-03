# RAG Chatbot

A powerful Retrieval-Augmented Generation (RAG) chatbot system that allows users to create custom knowledge bases from documents and interact with them through natural language queries. The system supports multiple document types (PDF and TXT) and provides a modern, user-friendly interface.

## Features

- **Document Management**
  - Upload PDF and TXT documents
  - Create and manage multiple knowledge bases
  - View and delete documents within each knowledge base
  - PDF preview functionality

- **Advanced RAG Implementation**
  - Document chunking and embedding generation
  - FAISS vector database for efficient similarity search
  - Integration with Ollama for LLM-powered responses
  - Source attribution and page number references

- **User Interface**
  - Modern, responsive design
  - Real-time chat interface
  - Document preview capabilities
  - Database management dashboard
  - Status notifications and error handling

## Technical Stack

- **Backend**
  - Flask (Python web framework)
  - FAISS (Vector similarity search)
  - Sentence Transformers (Text embeddings)
  - Ollama (LLM integration)
  - PDF.js (PDF processing)

- **Frontend**
  - HTML/CSS
  - JavaScript
  - PDF.js viewer
  - Modern UI components

## Prerequisites

- Python 3.10 or above
- Ollama installed and running locally
- Required Python packages in requirements.yaml

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RAG-Chatbot.git
cd RAG-Chatbot
```

2. Create a new python env with conda:
```bash
conda env create -f requirements.yaml
```

3. Ensure Ollama is installed and running on your system.

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Makes sue to have the nessessary API keys

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Create a new knowledge base or use the default "General" database.

4. Upload documents or create new ones through the interface.

5. Start querying your documents using natural language.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
