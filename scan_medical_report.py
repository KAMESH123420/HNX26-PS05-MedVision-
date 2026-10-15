#!/usr/bin/env python3
"""
Medical Report Scanner AI - Standalone Single Script
===================================================
Scans medical lab report images (photos/PDFs) or raw text with Gemini 3.8 Flash,
extracts structured biomarkers, reference intervals, flags abnormal markers,
and verifies clinical findings with live NCBI PubMed peer-reviewed literature.

Requirements:
    pip install google-genai
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from google import genai
from google.genai import types

# 1. Initialize Gemini Client (Uses GEMINI_API_KEY environment variable)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    print("Run: export GEMINI_API_KEY='your_key_here'")
    sys.exit(1)

client = genai.Client(api_key=api_key)

CLINICAL_PROMPT = """
You are an expert Clinical Laboratory Scientist & Medical Diagnostic AI.
Analyze the provided medical report document.
Carefully extract:
1. Report Title & Specimen type.
2. Complete biomarkers table with:
   - name (e.g. Alanine Aminotransferase)
   - canonicalSymbol (e.g. ALT)
   - measuredValue
   - unit (e.g. mg/dL, U/L, g/dL)
   - referenceRange
   - status: EXACTLY one of: "NORMAL", "HIGH", "LOW", "CRITICAL"
   - category (e.g. Hepatic, Renal, Hematology, Lipid, Endocrine)
   - interpretation: 1-sentence clinical explanation of this value.
3. Synthesized Clinical Impressions (key physiological patterns).
4. Potential Differential Considerations to discuss with a physician.
5. Any medications mentioned.

Return strict, valid JSON matching this schema:
{
  "reportTitle": "string",
  "specimen": "string",
  "summary": "string",
  "biomarkers": [
    {
      "name": "string",
      "canonicalSymbol": "string",
      "measuredValue": "string",
      "unit": "string",
      "referenceRange": "string",
      "status": "NORMAL|HIGH|LOW|CRITICAL",
      "category": "string",
      "interpretation": "string"
    }
  ],
  "clinicalImpressions": ["string"],
  "potentialPathologies": ["string"],
  "medications": ["string"]
}
"""

def scan_medical_report_text(report_text: str) -> dict:
    """Scans raw clinical report text using Gemini 3.8 Flash."""
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"{CLINICAL_PROMPT}\n\nClinical Report Document:\n{report_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    return json.loads(response.text)

def scan_medical_report_image(image_path: str) -> dict:
    """Scans a medical report photo, scan, or PDF page from disk."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Determine MIME type based on file extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/png" if ext == ".png" else "application/pdf" if ext == ".pdf" else "image/jpeg"

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            CLINICAL_PROMPT
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    return json.loads(response.text)

def query_pubmed_literature(term: str, max_results: int = 3) -> list:
    """Science Skill: Searches NCBI PubMed for peer-reviewed studies on abnormal biomarkers."""
    try:
        encoded_term = urllib.parse.quote(term)
        esearch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={encoded_term}&sort=pub_date&retmode=json&retmax={max_results}&tool=MedScanAI"
        )
        req = urllib.request.Request(esearch_url, headers={"User-Agent": "MedScanAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            pmids = data.get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        pmid_str = ",".join(pmids)
        esummary_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"db=pubmed&id={pmid_str}&retmode=json&tool=MedScanAI"
        )
        req_sum = urllib.request.Request(esummary_url, headers={"User-Agent": "MedScanAI/1.0"})
        with urllib.request.urlopen(req_sum, timeout=5) as response:
            sum_data = json.loads(response.read().decode())
            result_dict = sum_data.get("result", {})

            articles = []
            for pmid in pmids:
                item = result_dict.get(pmid, {})
                articles.append({
                    "pmid": pmid,
                    "title": item.get("title", "Clinical Study"),
                    "journal": item.get("source", "PubMed Journal"),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
            return articles
    except Exception as e:
        print(f"PubMed query notice: {e}")
        return []

# -----------------------------------------------------------------------------
# Demo Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    sample_report = """
    COMPREHENSIVE METABOLIC PANEL (CMP)
    Specimen: Serum | Patient: 52yo Male | Fasting: Yes
    
    Glucose, Fasting: 142 mg/dL       (HIGH,   Ref: 70 - 99)
    BUN: 18 mg/dL                     (NORMAL, Ref: 7 - 20)
    Creatinine, Serum: 0.95 mg/dL     (NORMAL, Ref: 0.70 - 1.30)
    eGFR: 89 mL/min/1.73m2            (NORMAL, Ref: > 60)
    Sodium: 140 mmol/L                (NORMAL, Ref: 136 - 145)
    Potassium: 4.4 mmol/L             (NORMAL, Ref: 3.5 - 5.1)
    ALT (SGPT): 84 U/L                (HIGH,   Ref: 9 - 46)
    AST (SGOT): 58 U/L                (HIGH,   Ref: 10 - 40)
    Total Bilirubin: 1.1 mg/dL        (NORMAL, Ref: 0.2 - 1.2)
    
    Medications: Metformin 500mg, Atorvastatin 20mg
    """

    print("=" * 60)
    print("1. Scanning Clinical Report with Gemini 3.8 Flash...")
    print("=" * 60)
    
    # To scan an image file instead, use:
    # result = scan_medical_report_image("path/to/blood_test.jpg")
    result = scan_medical_report_text(sample_report)
    
    print(f"Report: {result.get('reportTitle')} (Specimen: {result.get('specimen')})")
    print(f"Summary: {result.get('summary')}\n")

    print("=" * 60)
    print("2. Extracted Biomarkers Table:")
    print("=" * 60)
    for b in result.get("biomarkers", []):
        flag = f"[{b['status']}]"
        print(f"• {b['name']} ({b.get('canonicalSymbol')}): {b['measuredValue']} {b['unit']} (Ref: {b['referenceRange']}) {flag}")
        print(f"  Interpretation: {b.get('interpretation')}")

    print("\n" + "=" * 60)
    print("3. Synthesized Clinical Impressions:")
    print("=" * 60)
    for imp in result.get("clinicalImpressions", []):
        print(f"- {imp}")

    # Science Skill: Search PubMed for abnormal markers
    abnormal_markers = [b["name"] for b in result.get("biomarkers", []) if b["status"] in ["HIGH", "LOW", "CRITICAL"]]
    if abnormal_markers:
        print("\n" + "=" * 60)
        query = f"{abnormal_markers[0]} clinical management diagnosis"
        print(f"4. NCBI PubMed Evidence Verification for: '{query}'")
        print("=" * 60)
        citations = query_pubmed_literature(query)
        for c in citations:
            print(f"→ {c['title']}")
            print(f"  Journal: {c['journal']} | PMID: {c['pmid']} | {c['url']}\n")
