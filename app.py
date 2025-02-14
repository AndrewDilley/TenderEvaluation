from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import re
import openai
from werkzeug.utils import secure_filename
import PyPDF2
import pandas as pd
import docx
from dotenv import load_dotenv

import json  # Import json to check for encoding issues

import shutil



app = Flask(__name__, static_folder="static")
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['REDACTED_FOLDER'] = 'redacted/'
os.makedirs(app.config['REDACTED_FOLDER'], exist_ok=True)

load_dotenv()


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
import re
import os

def redact_sensitive_data(text, filename):
    """Redacts sensitive data including occurrences of file names."""
    patterns = [
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSNs
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',     # IP Addresses
        r'\b\d{16}\b',                      # Credit card numbers
        r'\b[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}\b',  # Email addresses
        r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?'  # ✅ Price amounts ($xx.xx, $1,000, $50,000.00)
    ]

    # ✅ Redact predefined patterns
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", text)

    # ✅ Remove file extension and clean company name
    if filename:
        company_name = os.path.splitext(filename)[0]  # ✅ Remove extension
        company_name_variants = [
            re.escape(company_name),  # Exact match
            re.escape(company_name).replace(r"\ ", r"\s?"),  # Handle spaces
            re.escape(company_name).replace(r"\_", r"\s?")  # Handle underscores
        ]

        for variant in company_name_variants:
            text = re.sub(variant, "[REDACTED COMPANY]", text, flags=re.IGNORECASE)

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
    # ww_names = ["Wannon Water", "WW", "Wannon Region Water Corporation"]
    # for name in ww_names:
    #     text = text.replace(name, "[REDACTED RECIPIENT NAME]")


    text = redact_persons_name_text(text)

    #text = re.sub(name_pattern, "[REDACTED NAME]", text)

    return text

def redact_persons_name_text(text):
    # explicitly keep references to Wannon Water in the text to allow the LLM to detect previous work done with Wannon Water
    name_pattern = r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[A-Z](?:\.|[a-z]+)?(?:\s[A-Z](?:\.|[a-z]+)?)*\s[A-Z][a-z]+)\b"
    def replace_name(match):
        exclude_pattern = r"Wannon Water"
        matched_text = match.group(0)
        if re.fullmatch(exclude_pattern, matched_text):
            return matched_text  # Don't redact Wannon Water
        return "[REDACTED NAME]"
    
    return re.sub(name_pattern, replace_name, text)



def extract_text_from_pdf(pdf_path):
    """Extract text from PDF while tracking page numbers."""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text_with_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_with_pages.append(f"(Page {i+1}) {page_text}")  # Add page number

    return "\n".join(text_with_pages)


# Function to extract text from Word documents
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def generate_evaluation_tables(evaluations, weightings):
    df = pd.DataFrame(evaluations)

    print("🔍 Debug: Full Evaluations DataFrame Before Filtering")
    print(df.head(10))  # Print first 10 rows to inspect structure
    print("🔍 Debug: Columns in DataFrame:", df.columns)

    if df.empty:
        print("⚠️ Debug: No evaluation data provided.")
        return pd.DataFrame(), pd.DataFrame()

    # **Rename columns to remove "_redacted.txt" dynamically**
    df.columns = [col.replace("_redacted.txt", "").strip() for col in df.columns]
    
    # **Find updated Score and Yes/No columns**
    score_cols = [col for col in df.columns if "Score" in col]
    yes_no_cols = [col for col in df.columns if "Yes/No" in col]

    print(f"✅ Debug: Updated Score Columns: {score_cols}")
    print(f"✅ Debug: Updated Yes/No Columns: {yes_no_cols}")

    if not score_cols and not yes_no_cols:
        print("❌ Debug: Could not find necessary columns. Check AI output.")
        return pd.DataFrame(), pd.DataFrame()

    # **Group by Criterion to Ensure Each Appears Only Once**
    grouped_df = df.groupby("Criterion").first().reset_index()

    # **Separate Scored Criteria and Add Weighted Score Columns for Each Document**
    if score_cols:
        scored_df = grouped_df.dropna(subset=score_cols).filter(["Criterion"] + score_cols)

        # **Map correct weightings from detect_criteria_type()**
        scored_df["Weighting (%)"] = scored_df["Criterion"].map(weightings)

        # **Calculate weighted scores using correct weightings**
        for score_col in score_cols:
            weighted_col = f"Weighted {score_col}"
            scored_df[weighted_col] = (scored_df[score_col] * scored_df["Weighting (%)"]) / 100

        # **Create Total Row (Sum of Scores, Keep Weightings Unchanged)**
        total_scores = pd.DataFrame(scored_df[score_cols + [f"Weighted {col}" for col in score_cols]].sum()).T
        total_scores.insert(0, "Criterion", "Total")  # Add "Total" label
        total_scores["Weighting (%)"] = ""  # Prevent summing of weightings

        scored_df = pd.concat([scored_df, total_scores], ignore_index=True)
    
    else:
        scored_df = pd.DataFrame()

    # **Separate Yes/No Criteria for Each Document**
    yes_no_df = grouped_df.dropna(subset=yes_no_cols).filter(["Criterion"] + yes_no_cols) if yes_no_cols else pd.DataFrame()

    print("✅ Debug: Scored Criteria DataFrame Shape:", scored_df.shape)
    print("✅ Debug: Yes/No Criteria DataFrame Shape:", yes_no_df.shape)

    return scored_df, yes_no_df


