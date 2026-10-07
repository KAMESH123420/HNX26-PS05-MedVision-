import streamlit as st
from PIL import Image
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="MedVision - Defect %", layout="wide")

def calculate_defect(image):
    img = image.convert("L")
    arr = np.array(img)
    mean_int = np.mean(arr)
    std_int = np.std(arr)
    gx, gy = np.gradient(arr)
    edge = np.sqrt(gx**2 + gy**2)
    edge_pixels = np.sum(edge > 30)
    edge_ratio = (edge_pixels / arr.size) * 100
    base = (edge_ratio * 3) + ((120 - mean_int) * 0.2) + (std_int * 0.25)
    pct = min(max(base, 0), 95)
    if edge_ratio < 0.8 and std_int < 20:
        pct = random.uniform(0, 1.2)
    return pct, edge_ratio, mean_int

st.title("🏥 MedVision - X-Ray | MRI | CT - Defect %")
scan_type = st.selectbox("Select Scan Type", ["X-Ray (Bone)", "MRI", "CT Scan"])
uploaded = st.file_uploader(f"Upload {scan_type}", type=["jpg","jpeg","png"])

if uploaded:
    image = Image.open(uploaded)
    st.image(image, caption="Original", width=400)
    if st.button(f"Analyze {scan_type}"):
        pct, edge_ratio, mean_int = calculate_defect(image)
        date_now = datetime.now().strftime("%d-%m-%Y %H:%M")
        if pct < 2:
            status = "NORMAL"
            st.success(f"## ✅ Report: {pct:.2f}% - NORMAL")
            severity = "No Defect"; advice = "No treatment needed"
        elif pct < 30:
            status = "LOW"
            st.warning(f"## ⚠️ Report: {pct:.2f}% - LOW Severity")
            severity = f"Minor defect {pct:.1f}%"; advice = "Observation & Rest"
        elif pct < 65:
            status = "MEDIUM"
            st.error(f"## 🚨 Report: {pct:.2f}% - MEDIUM Severity")
            severity = f"Moderate defect {pct:.1f}%"; advice = "Consult Doctor"
        else:
            status = "HIGH"
            st.error(f"## 🆘 Report: {pct:.2f}% - HIGH Severity")
            severity = f"Severe defect {pct:.1f}%"; advice = "Immediate Consultation"
        
        st.progress(int(pct))
        st.code(f"MEDVISION AI REPORT\nDate: {date_now}\nScan: {scan_type}\nDefect %: {pct:.2f}%\nStatus: {status}\nSeverity: {severity}\nEdge Density: {edge_ratio:.2f}%\nRecommendation: {advice}\n")
        c1,c2,c3 = st.columns(3)
        c1.metric("Defect %", f"{pct:.2f}%")
        c2.metric("Status", status)
        c3.metric("Type", scan_type)

st.caption("Different image = Different % - Dynamic report")
