import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ID_PROOFS_FOLDER = os.path.join(UPLOAD_FOLDER, 'id_proofs')
GALLERY_FOLDER = os.path.join(UPLOAD_FOLDER, 'gallery')
DATA_FILE = 'data/database.json'

# Ensure directories exist
os.makedirs(ID_PROOFS_FOLDER, exist_ok=True)
os.makedirs(GALLERY_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ID_PROOFS_FOLDER'] = ID_PROOFS_FOLDER
app.config['GALLERY_FOLDER'] = GALLERY_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"portions": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_id():
    data = load_data()
    if not data["portions"]:
        return 1
    return max(portion["id"] for portion in data["portions"]) + 1

@app.route('/')
def dashboard():
    data = load_data()
    return render_template('dashboard.html', portions=data["portions"])


@app.route('/portion/<int:id>')
def portion_detail(id):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    return render_template('portion_detail.html', portion=portion)


@app.route('/portion/add', methods=['GET', 'POST'])
def add_portion():
    if request.method == 'POST':
        data = load_data()
        
        # Determine the portion number
        portion_no = request.form['portion_no']
        if portion_no == 'new':
            portion_no = request.form['new_portion_no']
        
        portion = {
            "id": get_next_id(),
            "floor": request.form['floor'],
            "portion_no": portion_no,
            "type": request.form['type'],
            "name": request.form['name'],
            "tenant_type": request.form['tenant_type'],
            "members": [m.strip() for m in request.form['members'].split(',') if m.strip()],
            "contact_number": request.form['contact_number'],
            "contact_number_2": request.form.get('contact_number_2', ''),
            "id_proofs": [],
            "photos": [],
            "bills": {}
        }
        data["portions"].append(portion)
        save_data(data)
        flash('Portion added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('portion_form.html')

@app.route('/portion/<int:id>/edit', methods=['GET', 'POST'])
def edit_portion(id):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # For editing, we don't change the floor or portion number
        portion["type"] = request.form['type']
        portion["name"] = request.form['name']
        portion["tenant_type"] = request.form['tenant_type']
        portion["members"] = [m.strip() for m in request.form['members'].split(',') if m.strip()]
        portion["contact_number"] = request.form['contact_number']
        portion["contact_number_2"] = request.form.get('contact_number_2', '')
        save_data(data)
        flash('Portion updated successfully!', 'success')
        return redirect(url_for('portion_detail', id=id))
    
    return render_template('portion_form.html', portion=portion)

@app.route('/get_portions_by_floor')
def get_portions_by_floor():
    floor = request.args.get('floor')
    data = load_data()
    
    if floor:
        portions = [p for p in data["portions"] if p.get("floor") == floor]
        return jsonify({"portions": portions})
    
    return jsonify({"portions": []})


@app.route('/portion/<int:id>/delete')
def delete_portion(id):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete associated files
    for proof in portion["id_proofs"]:
        proof_path = os.path.join(app.config['ID_PROOFS_FOLDER'], proof)
        if os.path.exists(proof_path):
            os.remove(proof_path)
    
    for photo in portion["photos"]:
        photo_path = os.path.join(app.config['GALLERY_FOLDER'], photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    data["portions"] = [p for p in data["portions"] if p["id"] != id]
    save_data(data)
    flash('Portion deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/portion/<int:id>/upload_id', methods=['POST'])
def upload_id_proof(id):
    if 'id_proof' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('portion_detail', id=id))
    
    file = request.files['id_proof']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('portion_detail', id=id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['ID_PROOFS_FOLDER'], filename))
        
        data = load_data()
        portion = next((p for p in data["portions"] if p["id"] == id), None)
        if portion:
            portion["id_proofs"].append(filename)
            save_data(data)
            flash('ID proof uploaded successfully!', 'success')
        else:
            flash('Portion not found!', 'error')
    
    return redirect(url_for('portion_detail', id=id))

@app.route('/portion/<int:id>/upload_photo', methods=['POST'])
def upload_photo(id):
    if 'photo' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('portion_detail', id=id))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('portion_detail', id=id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['GALLERY_FOLDER'], filename))
        
        data = load_data()
        portion = next((p for p in data["portions"] if p["id"] == id), None)
        if portion:
            portion["photos"].append(filename)
            save_data(data)
            flash('Photo uploaded successfully!', 'success')
        else:
            flash('Portion not found!', 'error')
    
    return redirect(url_for('portion_detail', id=id))

