from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from utils.document_processor import process_documents
from utils.querying_database import querying_faiss_database
import os
from werkzeug.utils import secure_filename
import logging
from utils.upload_local_database import inspect_faiss_database
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PDF_STORAGE'] = 'static/pdfs'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_STORAGE'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            db_name = request.form.get('database', 'General')
            print(f"Processing document {filename} for database {db_name}")
            
            # Store PDF files with database prefix
            if filename.endswith('.pdf'):
                safe_filename = secure_filename(f"{db_name}_{filename}")
                pdf_storage_path = os.path.join(app.config['PDF_STORAGE'], safe_filename)
                shutil.copy2(filepath, pdf_storage_path)
            
            success = process_documents(filepath, db_name)
            os.remove(filepath)  # Clean up the uploaded file
            
            if success:
                return jsonify({'message': f'Successfully processed {filename}'})
            else:
                return jsonify({'error': 'Failed to process document'}), 500
                
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type. Supported types: .pdf, .txt'}), 400

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Get database name from request, default to "General"
        db_name = data.get('database', 'General')
        
        # Add logging to debug
        logging.info(f"Querying database {db_name} with question: {data['question']}")
        
        response = querying_faiss_database(
            query=data['question'],
            model_name="deepseek-r1:1.5b",
            db_name=db_name,
            top_k=3  # Adjust this value as needed
        )
        
        if response is None:
            logging.error("Got None response from querying_faiss_database")
            return jsonify({'error': 'Failed to get response from model'}), 500
            
        logging.info(f"Got response: {response}")
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in query endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check-database', methods=['GET'])
def check_database():
    try:
        db_name = request.args.get('database', 'General')
        stats = inspect_faiss_database(db_name)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list-databases', methods=['GET'])
def list_databases():
    try:
        from utils.upload_local_database import get_available_databases
        databases = get_available_databases()
        return jsonify({'databases': databases})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create-database', methods=['POST'])
def create_database():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'No database name provided'}), 400
            
        db_name = secure_filename(data['name'])  # Sanitize the database name
        
        if not db_name:
            return jsonify({'error': 'Invalid database name'}), 400
            
        from utils.upload_local_database import create_database, get_available_databases
        
        # Check if database already exists
        existing_dbs = get_available_databases()
        if db_name in existing_dbs:
            return jsonify({'error': 'Database already exists'}), 400
            
        # Create the new database
        create_database(db_name)
        return jsonify({'message': f'Successfully created database: {db_name}'})
        
    except Exception as e:
        logging.error(f"Error creating database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/create-document', methods=['POST'])
def create_document():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'content' not in data or 'database' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        filename = secure_filename(data['name'])
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        # Ensure filename has .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        # Create temporary file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data['content'])
            
            # Process the document
            success = process_documents(filepath, data['database'])
            os.remove(filepath)  # Clean up the temporary file
            
            if success:
                return jsonify({'message': f'Successfully created and processed {filename}'})
            else:
                return jsonify({'error': 'Failed to process document'}), 500
                
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        logging.error(f"Error creating document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete-file', methods=['POST'])
def delete_file():
    try:
        data = request.get_json()
        if not data or 'filename' not in data or 'database' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        from utils.upload_local_database import delete_file_from_database
        success = delete_file_from_database(data['filename'], data['database'])
        
        if success:
            return jsonify({'message': f'Successfully deleted {data["filename"]}'})
        else:
            return jsonify({'error': 'Failed to delete file'}), 500
            
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete-database', methods=['POST'])
def delete_database():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'No database name provided'}), 400
            
        if data['name'] == 'General':
            return jsonify({'error': 'Cannot delete the General database'}), 400
            
        from utils.upload_local_database import delete_database
        success = delete_database(data['name'])
        
        if success:
            return jsonify({'message': f'Successfully deleted database: {data["name"]}'})
        else:
            return jsonify({'error': 'Failed to delete database'}), 500
            
    except Exception as e:
        logging.error(f"Error deleting database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-pdf/<database>/<filename>')
def get_pdf(database, filename):
    # Sanitize the filename
    safe_filename = secure_filename(f"{database}_{filename}")
    pdf_path = os.path.join(app.config['PDF_STORAGE'], safe_filename)
    
    if os.path.exists(pdf_path):
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )
    print(f"PDF not found: {pdf_path}")
    return jsonify({'error': 'PDF not found'}), 404

@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('static/pdfs', filename)

@app.route('/chat', methods=['POST'])
def chat():
    # ... existing code ...
    
    # Add PDF reference to response if available
    response_data = {
        'message': ai_response,
        'pdf_reference': 'document.pdf'  # Replace with actual PDF filename
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True) 