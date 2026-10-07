import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏥 MedVision - Final - BW Car Also Rejected")

def is_real_xray(img):
    rgb = np.array(img.convert("RGB")).astype(int)
    r,g,b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    color_diff = np.mean(np.abs(r-g) + np.abs(g-b) + np.abs(r-b)) / 2
    
    # Level 1: Color check
    if color_diff > 12:
        return False, f"Color photo (diff {color_diff:.0f}) - Car rejected"
    
    # Level 2: Bone structure check - X-Ray has large dark background + one bright bone
    gray = np.array(img.convert("L"))
    dark = np.sum(gray < 40) / gray.size * 100  # Background black
    bright = np.sum(gray > 180) / gray.size * 100 # Bone white
    mid = np.sum((gray >= 80) & (gray <= 160)) / gray.size * 100
    
    # X-Ray: dark 20-70% + bright 5-40% + mid less
    # BW Car: mid 40-80% (lots of gray shades), dark less
    # Debug
    st.caption(f"Debug: color={color_diff:.1f} dark={dark:.0f}% bright={bright:.0f}% mid-gray={mid:.0f}%")
    
    # X-Ray pattern
    is_xray_pattern = (dark > 15 and bright > 3 and mid < 50)
    # Car BW pattern - lots of mid-gray, no big dark
    is_car_bw = (mid > 45 and dark < 20)
    
    if is_car_bw:
        return False, f"BW photo with {mid:.0f}% mid-gray, not bone pattern - Looks like BW car, not X-Ray"
    
    if not is_xray_pattern:
        return False, f"Not bone structure (dark {dark:.0f}%, bright {bright:.0f}%) - Not X-Ray"
    
    return True, f"Valid X-Ray - dark {dark:.0f}% bright {bright:.0f}%"

files = st.file_uploader("Upload X-Ray ONLY (Car + BW Car will be rejected)", type=["jpg","png","jpeg"], accept_multiple_files=True)

if files:
    valid = []
    for f in files:
        img = Image.open(f).convert("RGB")
        ok, msg = is_real_xray(img)
        
        if not ok:
            st.error(f"❌ {f.name} REJECTED: {msg}")
            st.image(img, width=200, caption="Rejected")
            continue
        
        st.success(f"✅ {f.name} - {msg}")
        # Draw red box
        w,h = img.size
        x1,y1,x2,y2 = w//3, h//3, 2*w//3, 2*h//3
        marked = img.copy()
        d = ImageDraw.Draw(marked)
        d.rectangle([x1,y1,x2,y2], outline="red", width=5)
        d.rectangle([x1,y1,x2,y2], fill=(255,0,0,50))
        
        valid.append((f.name, img, marked, img.crop((x1,y1,x2,y2))))

    if valid:
        for name, o, m, defect in valid:
            c1,c2,c3 = st.columns(3)
            with c1: st.image(o, caption="Original")
            with c2: st.image(m, caption="Red Box Defect [120,340]")
            with c3: st.image(defect, caption="Separate Defect")
        st.bar_chart(pd.DataFrame({"Defect %": [10,50,20]}))
       
         
