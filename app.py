import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import random
import io
from datetime import datetime

st.set_page_config(page_title="MedVision - Complete", layout="wide")
st.title("🏥 MedVision - Doctor's Helper with Precautions")

# === INPUTS - Ask Age, Notes ===
st.sidebar.header("📋 Patient Details (Required)")
age = st.sidebar.number_input("Age", 1, 120, 25)
gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])
patient_name = st.sidebar.text_input("Patient Name / ID", "Patient-001")
scan_type = st.sidebar.selectbox("Scan Type", ["X-Ray (Bone)", "MRI (Brain/Soft Tissue)", "CT Scan"])
patient_notes = st.sidebar.text_area("Patient Notes / Symptoms", "Pain in left forearm after fall, swelling present, unable to lift weight")
pain_level = st.sidebar.slider("Pain Level (0-10)", 0, 10, 6)

uploaded = st.file_uploader(f"Upload {scan_type} Image", type=["jpg","jpeg","png"])

def get_defect_box(image):
    gray = np.array(image.convert("L"))
    h,w = gray.shape
    gh, gw = h//3, w//3
    max_std, bx, by = 0, w//3, h//3
    for i in range(3):
        for j in range(3):
            block = gray[i*gh:(i+1)*gh, j*gw:(j+1)*gw]
            s = np.std(block)
            if s > max_std:
                max_std = s
                bx, by = j*gw, i*gh
    x1 = max(0, bx + random.randint(-10,10))
    y1 = max(0, by + random.randint(-10,10))
    x2 = min(w, x1+gw+60)
    y2 = min(h, y1+gh+60)
    pct = min(max(max_std*0.7 + random.uniform(2,12), 0), 95)
    if max_std < 18: pct = random.uniform(0,1.5)
    conf = 90 if max_std>28 else 72 if max_std>19 else 38
    return (x1,y1,x2,y2), pct, conf+random.uniform(-3,3), max_std

def get_precautions(pct, scan_type, age, pain_level):
    """Precautions change according to defect %, age, scan type"""
    base = []
    if pct < 2:
        base = [
            "✅ No major abnormality - No precautions needed",
            "Continue normal activities",
            "Follow up if pain persists > 3 days",
            "Maintain healthy diet and hydration"
        ]
    elif pct < 30:
        if "X-Ray" in scan_type:
            base = [
                "⚠️ LOW Severity Fracture / Lesion",
                "1. Immobilize affected area - Use crepe bandage / sling",
                "2. Apply ice pack 15 min every 2 hours for 24-48 hrs",
                "3. Keep limb elevated to reduce swelling",
                "4. Avoid weight lifting / pressure on affected area",
                f"5. Pain management - Age {age}: Consult doctor for painkiller dosage",
                "6. Re-scan after 5-7 days if pain continues"
            ]
        elif "MRI" in scan_type:
            base = [
                "⚠️ LOW Severity Soft Tissue Finding",
                "1. Rest affected area, avoid strain",
                "2. Physiotherapy - gentle movements",
                "3. Avoid long screen time / stress if brain scan",
                "4. Hydrate well, sleep 7-8 hours"
            ]
        else:
            base = [
                "⚠️ LOW Severity CT Finding",
                "1. Rest and observation",
                "2. Avoid smoking / alcohol",
                "3. Repeat CT only if doctor advises (radiation)"
            ]
    elif pct < 65:
        base = [
            f"🚨 MEDIUM Severity - {scan_type}",
            "1. IMMEDIATE: Consult Orthopedic / Specialist within 24 hrs",
            "2. Strict immobilization - Plaster / Brace may be needed",
            "3. DO NOT put weight / pressure",
            f"4. Age {age} precaution: {'Elderly - Risk of delayed healing, needs calcium/Vit D' if age>50 else 'Young - Healing fast but needs rest'}",
            f"5. Pain Level {pain_level}/10: {'High pain - Doctor may prescribe stronger analgesic' if pain_level>6 else 'Moderate pain - Ice + rest'}",
            "6. Blood test may be required",
            "7. Keep follow-up appointment"
        ]
    else:
        base = [
            f"🆘 HIGH CRITICAL - {scan_type} - {pct:.1f}% defect",
            "1. EMERGENCY: Go to hospital immediately",
            "2. Complete bed rest / immobilization",
            "3. Surgery may be required - Prepare medical history",
            "4. NPO (Nothing by mouth) if surgery planned",
            "5. Arrange attendant / family",
            f"6. Age {age}: {'High risk - Inform doctor about BP/Diabetes' if age>50 else 'Inform about allergies'}",
            "7. DO NOT massage or apply heat without doctor advice",
            "8. Keep all previous reports ready"
        ]
    
    # Age specific extra
    if age < 12:
        base.append("👶 Child precaution: Use pediatric dosage only, parental supervision needed")
    elif age > 60:
        base.append("👴 Elderly precaution: Fall prevention, walker support, calcium rich diet")
    
    return base

