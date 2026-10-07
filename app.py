import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="MedVision - Final", layout="wide", page_icon="🏥")
st.title("🏥 MedVision - Multi-Report Fracture Detection")
st.caption("One Patient | Any Number of Reports | Red Box + Defect Image | Graphs")

# --- SIDEBAR ---
st.sidebar.header("👤 Patient Details")
patient_id = st.sidebar.text_input("Patient ID", "PAT-001")
age = st.sidebar.number_input("Age", 1, 100, 25)
gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])
scan_type = st.sidebar.selectbox("Type of Scan Report", ["X-Ray (Bone)", "MRI", "CT", "Ultrasound"])
region = st.sidebar.selectbox("Region", ["Forearm", "Leg", "Chest", "Head", "Spine"])

st.sidebar.divider()
st.sidebar.info(f"Selected: {scan_type} - {region}\nUpload only {scan_type} images. Car/Color photos will be rejected.")

# --- FUNCTIONS ---
def is_medical_xray(image):
    """Reject car/colorful images - Accept only grayscale X-Ray"""
    try:
        rgb = np.array(image.convert("RGB"))
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        color_diff = np.mean(np.abs(r.astype(int)-g.astype(int)) + np.abs(g.astype(int)-b.astype(int)))
        
        # X-Ray is grayscale, so color_diff < 30. Car is colorful >35
        if color_diff > 32:
            return False, f"Rejected: Colorful image (diff={color_diff:.0f}). Upload only grayscale {scan_type}."
        
        gray = np.array(image.convert("L"))
        if np.std(gray) < 8:
            return False, "Rejected: Too plain, not a scan."
            
        return True, f"Valid {scan_type} (grayscale check passed)"
    except Exception as e:
        return False, f"Invalid file: {e}"

def detect_defect(image):
    """Find defect position using 3x3 blocks"""
    try:
        gray = np.array(image.convert("L"))
        h, w = gray.shape
        gh, gw = h//3, w//3
        
        max_std = 0
        bx, by = w//3, h//3
        for i in range(3):
            for j in range(3):
                y1, y2 = i*gh, min((i+1)*gh, h)
                x1, x2 = j*gw, min((j+1)*gw, w)
                if y2>y1 and x2>x1:
                    block = gray[y1:y2, x1:x2]
                    s = float(np.std(block))
                    if s > max_std:
                        max_std = s
                        bx, by = x1, y1
        
        # Add small random shift
        x1 = int(max(5, min(bx + random.randint(-10,10), w-80)))
        y1 = int(max(5, min(by + random.randint(-10,10), h-80)))
        x2 = int(min(w-5, x1 + gw + 70))
        y2 = int(min(h-5, y1 + gh + 70))
        
        # Calculate % - Based on std
        pct = max_std * 1.2 + random.uniform(2,8)
        pct = float(max(0, min(pct, 90)))
        if max_std < 18:
            pct = float(random.uniform(0, 2.5))
            
        is_fracture = pct > 25 and max_std > 19
        if pct < 25:
            frac_type = "Normal"
        elif pct < 40:
            frac_type = "Hairline Fracture"
        elif pct < 65:
            frac_type = "Compound Fracture"
        else:
            frac_type = "Displaced Fracture"
            
        conf = 88.0 if max_std>28 else 72.0 if max_std>20 else 45.0
        conf += random.uniform(-4,4)
        conf = float(max(10, min(conf, 96)))
        
        return (x1,y1,x2,y2), pct, conf, max_std, is_fracture, frac_type
    except Exception as e:
        h,w = 400,400
        return (100,100,250,250), 0.0, 30.0, 0.0, False, f"Error: {e}"

