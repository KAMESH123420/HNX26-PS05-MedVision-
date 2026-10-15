import streamlit as st
import base64

st.set_page_config(page_title="MedVision AI", layout="wide")

# Load skeleton from repo - permanent, no imgbb
def get_img():
    try:
        with open("skeleton.jpg", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{b64}"
    except:
        try:
            with open("skeleton.png", "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{b64}"
        except:
            # Fallback - your skeleton embedded directly if file missing
            return "https://i.imgur.com/8Km9tLL.png"

img = get_img()

st.markdown(f"""
<style>
.stApp {{background:#020A15;}}
.liquid-nav{{background:linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04)); backdrop-filter:blur(40px); border:1px solid rgba(255,255,255,0.18);}}
@keyframes float{{0%,100%{{transform:translateY(0) scale(1); filter:drop-shadow(0 0 20px #00D9FF)}}50%{{transform:translateY(-8px) scale(1.02); filter:drop-shadow(0 0 35px #00D9FF)}}}}
.skeleton{{animation:float 4s ease-in-out infinite}}
</style>

<div style="position:relative; width:100%; height:88vh; background:#020A15; border-radius:24px; overflow:hidden; font-family:Inter,sans-serif; border:1px solid rgba(255,255,255,0.08);">
  <div style="position:absolute; top:18px; left:50%; transform:translateX(-50%); width:92%; height:54px; border-radius:999px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; z-index:30;" class="liquid-nav">
    <div style="color:white; font-weight:800;">✦ MedScan AI</div>
    <div style="display:flex; gap:28px; color:rgba(255,255,255,0.5); font-size:13px;"><span style="color:white;">Home</span><span>About</span><span>Pricing</span></div>
    <div style="display:flex; gap:8px;"><button style="padding:7px 18px; border-radius:999px; background:rgba(255,255,255,0.1); color:white; font-size:12px; border:none;">Log in</button><button style="padding:7px 18px; border-radius:999px; background:#2563eb; color:white; font-size:12px; border:none;">Get Started</button></div>
  </div>
  <div style="position:absolute; left:5%; top:28%; width:42%; z-index:20;">
    <h1 style="color:white; font-size:68px; font-weight:800; line-height:0.88; margin:0;">Here is your<br>medical<br>Helper</h1>
    <p style="color:rgba(255,255,255,0.4); font-size:12.5px; margin-top:20px; max-width:360px;">Instant AI second-opinion for doctors. Reads X-ray/CT, localizes abnormalities.</p>
    <div style="display:flex; gap:12px; margin-top:28px;">
      <button style="padding:13px 28px; border-radius:999px; background:linear-gradient(90deg,#22d3ee,#2563eb); color:white; font-size:14px; font-weight:700; border:none;">↗ Upload X-RAY</button>
      <button style="padding:13px 28px; border-radius:999px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.7); font-size:14px;">▶ View Demo</button>
    </div>
  </div>
  <div style="position:absolute; right:2%; top:10%; width:52%; height:86%; display:flex; align-items:flex-end; justify-content:center; z-index:10;">
    <img src="{img}" class="skeleton" style="height:92%; object-fit:contain;">
  </div>
  <div style="position:absolute; bottom:6%; left:50%; transform:translateX(-50%); width:40%; height:2px; background:#22d3ee; box-shadow:0 0 24px #22d3ee; border-radius:2px;"></div>
</div>
""", unsafe_allow_html=True)
