from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import os
from fitz import Document as PDFDocument
from PIL import Image
import io
import base64
import fitz

app = Flask(__name__)
app.secret_key = 'parsa1384'
UPLOAD_FOLDER = 'contracts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def redire():
    return redirect("https://nlco.site")

@app.route('/upload_contract')
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('فایلی انتخاب نکرده‌اید.')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('فایلی انتخاب نکرده‌اید.')
        return redirect(request.url)
    
    if file and file.filename.endswith('.pdf'):
        factor_number = request.form.get('factor_number')
        if not factor_number:
            flash('لطفاً شماره فاکتور را وارد کنید.')
            return redirect(request.url)
        
        filename = f"{factor_number}-not_signed.pdf"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(file_path):
            flash('فایل با این شماره فاکتور قبلاً آپلود شده است.')
            return redirect(request.url)
        
        file.save(file_path)
        flash('فایل با موفقیت آپلود شد.')
        return redirect(url_for('index', contract_id=factor_number))
    else:
        flash('فایل باید یک فایل PDF باشد.')
        return redirect(request.url)

@app.route('/<contract_id>')
def index(contract_id):
    contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}-not_signed.pdf")
    signed_contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}.pdf")

    if os.path.exists(signed_contract_path):
        return render_template('index.html', contract_id=contract_id, signed=True, pdf_url=url_for('print_contract', contract_id=contract_id))
    elif os.path.exists(contract_path):
        return render_template('index.html', contract_id=contract_id, signed=False, pdf_url=url_for('print_contract', contract_id=f"{contract_id}-not_signed"))
    else:
        return "قرارداد پیدا نشد", 404

@app.route('/sign/<contract_id>', methods=['POST'])
def sign(contract_id):
    contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}-not_signed.pdf")
    signed_contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}.pdf")

    if not os.path.exists(contract_path):
        return "قرارداد پیدا نشد", 404

    signature_data = request.form.get('signature_data')
    if not signature_data:
        flash("لطفا ابتدا امضا کنید.")
        return redirect(url_for('index', contract_id=contract_id))

    # Convert base64 to image
    img_data = signature_data.split(',')[1]
    img = Image.open(io.BytesIO(base64.b64decode(img_data)))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Load the PDF document
    pdf_doc = PDFDocument(contract_path)
    page = pdf_doc.load_page(0)

    # Embed the image into the PDF
    page_height = page.rect.height
    rect = fitz.Rect(40, page_height - 120, 200, page_height - 40)  # Define the position and size of the signature
    page.insert_image(rect, stream=img_byte_arr)

    # Save the modified PDF
    pdf_doc.save(signed_contract_path)
    pdf_doc.close()

    os.remove(contract_path)

    return "OK"

@app.route('/print/<contract_id>')
def print_contract(contract_id):
    contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}.pdf")
    not_signed_contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}-not_signed.pdf")

    if os.path.exists(contract_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], f"{contract_id}.pdf")
    elif os.path.exists(not_signed_contract_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], f"{contract_id}-not_signed.pdf")
    else:
        return "قرارداد پیدا نشد", 404
    
@app.route('/download/<contract_id>')
def download_contract(contract_id):
    contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}.pdf")
    not_signed_contract_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{contract_id}-not_signed.pdf")

    if os.path.exists(contract_path):
        return send_file(contract_path)
    elif os.path.exists(not_signed_contract_path):
        return send_file(not_signed_contract_path)
    else:
        return "قرارداد پیدا نشد", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0")