document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chatContainer');
    const questionInput = document.getElementById('questionInput');
    const sendButton = document.getElementById('sendButton');
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const databaseSelector = document.getElementById('databaseSelector');
    const fileList = document.getElementById('fileList');
    const newDatabaseInput = document.getElementById('newDatabaseInput');
    const createDatabaseBtn = document.getElementById('createDatabaseBtn');
    const createDatabaseStatus = document.getElementById('createDatabaseStatus');
    const createDocumentBtn = document.getElementById('createDocumentBtn');
    const createDocumentModal = document.getElementById('createDocumentModal');
    const modalClose = document.querySelector('.modal-close');
    const cancelCreateDocument = document.getElementById('cancelCreateDocument');
    const createDocumentForm = document.getElementById('createDocumentForm');
    let currentDatabase = 'General';
    let pdfDoc = null;
    let pageNum = 1;
    let currentPdfUrl = null;

    // Initialize PDF.js
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    let currentPdf = null;
    let currentPage = 1;

    const uploadDropZone = document.getElementById('uploadDropZone');
    const fileInput = document.getElementById('fileInput');
    const selectedFiles = document.getElementById('selectedFiles');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadDropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadDropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadDropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadDropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        uploadDropZone.classList.remove('dragover');
    }

    // Handle dropped files
    uploadDropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    // Handle selected files
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    // Click on drop zone to trigger file input
    uploadDropZone.addEventListener('click', () => {
        fileInput.click();
    });

    function handleFiles(files) {
        selectedFiles.innerHTML = '';
        Array.from(files).forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'selected-file';
            fileElement.innerHTML = `
                <div class="selected-file-name">
                    <span class="selected-file-icon">${file.name.endsWith('.pdf') ? '📄' : '📝'}</span>
                    ${file.name}
                </div>
                <button type="button" class="remove-file" title="Remove file">×</button>
            `;
            selectedFiles.appendChild(fileElement);
        });
    }

    function removeThinkTags(text) {
        // Remove content between <think> and </think> tags
        return text.replace(/<think>[\s\S]*?<\/think>/g, '');
    }

    async function typeText(element, text) {
        let formattedMessage = '';
        let index = 0;
        const delay = 10; // Milliseconds per character
        
        return new Promise((resolve) => {
            function type() {
                if (index < text.length) {
                    // Handle bold text (**text**)
                    if (text.slice(index).startsWith('**')) {
                        const endBold = text.indexOf('**', index + 2);
                        if (endBold !== -1) {
                            const boldText = text.slice(index + 2, endBold);
                            formattedMessage += `<strong>${boldText}</strong>`;
                            index = endBold + 2;
                            element.innerHTML = formattedMessage;
                            setTimeout(type, delay);
                            return;
                        }
                    }
                    
                    // Handle italic text (*text*)
                    if (text.slice(index).startsWith('*') && !text.slice(index).startsWith('**')) {
                        const endItalic = text.indexOf('*', index + 1);
                        if (endItalic !== -1) {
                            const italicText = text.slice(index + 1, endItalic);
                            formattedMessage += `<em>${italicText}</em>`;
                            index = endItalic + 1;
                            element.innerHTML = formattedMessage;
                            setTimeout(type, delay);
                            return;
                        }
                    }
                    
                    // Handle code text (`text`)
                    if (text.slice(index).startsWith('`')) {
                        const endCode = text.indexOf('`', index + 1);
                        if (endCode !== -1) {
                            const codeText = text.slice(index + 1, endCode);
                            formattedMessage += `<code>${codeText}</code>`;
                            index = endCode + 1;
                            element.innerHTML = formattedMessage;
                            setTimeout(type, delay);
                            return;
                        }
                    }
                    
                    // Handle line breaks
                    if (text.charAt(index) === '\n') {
                        // Only add line break if not at start of text
                        if (index > 1) {
                            formattedMessage += '<br>';
                        }
                    } else {
                        formattedMessage += text.charAt(index);
                    }
                    
                    element.innerHTML = formattedMessage;
                    index++;
                    element.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    setTimeout(type, delay);
                } else {
                    resolve();
                }
            }
            type();
        });
    }

    async function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        if (isUser) {
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            // Add typing indicator first
            messageDiv.innerHTML = '<div class="typing-indicator">...</div>';
            chatContainer.appendChild(messageDiv);
            
            // Process the message
            setTimeout(async () => {
                // Extract source information
                const sourceMatch = content.match(/Source: (.*?) \(Page (\d+)\)/);
                let sourceRef = '';
                
                if (sourceMatch) {
                    const [fullMatch, filename, page] = sourceMatch;
                    // Remove the .txt extension and ensure .pdf extension
                    const pdfFilename = filename.replace(/\.(txt|pdf)$/, '') + '.pdf';
                    sourceRef = `<br><span class="source-reference" onclick="loadAndShowPdf('${currentDatabase}', '${pdfFilename}', ${page})">${fullMatch}</span>`;
                    content = content.replace(fullMatch, '');
                }
                
                // Clear typing indicator and start typing the formatted content
                messageDiv.innerHTML = '';
                await typeText(messageDiv, removeThinkTags(content));
                
                // Add source reference if exists
                if (sourceRef) {
                    messageDiv.innerHTML += sourceRef;
                }
                
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 500);
        }
    }

    // Function to load available databases
    async function loadDatabases() {
        try {
            const response = await fetch('/list-databases');
            const data = await response.json();
            
            databaseSelector.innerHTML = '';
            data.databases.forEach(db => {
                const option = document.createElement('option');
                option.value = db;
                option.textContent = db;
                if (db === currentDatabase) {
                    option.selected = true;
                }
                databaseSelector.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading databases:', error);
        }
    }

    // Function to update file list
    async function updateFileList() {
        try {
            const response = await fetch(`/check-database?database=${currentDatabase}`);
            const data = await response.json();
            
            fileList.innerHTML = '';
            if (data.documents) {
                Object.entries(data.documents).forEach(([filename, count]) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div class="file-content">
                            <span class="file-name">${filename}</span>
                            <span class="file-meta">${count} chunks</span>
                        </div>
                        <button class="delete-btn" title="Delete File">🗑️</button>
                    `;
                    
                    const deleteBtn = fileItem.querySelector('.delete-btn');
                    deleteBtn.addEventListener('click', async () => {
                        if (confirm(`Are you sure you want to delete ${filename}?`)) {
                            await deleteFile(filename, currentDatabase);
                        }
                    });
                    
                    fileList.appendChild(fileItem);
                });
            }
        } catch (error) {
            console.error('Error updating file list:', error);
        }
    }

    // Handle database selection change
    databaseSelector.addEventListener('change', function(e) {
        currentDatabase = e.target.value;
        deleteDatabaseBtn.disabled = currentDatabase === 'General';
        updateFileList();
    });

    // Update upload form to include database selection
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        const files = fileInput.files;

        if (files.length === 0) {
            uploadStatus.textContent = 'Please select a file';
            uploadStatus.className = 'error';
            return;
        }

        const formData = new FormData();
        for (let file of files) {
            formData.append('file', file);
        }
        formData.append('database', currentDatabase);

        try {
            uploadStatus.textContent = 'Uploading...';
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) {
                uploadStatus.textContent = `Error: ${data.error}`;
                uploadStatus.className = 'error';
            } else {
                uploadStatus.textContent = data.message;
                uploadStatus.className = 'success';
                fileInput.value = '';
                updateFileList();  // Update file list after successful upload
            }
        } catch (error) {
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.className = 'error';
        }
    });

    // Update query to include current database
    async function sendQuestion() {
        const question = questionInput.value.trim();
        if (!question) return;

        addMessage(question, true);
        questionInput.value = '';
        sendButton.disabled = true;

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    database: currentDatabase
                }),
            });

            const data = await response.json();
            if (data.error) {
                addMessage(`Error: ${data.error}`, false);
            } else {
                addMessage(data.response, false);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage(`Error: ${error.message}`, false);
        } finally {
            sendButton.disabled = false;
        }
    }

    // Function to create a new database
    async function createDatabase(name) {
        try {
            const response = await fetch('/create-database', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name }),
            });

            const data = await response.json();
            
            if (response.ok) {
                createDatabaseStatus.textContent = data.message;
                createDatabaseStatus.className = 'status-message success';
                newDatabaseInput.value = '';
                
                // Refresh database list and switch to new database
                await loadDatabases();
                currentDatabase = name;
                databaseSelector.value = name;
                updateFileList();
            } else {
                createDatabaseStatus.textContent = data.error;
                createDatabaseStatus.className = 'status-message error';
            }
        } catch (error) {
            console.error('Error creating database:', error);
            createDatabaseStatus.textContent = 'Error creating database';
            createDatabaseStatus.className = 'status-message error';
        }
    }

    // Handle create database button click
    createDatabaseBtn.addEventListener('click', function() {
        const name = newDatabaseInput.value.trim();
        if (!name) {
            createDatabaseStatus.textContent = 'Please enter a database name';
            createDatabaseStatus.className = 'status-message error';
            return;
        }
        
        // Validate database name (only allow letters, numbers, underscores, and hyphens)
        if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
            createDatabaseStatus.textContent = 'Invalid database name. Use only letters, numbers, underscores, and hyphens.';
            createDatabaseStatus.className = 'status-message error';
            return;
        }
        
        createDatabase(name);
    });

    // Handle Enter key in database input
    newDatabaseInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            createDatabaseBtn.click();
        }
    });

    // Clear status message when typing
    newDatabaseInput.addEventListener('input', function() {
        createDatabaseStatus.textContent = '';
        createDatabaseStatus.className = 'status-message';
    });

    // Initial load
    loadDatabases();
    updateFileList();

    sendButton.addEventListener('click', sendQuestion);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });

    // Open modal
    createDocumentBtn.addEventListener('click', () => {
        createDocumentModal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    });

    // Close modal functions
    function closeModal() {
        const modalStatus = document.getElementById('modalStatus');
        createDocumentModal.style.display = 'none';
        document.body.style.overflow = '';
        createDocumentForm.reset(); // Reset form
        if (modalStatus) {
            modalStatus.textContent = '';
            modalStatus.className = 'status-message';
        }
    }

    modalClose.addEventListener('click', closeModal);
    cancelCreateDocument.addEventListener('click', closeModal);

    // Close modal when clicking outside
    createDocumentModal.addEventListener('click', (e) => {
        if (e.target === createDocumentModal) {
            closeModal();
        }
    });

    // Handle form submission
    createDocumentForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const modalStatus = document.getElementById('modalStatus');
        const submitButton = this.querySelector('button[type="submit"]');
        
        try {
            // Disable submit button and show loading state
            submitButton.disabled = true;
            modalStatus.textContent = 'Creating document...';
            modalStatus.className = 'status-message';
            
            const response = await fetch('/create-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: document.getElementById('documentName').value,
                    content: document.getElementById('documentContent').value,
                    database: currentDatabase
                }),
            });

            const data = await response.json();
            if (response.ok) {
                // Show success message briefly before closing
                modalStatus.textContent = 'Document created successfully!';
                modalStatus.className = 'status-message success';
                
                // Close modal and reset after short delay
                setTimeout(() => {
                    closeModal();
                    updateFileList(); // Refresh the file list
                }, 1000);
            } else {
                throw new Error(data.error || 'Failed to create document');
            }
        } catch (error) {
            console.error('Error creating document:', error);
            modalStatus.textContent = error.message;
            modalStatus.className = 'status-message error';
        } finally {
            submitButton.disabled = false;
        }
    });

    // Add these functions to your existing JavaScript

    async function deleteFile(filename, database) {
        try {
            const response = await fetch('/delete-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    database: database
                }),
            });

            const data = await response.json();
            if (response.ok) {
                updateFileList();  // Refresh the file list
                return true;
            } else {
                console.error('Error:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    }

    async function deleteDatabase(name) {
        try {
            const response = await fetch('/delete-database', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name }),
            });

            const data = await response.json();
            if (response.ok) {
                await loadDatabases();  // Refresh database list
                currentDatabase = 'General';  // Switch to General database
                databaseSelector.value = 'General';
                updateFileList();
                return true;
            } else {
                console.error('Error:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    }

    // Add delete database button handler
    const deleteDatabaseBtn = document.getElementById('deleteDatabaseBtn');
    deleteDatabaseBtn.addEventListener('click', async function() {
        if (currentDatabase === 'General') {
            alert('Cannot delete the General database');
            return;
        }
        
        if (confirm(`Are you sure you want to delete the database "${currentDatabase}"?`)) {
            await deleteDatabase(currentDatabase);
        }
    });

    // Add this function to handle PDF loading and display
    window.loadAndShowPdf = async function(database, filename, pageNumber) {
        console.log('Loading PDF:', database, filename, pageNumber); // Debug log
        
        const pdfPreview = document.getElementById('pdfPreview');
        const pdfUrl = `/get-pdf/${encodeURIComponent(database)}/${encodeURIComponent(filename)}`;
        
        console.log('Attempting to load PDF from:', pdfUrl); // Debug log
        
        try {
            // Show loading state
            pdfPreview.classList.add('active');
            const canvas = document.getElementById('pdf-canvas');
            canvas.style.opacity = '0.5';
            
            // Load new PDF
            const loadingTask = pdfjsLib.getDocument(pdfUrl);
            pdfDoc = await loadingTask.promise;
            currentPdfUrl = pdfUrl;
            document.getElementById('pageCount').textContent = pdfDoc.numPages;
            
            // Update page number
            pageNum = Math.min(Math.max(1, parseInt(pageNumber) || 1), pdfDoc.numPages);
            await renderPage(pageNum);
            
            // Show the loaded PDF
            canvas.style.opacity = '1';
        } catch (error) {
            console.error('Error loading PDF:', error);
            console.error('PDF URL attempted:', pdfUrl);
            alert('Error loading PDF. Please try again.');
            pdfPreview.classList.remove('active');
        }
    };

    async function renderPage(num) {
        if (!pdfDoc) return;
        
        const canvas = document.getElementById('pdf-canvas');
        const ctx = canvas.getContext('2d');
        
        try {
            const page = await pdfDoc.getPage(num);
            
            // Calculate scale to fit width while maintaining aspect ratio
            const pdfWidth = page.getViewport({ scale: 1 }).width;
            const containerWidth = document.getElementById('pdfPreview').clientWidth - 40; // Account for padding
            const scale = containerWidth / pdfWidth;
            
            const viewport = page.getViewport({ scale });
            
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            await page.render({
                canvasContext: ctx,
                viewport: viewport
            }).promise;
            
            document.getElementById('pageNum').textContent = num;
        } catch (error) {
            console.error('Error rendering page:', error);
        }
    }

    // Add event listeners for PDF controls
    document.getElementById('closePdfBtn').addEventListener('click', () => {
        document.getElementById('pdfPreview').classList.remove('active');
    });

    document.getElementById('prevPage').addEventListener('click', async () => {
        if (pageNum <= 1) return;
        await renderPage(--pageNum);
    });

    document.getElementById('nextPage').addEventListener('click', async () => {
        if (pageNum >= pdfDoc.numPages) return;
        await renderPage(++pageNum);
    });

    async function loadAndRenderPdf(pdfUrl, pageNumber = 1) {
        try {
            // Load the PDF document
            const loadingTask = pdfjsLib.getDocument(pdfUrl);
            const pdf = await loadingTask.promise;
            currentPdf = pdf;
            currentPage = pageNumber;
            
            // Render the page
            await renderPage(pageNumber);
        } catch (error) {
            console.error('Error loading PDF:', error);
        }
    }

    function updatePdfPreview(pdfReference) {
        if (pdfReference) {
            loadAndRenderPdf(`/static/pdfs/${pdfReference}`);
        }
    }

    async function handleMessage(message) {
        // ... existing code ...
        
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Update PDF preview if reference is provided
        if (data.pdf_reference) {
            updatePdfPreview(data.pdf_reference);
        }
        
        // ... rest of your message handling code ...
    }
}); 