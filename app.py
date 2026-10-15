import streamlit as st
import base64

# CONFIG
st.set_page_config(page_title="MedVision AI", layout="wide")

# READ YOUR SKELETON IMAGE (upload skeleton.jpg to same folder as app.py)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""  # fallback

# If you have skeleton.png in repo, use it. Otherwise uses online placeholder
b64_skeleton = get_base64_image("skeleton.png")
if b64_skeleton:
    img_src = f"data:image/png;base64,{b64_skeleton}"
else:
    # Your actual skeleton - fallback embedded (small version)
    img_src = "https://i.ibb.co/3mJ7yQ5Z/skeleton.png"  # replace with your path

# HTML + CSS - Now INSIDE Python correctly
html_code = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@800&display=swap');
.liquid-nav{{background:linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04)); backdrop-filter:blur(40px); border:1px solid rgba(255,255,255,0.18);}}
@keyframes float{{0%,100%{{transform:translateY(0) scale(1); filter:drop-shadow(0 0 20px #00D9FF)}}50%{{transform:translateY(-10px) scale(1.02); filter:drop-shadow(0 0 35px #00D9FF)}}}}
.skeleton{{animation:float 4s ease-in-out infinite}}
</style>

<div style="position:relative; width:100%; height:92vh; background:#020A15; border-radius:20px; overflow:hidden; font-family:'Inter',sans-serif;">

  <div style="position:absolute; top:16px; left:50%; transform:translateX(-50%); width:92%; height:54px; border-radius:999px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; z-index:20;" class="liquid-nav">
    <div style="color:white; font-weight:bold;">✦ MedScan AI</div>
    <div style="display:flex; gap:28px; color:rgba(255,255,255,0.5); font-size:13px;"><span style="color:white;">Home</span><span>About</span><span>Pricing</span></div>
    <div style="display:flex; gap:8px;"><button style="padding:6px 16px; border-radius:999px; background:rgba(255,255,255,0.1); color:white; font-size:12px; border:none;">Log in</button><button style="padding:6px 16px; border-radius:999px; background:#2563eb; color:white; font-size:12px; border:none;">Get Started</button></div>
  </div>

  <div style="position:absolute; left:5%; top:25%; width:45%; z-index:10;">
    <h1 style="color:white; font-size:64px; font-weight:800; line-height:0.9; margin:0;">Here is your<br>medical<br>Helper</h1>
    <p style="color:rgba(255,255,255,0.4); font-size:12px; margin-top:20px; max-width:340px;">An AI second-opinion system for doctors. Reads X-ray/CT, localizes abnormalities, gives evidence-backed findings.</p>
    <div style="display:flex; gap:12px; margin-top:28px;">
      <button style="padding:12px 28px; border-radius:999px; background:linear-gradient(90deg,#22d3ee,#2563eb); color:white; font-size:14px; font-weight:bold; border:none;">↗ Upload X-RAY</button>
      <button style="padding:12px 28px; border-radius:999px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.7); font-size:14px;">▶ View Demo</button>
    </div>
  </div>

  <div style="position:absolute; right:0; top:8%; width:55%; height:88%; display:flex; align-items:flex-end; justify-content:center;">
    <img src="{img_src}" class="skeleton" style="height:90%; object-fit:contain; margin-bottom:20px;">
  </div>
</div>
"""

st.markdown(html_code, unsafe_allow_html=True)

# YOUR ORIGINAL AI LOGIC BELOW - KEEP IT
# st.title("MedVision AI Backend")
# ... rest of your app.py ...