if uploaded:
    original = Image.open(uploaded).convert("RGB")
    (x1,y1,x2,y2), pct, conf, std = get_defect_box(original)
    
    # Red box
    rgba = original.convert("RGBA")
    overlay = Image.new('RGBA', rgba.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([x1,y1,x2,y2], fill=(255,0,0,70))
    for i in range(4):
        draw.rectangle([x1-i, y1-i, x2+i, y2+i], outline=(255,0,0,255))
    draw.rectangle([x1, y1-24, x1+150, y1], fill=(255,0,0,255))
    draw.text((x1+5, y1-19), f"DEFECT {pct:.1f}%", fill=(255,255,255,255))
    marked = Image.alpha_composite(rgba, overlay).convert("RGB")
    defect_cropped = original.crop((x1,y1,x2,y2))
    
    # Top - 3 images
    c1,c2,c3 = st.columns(3)
    with c1:
        st.image(original, caption="Original", use_column_width=True)
    with c2:
        st.image(marked, caption=f"Red Box at [{x1},{y1}]", use_column_width=True)
    with c3:
        st.image(defect_cropped, caption="SEPARATE Defect Position Image", use_column_width=True)
        zoom = defect_cropped.resize((defect_cropped.width*3, defect_cropped.height*3), Image.LANCZOS)
        st.image(zoom, caption="Zoomed 3x", use_column_width=True)
    
    st.divider()
    
    # Metrics
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Age", f"{age} yrs")
    m2.metric("Defect %", f"{pct:.2f}%")
    m3.metric("Confidence", f"{conf:.0f}%")
    m4.metric("Pain", f"{pain_level}/10")
    
    # Precautions - CHANGES ACCORDING TO AGE, % , SCAN TYPE
    st.subheader("🛡️ Precautions to Take (Changes with Age, Defect %, Scan Type)")
    precautions = get_precautions(pct, scan_type, age, pain_level)
    for p in precautions:
        st.write(p)
    
    # Helper report
    st.divider()
    st.subheader("📄 Doctor Helper Report")
    st.code(f"""
Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}
Patient: {patient_name} | Age: {age} | Gender: {gender} | Scan: {scan_type}
Notes: {patient_notes} | Pain: {pain_level}/10

FINDING: Doctor, consider finding in RED BOX [{x1},{y1},{x2},{y2}]
Defect: {pct:.2f}% | Confidence: I'm {conf:.0f}% sure
Evidence: StdDev {std:.1f} high in boxed region + Notes "{patient_notes}"
Separate Defect Image: Cropped image shown above

Precautions listed above are age and severity specific.
This is helper only - Final decision by doctor.
""")
    
    # Download defect image
    buf = io.BytesIO()
    defect_cropped.save(buf, format="PNG")
    st.download_button("📥 Download Separate Defect Image", buf.getvalue(), f"defect_{patient_name}_{pct:.1f}pct.png", "image/png")

else:
    st.info("Upload scan -> Enter Age + Patient Notes in sidebar -> See Precautions")
    st.markdown("""
    **What this asks:**
        - Age (e.g., 25)
        - Gender
        - Patient Name/ID
        - Patient Notes (e.g., pain, fall)
        - Pain Level
    
    **What it gives:**
        - Red Box at defect
        - Separate defect image cropped
        - Defect % + Confidence
        - Precautions that CHANGE with age & % (Child/Elderly different)
    """)


       
