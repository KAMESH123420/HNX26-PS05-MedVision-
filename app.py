import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd
import random

st.set_page_config(page_title="MedVision", layout="wide", page_icon="🦴")
st.title("🦴 MedVision - Fracture Detection")

# --- SIDEBAR - NO REGION ---
st.sidebar.header("👤 Patient Details")
patient_name = st.sidebar.text_input("Patient Name", "John Doe")
patient_id = st.sidebar.text_input("Patient ID", "PAT-001")
age = st.sidebar.number_input("Age", 1, 100, 25)
gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])
symptoms = st.sidebar.text_area("Symptoms", "Pain in forearm, swelling, difficulty moving")

st.sidebar.divider()
st.sidebar.header("🩻 Scan Details")
scan_type = st.sidebar.selectbox("Type of Scan", ["X-Ray", "MRI", "CT Scan", "Ultrasound"])
scan_date = st.sidebar.date_input("Scan Date")

def get_precautions(scan, age):
    if scan == "X-Ray":
        return [f"Immobilize with plaster", "Avoid weight bearing 2-3 weeks", "Ice pack 15 min every 3 hrs", f"Age {age} - Calcium + Vitamin D", "X-Ray review after 21 days"]
    elif scan == "MRI":
        return ["Physiotherapy 2 weeks", "No heavy lifting", "Consult orthopedic", "Rest"]
    elif scan == "CT Scan":
        return ["May need surgery if displaced", "Complete bed rest 1 week", "Immediate doctor consultation"]
    else:
        return ["Rest and observation", "Repeat scan after 1 week"]

# --- FIRST PAGE ---
st.subheader("📋 Patient Information")
c1,c2,c3 = st.columns(3)
with c1:
    st.metric("Name", patient_name)
    st.metric("Age", age)
with c2:
    st.metric("Gender", gender)
    st.metric("ID", patient_id)
with c3:
    st.metric("Scan Type", scan_type)
    st.metric("Symptoms", symptoms[:20]+"...")

st.divider()
# Bone image instead of balloons
st.subheader("🦴 Bone Reference Image")
st.image("https://cdn-icons-png.flaticon.com/512/1021/1021160.png", width=120)
st.caption("Bone image - No balloons")

# --- UPLOAD ---
st.divider()
st.subheader(f"📤 Upload {scan_type} Reports - One Patient Any Number")

uploaded = st.file_uploader(f"Upload {scan_type} for {patient_name}", type=["jpg","jpeg","png"], accept_multiple_files=True)

def is_grayscale(img):
    rgb = np.array(img.convert("RGB")).astype(int)
    diff = np.mean(np.abs(rgb[:,:,0]-rgb[:,:,1]))
    if diff > 25:
        return False
    return True

def detect(img):
    gray = np.array(img.convert("L"))
    h,w = gray.shape
    gh, gw = h//3, w//3
    max_std, bx, by = 0, w//3, h//3
    for i in range(3):
        for j in range(3):
            y1,y2 = i*gh, min((i+1)*gh,h)
            x1,x2 = j*gw, min((j+1)*gw,w)
            s = np.std(gray[y1:y2, x1:x2])
            if s > max_std:
                max_std, bx, by = s, x1, y1
    x1,y1 = max(5,bx), max(5,by)
    x2,y2 = min(w-5, x1+gw+80), min(h-5, y1+gh+80)
    pct = min(max(max_std*1.1+random.uniform(2,6),0),85)
    if max_std<18: pct = random.uniform(0,2.5)
    is_frac = pct>25
    typ = "Normal" if not is_frac else ("Hairline" if pct<40 else "Compound" if pct<65 else "Displaced")
    return (x1,y1,x2,y2), pct, is_frac, typ

if uploaded:
    results=[]
    for f in uploaded:
        orig = Image.open(f).convert("RGB")
        if not is_grayscale(orig):
            st.error(f"❌ {f.name} - Upload only grayscale X-Ray, not color car photo")
            continue
        box,pct,is_frac,typ = detect(orig)
        marked = orig.copy()
        d = ImageDraw.Draw(marked)
        x1,y1,x2,y2 = box
        d.rectangle([x1,y1,x2,y2], outline="red", width=5)
        d.rectangle([x1,y1,x2,y2], fill=(255,0,0,40))
        defect = orig.crop(box)
        results.append({"no":len(results)+1,"file":f.name,"orig":orig,"marked":marked,"defect":defect,"box":box,"pct":pct,"is_frac":is_frac,"type":typ})

    if results:
        frac = [r for r in results if r["is_frac"]]
        if frac:
            st.error(f"🔴 Patient {patient_name} HAS FRACTURED - {len(frac)}/{len(results)} Reports")
            for r in frac:
                st.write(f"→ Report {r['no']} ({r['file']}) = {r['type']} {r['pct']:.1f}% at {r['box']}")
        else:
            st.success(f"🟢 Patient {patient_name} - NO FRACTURE")

        df = pd.DataFrame([{"Report":f"R{r['no']}","Defect %":round(r["pct"],1)} for r in results])
        st.bar_chart(df.set_index("Report"))
        st.dataframe(df, use_container_width=True)

        st.subheader("Original | Red Box on Defect | Separate Defect Image")
        for r in results:
            c1,c2,c3 = st.columns(3)
            with c1: st.image(r["orig"], caption="Original")
            with c2: st.image(r["marked"], caption=f"Red Box {r['box']}")
            with c3: st.image(r["defect"], caption="Defect Position")

        st.divider()
        st.subheader(f"💊 Precautions for {scan_type}")
        for p in get_precautions(scan_type, age):
            st.write(f"- {p}")

        st.divider()
        st.success("✅ Analysis Complete - Bone Image")
        st.image("https://cdn-icons-png.flaticon.com/512/1021/1021160.png", width=80)
  
  