from datetime import datetime

@app.route('/portion/<int:id>/bills', methods=['GET', 'POST'])
def manage_bills(id):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        month = request.form['month']
        portion["bills"][month] = {
            "rent": float(request.form['rent']),
            "water": float(request.form['water']),
            "electricity": float(request.form['electricity']),
            "extra": float(request.form['extra']),
            "total": float(request.form['rent']) + float(request.form['water']) + 
                    float(request.form['electricity']) + float(request.form['extra'])
        }
        save_data(data)
        flash('Bill updated successfully!', 'success')
        return redirect(url_for('manage_bills', id=id))
    
    # Pass current datetime to the template
    return render_template('bills.html', portion=portion, now=datetime.now())




@app.route('/portion/<int:id>/bill/<month>/delete', methods=['POST'])
def delete_bill(id, month):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if month in portion["bills"]:
        del portion["bills"][month]
        save_data(data)
        flash('Bill deleted successfully!', 'success')
    else:
        flash('Bill not found!', 'error')
    
    return redirect(url_for('manage_bills', id=id))

@app.route('/send_message/<int:id>')
def send_message(id):
    data = load_data()
    portion = next((p for p in data["portions"] if p["id"] == id), None)
    if not portion:
        flash('Portion not found!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get current month's bill if exists
    current_month = datetime.now().strftime('%B %Y').lower()
    bill = portion["bills"].get(current_month, {})
    
    # Create WhatsApp message
    message = f"Hello, this is your rental bill for {current_month.capitalize()}:\n"
    if bill:
        message += f"Rent: ₹{bill.get('rent', 0)}\n"
        message += f"Water: ₹{bill.get('water', 0)}\n"
        message += f"Electricity: ₹{bill.get('electricity', 0)}\n"
        message += f"Extra: ₹{bill.get('extra', 0)}\n"
        message += f"Total: ₹{bill.get('total', 0)}"
    else:
        message += "No bill generated for this month yet."
    
    # Encode message for URL
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    # Use primary contact number, fall back to secondary if needed
    contact_number = portion['contact_number'] or portion.get('contact_number_2', '')
    
    if contact_number:
        whatsapp_url = f"https://wa.me/{contact_number}?text={encoded_message}"
        return redirect(whatsapp_url)
    else:
        flash('No contact number available for this portion!', 'error')
        return redirect(url_for('portion_detail', id=id))



@app.route('/send_to_all')
def send_to_all():
    data = load_data()
    current_month = datetime.now().strftime('%B %Y').lower()
    
    # Create a message with all bills
    message = f"Rental Bills for {current_month.capitalize()}:\n\n"
    for portion in data["portions"]:
        bill = portion["bills"].get(current_month, {})
        message += f"{portion['name']}:\n"
        if bill:
            message += f"  Rent: ₹{bill.get('rent', 0)}\n"
            message += f"  Water: ₹{bill.get('water', 0)}\n"
            message += f"  Electricity: ₹{bill.get('electricity', 0)}\n"
            message += f"  Extra: ₹{bill.get('extra', 0)}\n"
            message += f"  Total: ₹{bill.get('total', 0)}\n\n"
        else:
            message += "  No bill generated for this month yet.\n\n"
    
    # Encode message for URL (will send to first tenant as example)
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    if data["portions"]:
        first_contact = data["portions"][0]["contact_number"]
        whatsapp_url = f"https://wa.me/{first_contact}?text={encoded_message}"
        flash('Message prepared. Please review before sending.', 'info')
        return redirect(whatsapp_url)
    
    flash('No portions found!', 'error')
    return redirect(url_for('dashboard'))

@app.route('/uploads/id_proofs/<filename>')
def serve_id_proof(filename):
    return send_from_directory(app.config['ID_PROOFS_FOLDER'], filename)

@app.route('/uploads/gallery/<filename>')
def serve_gallery(filename):
    return send_from_directory(app.config['GALLERY_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)