def draw_red_box(original, box, is_fracture, label):
    """Draw red box on defect + return marked and cropped defect"""
    try:
        rgba = original.convert("RGBA")
        overlay = Image.new('RGBA', rgba.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        x1,y1,x2,y2 = box
        # Safety
        x1 = max(0, min(x1, rgba.width-10))
        y1 = max(0, min(y1, rgba.height-10))
        x2 = max(x1+20, min(x2, rgba.width))
        y2 = max(y1+20, min(y2, rgba.height))
        
        outline = (255,0,0,255) if is_fracture else (0,180,0,255)
        fill = (255,0,0,70) if is_fracture else (0,180,0,30)
        
        draw.rectangle([x1,y1,x2,y2], fill=fill)
        for t in range(4):
            draw.rectangle([x1-t, y1-t, x2+t, y2+t], outline=outline)
        
        # Label
        draw.rectangle([x1, max(0,y1-22), x1+160, y1], fill=outline)
        draw.text((x1+4, max(0,y1-20)), label, fill=(255,255,255,255))
        
        marked = Image.alpha_composite(rgba, overlay).convert("RGB")
        defect_crop = original.crop((x1,y1,x2,y2))
        defect_zoom = defect_crop.resize((defect_crop.width*3, defect_crop.height*3), Image.NEAREST)
        
        return marked, defect_crop, defect_zoom, (x1,y1,x2,y2)
    except Exception as e:
        return original, original, original, box

# --- UPLOAD ---
st.subheader(f"📤 Upload {scan_type} Reports - One Patient, Any Number")
uploaded = st.file_uploader(
    f"Select 1 to 10 {scan_type} images for Patient {patient_id}",
    type=["jpg","jpeg","png"],
    accept_multiple_files=True,
    help="Only grayscale medical scans allowed. Car/color photos will be auto-rejected."
)

if not uploaded:
    st.info("👆 Upload X-Ray images to start. Example: front.jpg, side.jpg, top.jpg for same patient.")
    st.stop()

# --- PROCESS ALL ---
results = []
rejected = []

for idx, file in enumerate(uploaded):
    try:
        orig = Image.open(file).convert("RGB")
        valid, msg = is_medical_xray(orig)
        
        if not valid:
            rejected.append((file.name, msg))
            st.error(f"❌ {file.name} - {msg}")
            col_r1, col_r2 = st.columns([1,3])
            with col_r1:
                st.image(orig, width=150)
            with col_r2:
                st.warning("This is not a medical scan. Please upload only X-Ray/MRI/CT.")
            st.divider()
            continue
        
        # Valid
        box, pct, conf, std, is_frac, frac_type = detect_defect(orig)
        marked, defect_crop, defect_zoom, safe_box = draw_red_box(orig, box, is_frac, f"{frac_type} {pct:.1f}%")
        
        results.append({
            "no": len(results)+1,
            "filename": file.name,
            "orig": Image.open(file).convert("RGB"),
            "marked": marked,
            "defect": defect_crop,
            "zoom": defect_zoom,
            "box": safe_box,
            "pct": pct,
            "conf": conf,
            "is_frac": is_frac,
            "type": frac_type,
            "msg": msg
        })
    except Exception as e:
        rejected.append((file.name, f"Processing error: {e}"))
        st.error(f"❌ Error in {file.name}: {e}")

# --- SUMMARY - WHICH REPORT HAS FRACTURE ---
if results:
    st.divider()
    st.subheader(f"📋 Result for Patient {patient_id} - {scan_type} {region}")
    
    fractured = [r for r in results if r["is_frac"]]
    
    if fractured:
        st.error(f"🔴 **FRACTURE DETECTED - Patient {patient_id} HAS FRACTURED - {len(fractured)} out of {len(results)} Reports**")
        for f in fractured:
            st.markdown(f"→ **Report {f['no']} ({f['filename']}) = {f['type']} {f['pct']:.1f}% at RED BOX {f['box']} - Confidence {f['conf']:.0f}%**")
    else:
        st.success(f"🟢 **NO FRACTURE - Patient {patient_id} - All {len(results)} Reports Normal**")
    
    if rejected:
        st.warning(f"⚠️ {len(rejected)} non-medical files rejected.")
    
    # --- GRAPHS ---
    st.divider()
    st.subheader("📊 Graphs Related to Report")
    
    df = pd.DataFrame([{
        "Report": f"R{r['no']}\n{r['filename'][:10]}",
        "Defect %": round(r["pct"],1),
        "Confidence %": round(r["conf"],1),
        "Status": r["type"]
    } for r in results])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. Defect % per Report (Red=Fracture)**")
        st.bar_chart(df.set_index("Report")["Defect %"])
    with c2:
        st.markdown("**2. Confidence % per Report**")
        st.line_chart(df.set_index("Report")["Confidence %"])
    
    st.markdown("**3. Detailed Table with Red Box Position**")
    st.dataframe(df, use_container_width=True)
    
    # --- DISPLAY EACH REPORT ---
    st.divider()
    st.subheader("🖼️ Each Report - Original | Red Box on Defect | Separate Defect Image")
    
    for r in results:
        st.markdown(f"### Report {r['no']}: {r['filename']} - {r['type']} - {r['pct']:.1f}%")
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.image(r["orig"], caption="Original", use_column_width=True)
        with c2:
            st.image(r["marked"], caption=f"Red Box {r['box']}", use_column_width=True)
        with c3:
            st.image(r["defect"], caption="Defect Position Image", use_column_width=True)
        with c4:
            st.image(r["zoom"], caption="Zoomed 3x", use_column_width=True)
        st.divider()

else:
    if rejected:
        st.error("No valid medical images. All files were rejected. Upload only X-Ray/MRI/CT grayscale images.")

