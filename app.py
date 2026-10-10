from flask import Flask, request, jsonify, render_template
from PIL import Image
import numpy as np
from datetime import datetime

app = Flask(__name__)

# --- VALIDATORS FOR EACH MODALITY ---
def is_valid_xray(image):
    img_np = np.array(image)
    if len(img_np.shape)==3 and img_np.shape[2]==3:
        r,g,b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]
        if np.mean(np.abs(r.astype(int)-g.astype(int))) > 15:
            return False, "Color photo rejected. Please upload X-ray (grayscale)."
    return True, "Valid X-ray"

def is_valid_mri(image):
    # MRI can be grayscale but different contrast
    return True, "Valid MRI" # Add your MRI checks

def is_valid_ct(image):
    return True, "Valid CT"

def is_valid_ultrasound(image):
    # Ultrasound often has fan shape, text overlays
    img_np = np.array(image)
    # Ultrasound can be color Doppler, so allow color
    return True, "Valid Ultrasound"

VALIDATORS = {
    "xray": is_valid_xray,
    "mri": is_valid_mri,
    "ct": is_valid_ct,
    "ultrasound": is_valid_ultrasound
}

# --- CORE PREDICTION ---
def get_finding_for_modality(image, report_type, patient_info, clinical_notes):
    age = patient_info.get('age')
    gender = patient_info.get('gender')

    # Example: Use patient context (This is multimodal - image + notes + age/gender)
    # E.g., fracture risk higher in elderly, certain findings in gender

    # DUMMY MODEL - Replace with your real model per modality
    # You can load 4 models: model_xray, model_mri, model_ct, model_us

    if report_type == "xray":
        finding_text = "Fracture line suggestive"
    elif report_type == "mri":
        finding_text = "Ligament tear / Soft tissue abnormality"
    elif report_type == "ct":
        finding_text = "Hemorrhage / Fracture"
    elif report_type == "ultrasound":
        finding_text = "Fluid collection / Abnormal echogenicity"

    return {
        "finding": finding_text,
        "location": {"x1": 100, "y1": 100, "x2": 300, "y2": 300} if image else None,
        "confidence": 0.85,
        "evidence": {
            "image_evidence": f"{report_type.upper()} shows abnormality",
            "clinical_evidence": f"Patient: {patient_info['name']}, {age}Y/{gender}. Notes: {clinical_notes[:100]}",
            "patient_context": f"Age {age}, Gender {gender} considered"
        },
        "modality": report_type,
        "suggestion": f"Doctor, consider {finding_text} in this {age}Y {gender} patient - please correlate with {report_type.upper()}."
    }

def get_finding_from_report_text(report_text, report_type, patient_info):
    # For text reports - parse normal vs abnormal
    lower = report_text.lower()
    if "no" in lower and ("fracture" in lower or "abnormal" in lower or "normal" in lower):
        return {
            "finding": f"No abnormality in {report_type.upper()} report - Normal",
            "location": None,
            "confidence": 0.92,
            "evidence": {"clinical_evidence": report_text[:200]},
            "suggestion": f"Doctor, {report_type.upper()} report appears normal for {patient_info['age']}Y {patient_info['gender']}"
        }
    else:
        return {
            "finding": f"Abnormality mentioned in {report_type.upper()} report",
            "location": None,
            "confidence": 0.88,
            "evidence": {"clinical_evidence": report_text[:200]},
            "suggestion": f"Doctor, consider findings in {report_type.upper()} report"
        }

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # 1. Get Patient Details
    patient_info = {
        "name": request.form.get('patient_name', '').strip(),
        "age": request.form.get('patient_age', '').strip(),
        "gender": request.form.get('patient_gender', '').strip(),
    }
    report_type = request.form.get('report_type', 'xray').lower() # xray, mri, ct, ultrasound
    clinical_notes = request.form.get('notes', '')
    report_text = request.form.get('report_text', '').strip()

    # Validation: Patient details mandatory
    if not patient_info["name"] or not patient_info["age"] or not patient_info["gender"]:
        return jsonify({"error": "Patient Name, Age, Gender are required"}), 400

    try:
        age_int = int(patient_info["age"])
        if age_int < 0 or age_int > 120:
            raise ValueError()
    except:
        return jsonify({"error": "Invalid age (0-120)"}), 400

    # 2. Check input type
    has_image = 'image' in request.files and request.files['image'].filename!= ''

    # CASE A: Report text only
    if report_text and not has_image:
        finding = get_finding_from_report_text(report_text, report_type, patient_info)
        return jsonify({
            "patient": patient_info,
            "report_type": report_type,
            "input_type": "report_text",
            "findings": [finding],
            "timestamp": datetime.now().isoformat()
        })

    # CASE B: Image upload
    if has_image:
        img = Image.open(request.files['image'].file)

        # Validate based on selected modality
        validator = VALIDATORS.get(report_type, is_valid_xray)
        valid, msg = validator(img)

        if not valid:
            return jsonify({
                "error": msg,
                "patient": patient_info,
                "report_type": report_type,
                "message": f"Uploaded image does not match selected type {report_type.upper()}"
            }), 400

        finding = get_finding_for_modality(img, report_type, patient_info, clinical_notes)

        return jsonify({
            "patient": patient_info,
            "report_type": report_type,
            "input_type": "image",
            "image_quality": 0.91,
            "findings": [finding],
            "disclaimer": "AI second opinion only - final diagnosis by physician"
        })

    return jsonify({"error": "Upload either medical image or report text"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
