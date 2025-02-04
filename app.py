from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import re
import openai
from werkzeug.utils import secure_filename
import PyPDF2
import pandas as pd
import docx
from dotenv import load_dotenv

app = Flask(__name__, static_folder="static")
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['REDACTED_FOLDER'] = 'redacted/'
os.makedirs(app.config['REDACTED_FOLDER'], exist_ok=True)

load_dotenv()

import shutil

import os
import shutil

def reset_flag_file():
    """Removes the .cleared flag file at the start of a new session."""
    folder_path = app.config['REDACTED_FOLDER']
    flag_file = os.path.join(folder_path, ".cleared")

    print(f"🔍 Checking if flag file exists: {flag_file}")

    if os.path.exists(flag_file):
        try:
            os.remove(flag_file)
            print("🗑️ .cleared flag file removed at the start of a new session.")
        except Exception as e:
            print(f"⚠️ Error removing flag file: {e}")
    else:
        print("✅ No previous .cleared flag file found, skipping deletion.")

def clear_redacted_folder_once():
    """Clears REDACTED_FOLDER only once per session by using a flag file."""
    folder_path = app.config['REDACTED_FOLDER']
    flag_file = os.path.join(folder_path, ".cleared")

    print(f"🔍 Checking REDACTED_FOLDER: {folder_path}")

    # Ensure the folder exists before proceeding
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        print("📂 Created missing REDACTED_FOLDER.")

    # Step 1: Remove old flag file (reset for new session)
    reset_flag_file()

    # Step 2: Check if the flag file exists; if so, do not clear the folder again
    print(f"🔍 Checking if cleanup was already done: {flag_file}")

    if os.path.exists(flag_file):
        print("✅ REDACTED_FOLDER was already cleared this session. Skipping cleanup.")
        return

    # Step 3: Clear folder contents
    print("🗑️ Clearing REDACTED_FOLDER contents...")

    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Delete file or symlink
                    print(f"🗑️ Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Delete subdirectory
                    print(f"🗑️ Deleted directory: {file_path}")
            except Exception as e:
                print(f"⚠️ Error deleting {file_path}: {e}")

        # Step 4: Create a flag file to indicate cleanup has been done
        with open(flag_file, "w") as f:
            f.write("Cleared at startup.")
        print("✅ REDACTED_FOLDER has been cleared at startup.")

    except Exception as e:
        print(f"❌ Unexpected error while clearing REDACTED_FOLDER: {e}")

# Run the function at startup
clear_redacted_folder_once()




# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure OPENAI_API_KEY is set in the .env file.")

# Serve static files
@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory("static/js", filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory("static/css", filename)

# Preprocessing function to redact sensitive data using regex
def redact_sensitive_data(text, company_name):
    patterns = [
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSNs
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',     # IP Addresses
        r'\b\d{16}\b',                        # Credit card numbers
        r'\b[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}\b'  # Email addresses
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", text)
    
    if company_name:
        text = re.sub(re.escape(company_name), "[REDACTED COMPANY]", text, flags=re.IGNORECASE)
    
    return text


# Function to redact PII from the text
def redact_pii(text):
    import re
    # Redact email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED EMAIL]", text)
    # Redact phone numbers
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b", "[REDACTED PHONE]", text)
    # Redact credit card numbers
    text = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED CREDIT CARD]", text)

    # Redact addresses
    street_types = r"(St|Street|Dv|Dve|Drive|Lane|Ln|Road|Rd|Court|Ct|Crescent|Cr|Cres|Highway|HWY|Hwy|Ave|Avenue|Boulevard|Way)"
    state_types = r"(ACT|Australian Capital Territory|NSW|New South Wales|NT|Northern Territory|QLD|Queensland|SA|South Australia|TAS|Tasmania|VIC|Victoria|WA|Western Australia)"
    
    address_pattern = fr"\b(?:\d+/)?\d+[a-zA-Z]?\s+\w+(?:\s\w+)*\s{street_types}(?:,?\s\w+(?:\s\w+)*)?(?:,?\s\d{{4}})?(?:,?\s{state_types})?(?:,?\s\d{{4}})?\b"
    text = re.sub(address_pattern, "[REDACTED ADDRESS]", text, flags=re.IGNORECASE)

    # Redact names (known names)
    ww_names = ["Wannon Water", "WW", "Wannon Region Water Corporation"]
    for name in ww_names:
        text = text.replace(name, "[REDACTED RECIPIENT NAME]")

    name_pattern = r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[A-Z](?:\.|[a-z]+)?(?:\s[A-Z](?:\.|[a-z]+)?)*\s[A-Z][a-z]+)\b"
    text = re.sub(name_pattern, "[REDACTED NAME]", text)

    return text


# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

# Function to extract text from Word documents
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Evaluation function using OpenAI API
client = openai.OpenAI()  # Initialize OpenAI client

def evaluate_document(document_text, criteria):
    prompt = f"Evaluate the following document based on these criteria: {criteria} Document: {document_text} Provide scores and justifications for each criterion in the following structured format: <h2><b>Criterion Name (Weighting%)</b></h2> ⭐ Score: X/10<br><br><b>📌 Evaluation Summary:</b><br><ul><li>Key point 1</li><li>Key point 2</li></ul><br><b>📈 Strengths:</b><br><ul><li>Strength 1</li><li>Strength 2</li></ul><br><b>💡 Weaknesses:</b><br><ul><li>Weakness suggestion 1</li><li>Weakness suggestion 2</li></ul>".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that evaluates documents."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    evaluation_text = response.choices[0].message.content
    
    # 🚀 **New Blank Line Cleanup Logic**
    evaluation_text = re.sub(r'\n{3,}', '\n\n', evaluation_text).strip()  # Remove more than 2 newlines
    evaluation_text = re.sub(r'\n\s*\n', '\n', evaluation_text).strip()  # Remove whitespace-only lines
    evaluation_text = re.sub(r'^\s*\n', '', evaluation_text)  # Ensure no leading newlines
 
    return evaluation_text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'documents' not in request.files:
        return jsonify({"error": "Please upload documents."}), 400

    document_files = request.files.getlist('documents')
    redacted_files = []  # Track redacted files

    for file in document_files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text from document
        if filename.lower().endswith('.pdf'):
            raw_text = extract_text_from_pdf(filepath)
        elif filename.lower().endswith('.docx'):
            raw_text = extract_text_from_docx(filepath)
        else:
            return jsonify({"error": f"Unsupported file type: {filename}"}), 400

        # Apply redaction functions
        redacted_text = redact_sensitive_data(raw_text, filename)
        redacted_text = redact_pii(redacted_text)

        # Save redacted text immediately
        redacted_filename = f"{filename.rsplit('.', 1)[0]}_redacted.txt"
        redacted_path = os.path.join(app.config['REDACTED_FOLDER'], redacted_filename)

        with open(redacted_path, "w", encoding="utf-8") as redacted_file:
            redacted_file.write(redacted_text)

        redacted_files.append({
            "document": filename,
            "redacted_text_file": f"/download/{redacted_filename}"
        })

    # Return response immediately after redaction
    return jsonify({"redacted_files": redacted_files}), 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['REDACTED_FOLDER'], filename, as_attachment=True)


