import streamlit as st
from PIL import Image
import numpy as np

# --- BACKGROUND IMAGE CSS ---
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1576091160550-2173dba999ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80");
    background-size: cover;
    background-attachment: fixed;
}
.main-box {
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-box">', unsafe_allow_html=True)

st.title("🦴 MedVision Hospital - Salem")
st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=80)

# --- PATIENT DETAILS ---
name = st.text_input("Patient Name")
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", 1, 100, 25)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
with col2:
    report_type = st.selectbox("Report Type", ["X-Ray", "MRI", "CT Scan"])

notes = st.text_area("Patient Notes")

# --- UPLOAD ---
file = st.file_uploader(f"Upload {report_type} Report", type=["jpg","png","jpeg"])

if file:
    img = Image.open(file)
    st.image(img, width=350)

    # Validation - Only Report Allowed
    arr = np.array(img.convert("RGB"))
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    if np.mean(np.abs(r.astype(int) - g.astype(int))) > 12:
        st.error("❌ Only medical reports allowed")
        st.stop()

    # Fracture Logic
    gray = np.array(img.convert("L"))
    fracture = np.sum(gray < 40) > 5000

    st.divider()
    st.write(f"**Patient:** {name} | Age: {age} | Gender: {gender}")
    st.write(f"**Notes:** {notes}")

    if fracture:
        st.error("🔴 Fracture Detected")
        # Background related image for fracture
        st.image("https://img.freepik.com/free-vector/broken-bone-concept-illustration_114360-15188.jpg", width=250)
        st.warning("**Precautions:**\n- Immobilize the pain/affected area \n-Give Ice pack in pain /affected area as FIRST AID\n- Consult Doctor Immediately")
    else:
        st.success("✅ Patient is Perfect - No Fracture Found")
        # Background related image for healthy
        st.image("https://img.freepik.com/free-vector/healthy-lifestyle-concept-illustration_114360-14939.jpg", width=250)
        st.info("**Precautions:**\n-Add more calcium in diet to maintain same condition\n- Do work out or Exercise for 30 min \n- Stay Healthy and be brisk")

st.markdown('</div>', unsafe_allow_html=True)
