import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
import io
import re
import fitz  # PyMuPDF
import pytesseract

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MedVision - Medical Report Analyzer",
    layout="wide",
    page_icon="🩺"
)

st.title("🩺 MedVision - Medical Report Analyzer")
st.caption(
    "Reads written medical reports and highlights reported findings. "
    "It does not diagnose the uploaded scan image itself."
)

# ============================================================
# SIDEBAR - PATIENT DETAILS
# ============================================================

st.sidebar.header("👤 Patient Details")

patient_name = st.sidebar.text_input(
    "Patient Name",
    "John Doe"
)

patient_id = st.sidebar.text_input(
    "Patient ID",
    "PAT-001"
)

age = st.sidebar.number_input(
    "Age",
    min_value=1,
    max_value=100,
    value=25
)

gender = st.sidebar.selectbox(
    "Gender",
    ["Male", "Female", "Other"]
)

symptoms = st.sidebar.text_area(
    "Symptoms",
    "Pain in forearm, swelling, difficulty moving"
)

st.sidebar.divider()

# ============================================================
# SCAN DETAILS
# ============================================================

st.sidebar.header("🩻 Report Details")

scan_type = st.sidebar.selectbox(
    "Type of Report",
    [
        "X-Ray",
        "MRI",
        "CT Scan",
        "Ultrasound",
        "Blood Test",
        "Other"
    ]
)

scan_date = st.sidebar.date_input("Report Date")

# ============================================================
# MEDICAL FINDING KEYWORDS
# ============================================================

FINDING_RULES = {

    "Fracture": [
        "fracture",
        "fractured",
        "break in bone",
        "bone break",
        "hairline fracture",
        "stress fracture",
        "comminuted fracture",
        "displaced fracture",
        "non displaced fracture"
    ],

    "Dislocation": [
        "dislocation",
        "dislocated",
        "subluxation",
        "subluxed"
    ],

    "Swelling": [
        "swelling",
        "edema",
        "oedema",
        "soft tissue swelling"
    ],

    "Inflammation": [
        "inflammation",
        "inflammatory",
        "inflammation noted"
    ],

    "Infection": [
        "infection",
        "infected",
        "abscess",
        "pus",
        "infective"
    ],

    "Lesion": [
        "lesion",
        "lesions"
    ],

    "Tumor / Mass": [
        "tumor",
        "tumour",
        "mass",
        "neoplasm",
        "growth"
    ],

    "Arthritis": [
        "arthritis",
        "osteoarthritis",
        "degenerative changes"
    ],

    "Tear": [
        "tear",
        "torn",
        "ligament tear",
        "tendon tear",
        "meniscal tear"
    ],

    "Bleeding": [
        "bleeding",
        "hemorrhage",
        "haemorrhage",
        "hematoma",
        "haematoma"
    ],

    "Fluid": [
        "fluid collection",
        "effusion",
        "fluid accumulation"
    ],

    "Abnormality": [
        "abnormal",
        "abnormality",
        "abnormalities",
        "suspicious finding",
        "significant finding"
    ]
}

# Words that generally indicate a negative finding.
NEGATIVE_WORDS = [
    "no ",
    "no evidence",
    "without",
    "negative for",
    "normal",
    "unremarkable",
    "not seen",
    "not identified",
    "absence of",
    "free from"
]


# ============================================================
# OCR FUNCTIONS
# ============================================================

def preprocess_image(image):
    """
    Prepare a scanned report image for OCR.
    This does NOT perform medical image analysis.
    """

    image = image.convert("RGB")

    # Convert to grayscale for OCR only.
    gray = image.convert("L")

    # Increase contrast.
    arr = np.array(gray)

    # Simple thresholding.
    threshold = 180
    binary = np.where(arr > threshold, 255, 0).astype(np.uint8)

    processed = Image.fromarray(binary)

    return processed


def extract_text_from_image(image):
    """
    Extract written text from a report image using OCR.
    """

    processed = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed,
        config="--psm 6"
    )

    return text.strip()


def extract_text_from_pdf(pdf_bytes):
    """
    Extract text from a PDF.

    First attempts normal PDF text extraction.
    If the PDF is scanned, OCR is performed on its pages.
    """

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    all_text = []

    for page in document:

        text = page.get_text("text").strip()

        if text:
            all_text.append(text)

        else:
            # Scanned PDF page.
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            ocr_text = extract_text_from_image(img)

            if ocr_text:
                all_text.append(ocr_text)

    document.close()

    return "\n\n".join(all_text).strip()