import json  # Import json to check for encoding issues

@app.route('/evaluate', methods=['POST'])
def evaluate_files():
    if 'evaluation_criteria' not in request.files:
        return jsonify({"error": "Please upload evaluation criteria."}), 400

    criteria_file = request.files['evaluation_criteria']
    criteria_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(criteria_file.filename))
    criteria_file.save(criteria_path)

    # Read evaluation criteria
    if criteria_path.lower().endswith(".xlsx"):
        df = pd.read_excel(criteria_path)
        criteria = df.to_string(index=False)
    else:
        with open(criteria_path, 'r', encoding="utf-8", errors="replace") as f:
            criteria = f.read()

    evaluations = []

    #redacted_files = os.listdir(app.config['REDACTED_FOLDER'])

    redacted_files = [f for f in os.listdir(app.config['REDACTED_FOLDER']) if f != ".cleared"]


    if not redacted_files:
        print("❌ No redacted files found for evaluation!")
        return jsonify({"error": "No redacted files found for evaluation."}), 400

    print(f"✅ Evaluating {len(redacted_files)} redacted files...")

    for redacted_filename in redacted_files:
        redacted_path = os.path.join(app.config['REDACTED_FOLDER'], redacted_filename)

        with open(redacted_path, 'r', encoding="utf-8") as redacted_file:
            redacted_text = redacted_file.read()

        evaluation_result = evaluate_document(redacted_text, criteria)

        evaluations.append({
            "document": redacted_filename,
            "evaluation": evaluation_result
        })


        
    # Log JSON to check validity
    try:
        json_string = json.dumps({"evaluations": evaluations}, ensure_ascii=False)
        print("🔄 JSON Response:", json_string)
    except Exception as e:
        print("❌ JSON Encoding Error:", e)

    return jsonify({"evaluations": evaluations})


if __name__ == '__main__':
    app.run(debug=True, port=5002)
