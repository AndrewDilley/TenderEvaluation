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

    return response.choices[0].message.content  # Extract the response text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'documents' not in request.files or 'evaluation_criteria' not in request.files:
        return jsonify({"error": "Please upload both documents and evaluation criteria."}), 400

    document_files = request.files.getlist('documents')
    criteria_file = request.files['evaluation_criteria']

    document_texts = []
    for file in document_files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract company name from filename (assuming it's before the first underscore or dot)
        company_name = filename.split('_')[0].split('.')[0]
        
        # Determine file type and extract text
        if filename.lower().endswith('.pdf'):
            raw_text = extract_text_from_pdf(filepath)
        elif filename.lower().endswith('.docx'):
            raw_text = extract_text_from_docx(filepath)
        else:
            return jsonify({"error": f"Unsupported file type: {filename}"}), 400
        
        # Apply both redaction functions
        redacted_text = redact_sensitive_data(raw_text, company_name)
        redacted_text = redact_pii(redacted_text)  # Apply new PII redaction

        document_texts.append(redacted_text)

        # Save redacted text as a .txt file
        redacted_filename = f"{filename.rsplit('.', 1)[0]}_redacted.txt"
        redacted_path = os.path.join(app.config['REDACTED_FOLDER'], redacted_filename)
        with open(redacted_path, "w", encoding="utf-8") as redacted_file:
            redacted_file.write(redacted_text)

        return jsonify({
            "document": filename,
            "redacted_text_file": f"/download/{redacted_filename}"
        }), 200
 
    # Read evaluation criteria
    criteria_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(criteria_file.filename))
    criteria_file.save(criteria_path)
    if criteria_path.lower().endswith(".xlsx"):
        df = pd.read_excel(criteria_path)  # Read Excel file
        criteria = df.to_string(index=False)  # Convert DataFrame to a string
    else:
        with open(criteria_path, 'r', encoding="utf-8", errors="replace") as f:
            criteria = f.read()  # Read as text

    # Evaluate documents
    evaluations = []
    for idx, text in enumerate(document_texts):
        evaluation = evaluate_document(text, criteria)
        evaluations.append({"document": document_files[idx].filename, "evaluation": evaluation})

    return jsonify(evaluations)

# Endpoint to download redacted text files
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['REDACTED_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