# Evaluation function using OpenAI API
client = openai.OpenAI()  # Initialize OpenAI client


def evaluate_document_new(document_text, criteria_data, document_name):
    scored_criteria = {k: v['weighting'] for k, v in criteria_data.items() if v['type'] == 'scored_criteria'}
    yes_no_criteria = [k for k, v in criteria_data.items() if v['type'] == 'yes_no_criteria']
    sub_criteria_data = {k: v['sub_criteria'] for k, v in criteria_data.items()}
    comments_data = {k: v['comments'] for k, v in criteria_data.items()}

    prompt = f"""
Evaluate the provided document using the specified criteria.

### Scored Criteria (Rate 1-10):
{scored_criteria}

### Yes/No Criteria (Answer 'Yes' if explicit evidence is present, otherwise 'No'):
{yes_no_criteria}

### Sub-Criteria:
{sub_criteria_data}

### Comments:
{comments_data}

### Document:
{document_text}

---

### Output Requirements:
1. **HTML Report:**
   - Include an executive summary and detailed evaluations.
   - Separate each criterion with a horizontal line (`<hr>`).
   - For scored criteria, include the criterion name, score (X/10), page references, strengths, and weaknesses.
   - For Yes/No criteria, provide the answer and justification with page references.
   - Include sub-criteria and related comments in the evaluation, and include page references.
   - Output only the HTML content (no markdown or code block indicators).
   - **Ensure that all tables include data for each criterion, even if it's a placeholder or explicitly states 'No data found'.**

2. **JSON Data:**
   - Return a structured JSON array with keys: `Criterion`, `{document_name} Score`, `Weighting (%)` for {scored_criteria}, and `Criterion`, `{document_name} Yes/No` for {yes_no_criteria}.
   - Include sub-criteria and comments in the JSON output.
   - Include all criteria, even if no data is found.
   - Present JSON after a `### JSON Output:` header.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that evaluates documents."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    evaluation_text = response.choices[0].message.content

    evaluation_text = re.sub(r'\n{3,}', '\n\n', evaluation_text).strip()
    evaluation_text = re.sub(r'\n\s*\n', '\n', evaluation_text).strip()
    evaluation_text = re.sub(r'^\s*\n', '', evaluation_text)

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






def detect_criteria_type_new(df):
    criteria_data = {}
    current_criterion = None

    for index, row in df.iterrows():
        print(f"Processing row {index}: {row.tolist()}")
        if pd.notna(row.iloc[0]):  # Check if the first column is not empty
            if pd.notna(row.iloc[1]):  # Main criterion with value in second column
                current_criterion = row.iloc[0]
                value = str(row.iloc[1]).strip().lower()

                print(f"Found main criterion: {current_criterion} with value: {value}")

                if value.isdigit():
                    criteria_type = 'scored_criteria'
                    weighting = float(value)
                elif value in ['y', 'n', 'yes', 'no', 'y/n']:
                    criteria_type = 'yes_no_criteria'
                    weighting = None
                else:
                    criteria_type = 'unknown'
                    weighting = None

                criteria_data[current_criterion] = {
                    'sub_criteria': [],
                    'type': criteria_type,
                    'weighting': weighting,
                    'comments': []
                }
            else:
                if current_criterion:
                    sub_criterion_data = {
                        'name': row.iloc[0],
                        'comments': row.iloc[2].split('\n') if len(row) > 2 and pd.notna(row.iloc[2]) else []
                    }
                    print(f"Adding sub-criterion to {current_criterion}: {sub_criterion_data}")
                    criteria_data[current_criterion]['sub_criteria'].append(sub_criterion_data)
        elif current_criterion and len(row) > 2 and pd.notna(row.iloc[2]):
            comments = row.iloc[2].split('\n')
            print(f"Adding comment to {current_criterion}: {comments}")
            criteria_data[current_criterion]['comments'].extend(comments)

    print("Final criteria data:")
    print(criteria_data)

    weightings = {criterion: data['weighting'] for criterion, data in criteria_data.items() if data['type'] == 'scored_criteria'}

    scored_criteria = {k: v for k, v in criteria_data.items() if v['type'] == 'scored_criteria'}
    yes_no_criteria = {k: v for k, v in criteria_data.items() if v['type'] == 'yes_no_criteria'}

    print("Scored Criteria Detected:")
    for k, v in scored_criteria.items():
        print(f"{k}: Weighting = {v['weighting']}, Sub-criteria = {len(v['sub_criteria'])}")

    print("\nYes/No Criteria Detected:")
    for k, v in yes_no_criteria.items():
        print(f"{k}: Weighting = {v['weighting']}, Sub-criteria = {len(v['sub_criteria'])}")


    return criteria_data, weightings



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
    else:
        df = pd.read_csv(criteria_path, header=None)

    #scored_criteria, yes_no_criteria, weightings = detect_criteria_type(df)

    #testing of detect_criteria_type_new 
    criteria_data, weightings = detect_criteria_type_new(df)

    print(f"✅ Successfully evaluated {len(criteria_data)} criteria with sub-criteria and comments.")


    all_parsed_results = []
    evaluations = []

    redacted_files = [f for f in os.listdir(app.config['REDACTED_FOLDER']) if f != ".cleared"]

    if not redacted_files:
        print("❌ No redacted files found for evaluation!")
        return jsonify({"error": "No redacted files found for evaluation."}), 400

    print(f"✅ Evaluating {len(redacted_files)} redacted files...")

    for redacted_filename in redacted_files:
        redacted_path = os.path.join(app.config['REDACTED_FOLDER'], redacted_filename)

        with open(redacted_path, 'r', encoding="utf-8") as redacted_file:
            redacted_text = redacted_file.read()

        evaluation_result = evaluate_document_new(redacted_text, criteria_data, redacted_filename)
        print(f"✅ Evaluation complete for {redacted_filename} with {len(criteria_data)} criteria.")

        html_match = re.search(r"^(.*?)### JSON Output:", evaluation_result, re.DOTALL)
        html_part = html_match.group(1).strip() if html_match else evaluation_result.strip()
        
        print("✅ Extracted HTML Part:", html_part[:500])  # ✅ Debugging first 500 characters

        # ✅ **NEW: Extract JSON using regex to avoid parsing errors**
        json_match = re.search(r'\[\s*{.*?}\s*\]', evaluation_result, re.DOTALL)

        if json_match:
            json_part = json_match.group(0)  # ✅ **Extract matched JSON content**
            print("✅ Extracted JSON Part:", json_part)  # ✅ **Debugging step**
        else:
            print("❌ JSON Extraction Failed:", evaluation_result)  # ❌ **Debugging failure case**
            return jsonify({"error": "AI response does not contain valid JSON."}), 500


        try:
            parsed_result = json.loads(json_part)  # ✅ **Convert JSON text into Python list**
            evaluations.append({"document": redacted_filename, "evaluation": html_part})  # ✅ Store HTML part
            all_parsed_results.extend(parsed_result)

        except json.JSONDecodeError as err:
            print("❌ JSON Parsing Error:", str(err))  # ❌ **Handles JSON decoding errors**
            print("🔍 Full Response:", evaluation_result)  # 🔍 **Debugging AI response**
            return jsonify({"error": f"Invalid JSON format from AI response: {str(err)}"}), 500

            
    # Log JSON to check validity
    try:
        json_string = json.dumps({"evaluations": evaluations}, ensure_ascii=False)
        print("🔄 JSON Response:", json_string)
    except Exception as e:
        print("❌ JSON Encoding Error:", e)


    # clear REDACTED_FOLDER after evaluation
    folder_path = app.config['REDACTED_FOLDER']
    
    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Delete file or symlink
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Delete subdirectory
        print("✅ REDACTED_FOLDER has been cleared after evaluation.")
    except Exception as e:
        print(f"⚠️ Error clearing REDACTED_FOLDER: {e}")


    print("🔍 Debug: all_parsed_results (first 5 entries):", all_parsed_results[:5])
    print("🔍 Debug: Total parsed results count:", len(all_parsed_results))


    print("🔍 Debug: Full JSON Parsed Data Before Creating DataFrame:")
    for entry in all_parsed_results:
      print(entry)

    # Generate and return the evaluation table
    df_scores, df_yes_no = generate_evaluation_tables(all_parsed_results, weightings)

    print("🔍 Debug: df_scores shape:", df_scores.shape)
    print("🔍 Debug: df_yes_no shape:", df_yes_no.shape)

    # Convert to HTML only after checking emptiness
    df_scores_html = df_scores.to_html(classes='table table-bordered', escape=False) if not df_scores.empty else "<p>No scored criteria.</p>"
    df_yes_no_html = df_yes_no.to_html(classes='table table-bordered', escape=False) if not df_yes_no.empty else "<p>No Yes/No criteria.</p>"

    return jsonify({
        "evaluation_table": df_scores_html,
        "yes_no_table": df_yes_no_html,
        "evaluations": evaluations
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002)
