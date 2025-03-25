from flask import Flask, render_template, request, send_file, jsonify, url_for
import PyPDF2
import os
from werkzeug.utils import secure_filename
from PIL import Image
import img2pdf
from PyPDF2 import PdfReader, PdfWriter
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge-tool')
def merge_tool():
    return render_template('tools/merge.html')

@app.route('/split-tool')
def split_tool():
    return render_template('tools/split.html')

@app.route('/compress-tool')
def compress_tool():
    return render_template('tools/compress.html')

@app.route('/images-tool')
def images_tool():
    return render_template('tools/images.html')

@app.route('/reorder-tool')
def reorder_tool():
    return render_template('tools/reorder.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    files = request.files.getlist('files')
    merger = PyPDF2.PdfMerger()
    
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            merger.append(filepath)
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
    merger.write(output_path)
    merger.close()
    
    return send_file(output_path, as_attachment=True)

@app.route('/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    pdf = PyPDF2.PdfReader(filepath)
    pdf_writer = PyPDF2.PdfWriter()
    
    start_page = int(request.form.get('start_page', 1)) - 1
    end_page = int(request.form.get('end_page', len(pdf.pages)))
    
    for page_num in range(start_page, end_page):
        pdf_writer.add_page(pdf.pages[page_num])
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'split.pdf')
    with open(output_path, 'wb') as output_file:
        pdf_writer.write(output_file)
    
    return send_file(output_path, as_attachment=True)

@app.route('/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Read the PDF
    reader = PdfReader(filepath)
    writer = PdfWriter()

    # Compress each page
    for page in reader.pages:
        page.compress_content_streams()  # This compresses the PDF
        writer.add_page(page)
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed.pdf')
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    return send_file(output_path, as_attachment=True)

@app.route('/images-to-pdf', methods=['POST'])
def images_to_pdf():
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    files = request.files.getlist('files')
    image_paths = []
    
    # Save and process images
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Convert image to RGB if necessary
            with Image.open(filepath) as img:
                if img.mode != 'RGB':
                    rgb_img = img.convert('RGB')
                    rgb_img.save(filepath)
            
            image_paths.append(filepath)
    
    # Convert images to PDF
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted_images.pdf')
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(image_paths))
    
    return send_file(output_path, as_attachment=True)

@app.route('/reorder', methods=['POST'])
def reorder_pdf():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    page_order = request.form.get('page_order', '').split(',')
    
    if not page_order:
        return 'No page order specified', 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    # Add pages in the specified order
    for page_num in page_order:
        try:
            page_index = int(page_num.strip()) - 1
            if 0 <= page_index < len(reader.pages):
                writer.add_page(reader.pages[page_index])
        except ValueError:
            continue
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'reordered.pdf')
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 