# ============================================================
# REPORT TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Clean OCR/text extraction output.
    """

    text = text.replace("\x00", " ")

    # Remove excessive spaces.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# FIND MEDICAL FINDINGS
# ============================================================

def contains_negative_context(sentence, keyword):
    """
    Determine whether a finding is negated.

    Example:
    'No fracture is seen.'

    should not be reported as an actual fracture.
    """

    keyword_position = sentence.lower().find(
        keyword.lower()
    )

    if keyword_position == -1:
        return False

    before_keyword = sentence[
        max(0, keyword_position - 80):
        keyword_position
    ].lower()

    for negative_word in NEGATIVE_WORDS:
        if negative_word in before_keyword:
            return True

    return False


def split_into_sentences(text):
    """
    Split report into approximate sentences/lines.
    """

    # Keep line structure because medical reports often
    # use headings such as Findings / Impression.
    lines = text.splitlines()

    sentences = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Further split long lines.
        parts = re.split(
            r"(?<=[.!?])\s+",
            line
        )

        for part in parts:

            part = part.strip()

            if len(part) > 2:
                sentences.append(part)

    return sentences


def detect_findings(text):
    """
    Detect medical findings mentioned in the written report.

    This is text analysis only.
    """

    sentences = split_into_sentences(text)

    findings = []

    for sentence in sentences:

        lower_sentence = sentence.lower()

        for finding_type, keywords in FINDING_RULES.items():

            matched_keyword = None

            for keyword in keywords:

                if keyword.lower() in lower_sentence:

                    if not contains_negative_context(
                        sentence,
                        keyword
                    ):
                        matched_keyword = keyword
                        break

            if matched_keyword:

                findings.append({
                    "finding": finding_type,
                    "keyword": matched_keyword,
                    "sentence": sentence
                })

                break

    return findings


# ============================================================
# RED BOX HIGHLIGHTING
# ============================================================

def create_highlight_image(
    text,
    findings,
    width=1400
):
    """
    Create a visual report representation.

    The relevant finding text is displayed inside a RED BOX.

    This is text highlighting, not X-ray/MRI image analysis.
    """

    lines = []

    for sentence in text.splitlines():

        sentence = sentence.strip()

        if sentence:
            lines.append(sentence)

    if not lines:
        lines = ["No readable text found."]

    # Font
    try:
        font = ImageFont.truetype(
            "DejaVuSans.ttf",
            28
        )
    except:
        font = ImageFont.load_default()

    try:
        bold_font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            30
        )
    except:
        bold_font = font

    line_height = 48

    height = max(
        500,
        len(lines) * line_height + 100
    )

    canvas = Image.new(
        "RGB",
        (width, height),
        "white"
    )

    draw = ImageDraw.Draw(canvas)

    y = 40

    for line in lines:

        is_finding = False

        for finding in findings:

            if finding["sentence"] in line:

                is_finding = True
                break

        # Wrap long lines.
        max_chars = 75

        wrapped_lines = [
            line[i:i + max_chars]
            for i in range(
                0,
                len(line),
                max_chars
            )
        ]

        for wrapped in wrapped_lines:

            if is_finding:

                bbox = draw.textbbox(
                    (0, 0),
                    wrapped,
                    font=bold_font
                )

                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                padding = 12

                draw.rectangle(
                    [
                        20,
                        y - padding,
                        min(
                            width - 20,
                            text_width + 45
                        ),
                        y + text_height + padding
                    ],
                    outline="red",
                    width=5
                )

                draw.text(
                    (30, y),
                    wrapped,
                    fill="black",
                    font=bold_font
                )

            else:

                draw.text(
                    (30, y),
                    wrapped,
                    fill="black",
                    font=font
                )

            y += line_height

    return canvas


# ============================================================
# PRECAUTIONS
# ============================================================

def get_general_information(findings):

    if not findings:

        return [
            "No specific abnormal finding was detected in the report text.",
            "Continue follow-up according to the treating doctor."
        ]

    information = []

    finding_names = list(
        dict.fromkeys(
            [f["finding"] for f in findings]
        )
    )

    for finding in finding_names:

        if finding == "Fracture":
            information.append(
                "Fracture is mentioned in the report. "
                "Consult the treating doctor or orthopedic specialist."
            )

        elif finding == "Dislocation":
            information.append(
                "Dislocation is mentioned in the report. "
                "Seek medical evaluation."
            )

        elif finding == "Swelling":
            information.append(
                "Swelling is mentioned in the report. "
                "Discuss the finding with the treating doctor."
            )

        else:
            information.append(
                f"{finding} is mentioned in the report. "
                "Discuss the finding with the appropriate medical professional."
            )

    return information


# ============================================================
# PATIENT INFORMATION
# ============================================================

st.subheader("📋 Patient Information")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Name", patient_name)
    st.metric("Age", age)

with c2:
    st.metric("Gender", gender)
    st.metric("ID", patient_id)

with c3:
    st.metric("Report Type", scan_type)
    st.write("**Symptoms:**")
    st.write(symptoms)


# ============================================================
# IMPORTANT PROJECT NOTICE
# ============================================================

st.divider()

st.info(
    "ℹ️ **Report-only mode:** MedVision analyzes the written medical "
    "report using text extraction/OCR. It does NOT analyze X-ray, "
    "MRI, CT, or ultrasound pixels to diagnose abnormalities."
)


# ============================================================
# FILE UPLOAD
# ============================================================

st.divider()

st.subheader(
    f"📤 Upload {scan_type} Medical Reports"
)

st.write(
    "Upload a PDF report or an image containing the written report."
)

uploaded_files = st.file_uploader(
    "Choose medical reports",
    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png"
    ],
    accept_multiple_files=True
)


# ============================================================
# ANALYSIS
# ============================================================

if uploaded_files:

    results = []

    for file in uploaded_files:

        st.divider()

        st.write(
            f"### 📄 Processing: `{file.name}`"
        )

        extracted_text = ""

        highlighted_image = None

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        if file.name.lower().endswith(".pdf"):

            pdf_bytes = file.read()

            try:

                extracted_text = extract_text_from_pdf(
                    pdf_bytes
                )

            except Exception as e:

                st.error(
                    f"Could not read PDF: {e}"
                )

                continue

        # ----------------------------------------------------
        # IMAGE REPORT
        # ----------------------------------------------------

        else:

            try:

                image = Image.open(file)

                extracted_text = extract_text_from_image(
                    image
                )

            except Exception as e:

                st.error(
                    f"Could not read image: {e}"
                )

                continue

        # ----------------------------------------------------
        # CLEAN TEXT
        # ----------------------------------------------------

        extracted_text = clean_text(
            extracted_text
        )

        # ----------------------------------------------------
        # NO TEXT
        # ----------------------------------------------------

        if not extracted_text:

            st.warning(
                f"⚠️ `{file.name}` does not contain "
                "readable report text."
            )

            st.info(
                "If this is only an X-ray/MRI/CT image, "
                "MedVision will not attempt to diagnose it. "
                "Please upload the written radiology report."
            )

            results.append({
                "file": file.name,
                "status": "No readable report text",
                "findings": "None"
            })

            continue

        # ----------------------------------------------------
        # FINDINGS
        # ----------------------------------------------------

        findings = detect_findings(
            extracted_text
        )

        # ----------------------------------------------------
        # HIGHLIGHT IMAGE
        # ----------------------------------------------------

        highlighted_image = create_highlight_image(
            extracted_text,
            findings
        )

        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        finding_names = list(
            dict.fromkeys(
                [
                    finding["finding"]
                    for finding in findings
                ]
            )
        )

        if finding_names:

            finding_text = ", ".join(
                finding_names
            )

            status = "Finding detected"

        else:

            finding_text = "No abnormal finding detected"

            status = "No abnormal finding"


        results.append({
            "file": file.name,
            "status": status,
            "findings": finding_text,
            "text": extracted_text,
            "finding_objects": findings,
            "highlight": highlighted_image
        })


    # ========================================================
    # RESULTS
    # ========================================================

    if results:

        st.divider()

        st.subheader("📊 Analysis Summary")

        # Only actual findings.
        detected_results = [
            r for r in results
            if r.get("finding_objects")
        ]

        if detected_results:

            st.error(
                f"🔴 Medical findings mentioned in "
                f"{len(detected_results)} report(s)"
            )

        else:

            st.success(
                "🟢 No abnormal finding was detected "
                "in the readable report text."
            )


        # ====================================================
        # TABLE
        # ====================================================

        table_data = []

        for index, result in enumerate(
            results,
            start=1
        ):

            table_data.append({
                "Report": f"R{index}",
                "File": result["file"],
                "Status": result["status"],
                "Finding": result["findings"]
            })

        df = pd.DataFrame(
            table_data
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # INDIVIDUAL REPORTS
        # ====================================================

        st.divider()

        st.subheader(
            "🔎 Detailed Report Analysis"
        )

        for index, result in enumerate(
            results,
            start=1
        ):

            st.markdown(
                f"## Report {index}: {result['file']}"
            )

            if "finding_objects" not in result:

                st.warning(
                    "No report text available."
                )

                continue

            findings = result[
                "finding_objects"
            ]

            # ------------------------------------------------
            # FINDINGS
            # ------------------------------------------------

            if findings:

                st.error(
                    "🔴 Findings detected"
                )

                for finding in findings:

                    st.markdown(
                        f"""
                        **Finding:** `{finding['finding']}`

                        **Detected term:** `{finding['keyword']}`

                        **Report statement:**

                        > {finding['sentence']}
                        """
                    )

            else:

                st.success(
                    "🟢 No abnormal finding detected "
                    "from the report text."
                )


            # ------------------------------------------------
            # RED BOX REPORT
            # ------------------------------------------------

            st.subheader(
                "🟥 Report with Highlighted Findings"
            )

            st.image(
                result["highlight"],
                caption=(
                    "Red box = text containing a "
                    "detected medical finding"
                ),
                use_container_width=True
            )


            # ------------------------------------------------
            # ORIGINAL EXTRACTED TEXT
            # ------------------------------------------------

            with st.expander(
                "📄 View extracted report text"
            ):

                st.text(
                    result["text"]
                )


            # ------------------------------------------------
            # GENERAL INFORMATION
            # ------------------------------------------------

            st.subheader(
                "ℹ️ Follow-up Information"
            )

            for information in get_general_information(
                findings
            ):

                st.write(
                    f"- {information}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "⚠️ MedVision is a student/research prototype. "
    "Detected findings are based on text present in the uploaded "
    "medical report and are not a medical diagnosis. "
    "Always consult a qualified healthcare professional."
)
