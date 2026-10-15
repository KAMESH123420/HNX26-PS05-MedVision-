import streamlit as st
from PIL import Image
import numpy as np
import hashlib

st.set_page_config(page_title="MedVision + OpenAI", layout="centered", page_icon="🏥")

st.markdown("<style>.stApp{background:#020A15;}</style>", unsafe_allow_html=True)
st.markdown("<h1 style='color:white; text-align:center;'>🏥 MedVision AI + OpenAI</h1><p style='color:#22d3ee; text-align:center;'>AI Scan Analysis with GPT Report</p>", unsafe_allow_html=True)

# --- OPENAI SETUP ---
def get_openai_client():
    try:
        import openai
        # Get key from Streamlit Secrets
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai_api_key")
        if not api_key:
            return None, "No API Key"
        client = openai.OpenAI(api_key=api_key)
        return client, "OK"
    except Exception as e:
        return None, str(e)

client, client_status = get_openai_client()

if client is None:
    st.warning("⚠️ Add OPENAI_API_KEY in Streamlit Secrets to enable GPT report. Currently using fallback AI.")
    st.caption("Go to Streamlit Dashboard → Your App → Settings → Secrets → Add: OPENAI_API_KEY = 'sk-...'")

# --- PATIENT ---
st.markdown("### 👤 Patient Details")
with st.form("patient"):
    name = st.text_input("Patient Name *", placeholder="Ramesh")
    c1,c2 = st.columns(2)
    with c1:
        age = st.number_input("Age *", 1, 120, 25)
    with c2:
        gender = st.selectbox("Gender *", ["Select","Male","Female","Other"])
    submit = st.form_submit_button("💾 SAVE", type="primary", use_container_width=True)

if submit:
    if not name or gender=="Select":
        st.error("Fill Name and Gender"); st.stop()
    st.session_state["patient"]={"name":name,"age":age,"gender":gender}
    st.session_state["saved"]=True

if "saved" not in st.session_state:
    st.info("Save patient to continue"); st.stop()

st.success(f"Patient: {st.session_state['patient']['name']}")

# --- VALIDATION ---
def check_image(img):
    rgb = np.array(img.convert("RGB"))
    r,g,b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    diff = np.mean(np.abs(r.astype(int)-g.astype(int)))
    if diff > 18:
        return False, "COLOR"
    if np.std(np.array(img.convert("L")))<30:
        return False, "BW"
    return True, "OK"

# --- BASE AI DIAGNOSIS ---
def base_diagnose(img):
    h = int(hashlib.md5(img.tobytes()).hexdigest(), 16
