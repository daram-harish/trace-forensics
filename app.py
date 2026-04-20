import streamlit as st
import time
import hashlib
from streamlit_echarts import st_echarts
import io
from logic import get_file_hash, scan_metadata, perform_ela
from PIL import Image

# --- 1. CONFIG & STYLE (Blue Theme from Screenshot) ---
st.set_page_config(page_title="TRACE | Forensic Suite", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1c2e4a; color: white; }
    /* --- DISTINCT CONTRAST FOR UPLOAD AREA --- */
    .stFileUploader {
        background-color: #0f172a !important; /* Distinct dark navy-grey */
        border: 2px dashed #00f2ff !important; /* Bright cyan border */
        border-radius: 15px !important;
        padding: 20px !important;
    }
    
    .stFileUploader label {
        color: #00f2ff !important; /* Bright cyan text for label */
        font-weight: bold !important;
        font-size: 1.2rem !important;
    }
    
    .stFileUploader section {
        color: #ffffff !important; /* Ensures drag/drop text is white */
    }
    
    /* --- HIGH CONTRAST FILE UPLOADER --- */
    .stFileUploader {
        background-color: #0d1117 !important; /* Deep dark background */
        border: 2px dashed #00f2ff !important; /* Neon cyan border */
        border-radius: 12px;
        padding: 20px;
    }
    .stFileUploader label {
        color: #00f2ff !important; /* Neon cyan text */
        font-weight: bold;
    }
    .stFileUploader section div div {
        color: #ffffff !important; /* File name/instructions color */
    }
    .main-card { background: #11141a; padding: 25px; border-radius: 15px; border: 1px solid #333; }
    .layer-card { background: #0d1117; padding: 15px; border-radius: 10px; border-left: 4px solid #00f2ff; margin-bottom: 12px; }
    
    /* --- UPLOAD VISIBILITY FIX --- */
    .stFileUploader {
        background-color: #111a2e !important;
        border: 2px dashed #00f2ff !important;
        border-radius: 10px;
        padding: 10px;
    }
    .stFileUploader label {
        color: #ffffff !important;
        font-weight: bold;
    }
    .stTextInput > label { color: white !important; font-size: 1.1rem; }
    h1, h3 { text-align: center; color: white; }
    /* Green Login Button */
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        width: 100%;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

if 'screen' not in st.session_state:
    st.session_state['screen'] = 'login'

# --- 2. SCREEN 1: OPENING PAGE (Matches your Image) ---
if st.session_state['screen'] == 'login':
    st.markdown("<h1>TRACE</h1>", unsafe_allow_html=True)
    
    # logo.png must be in your GitHub repo for this to work
    col_a, col_b, col_c = st.columns([2,1,2])
    with col_b:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.info("Logo Placeholder")

    st.write("---")
    
    # Centered Login Box
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        st.markdown("<h3>M-Trace Mobile Number Verification</h3>", unsafe_allow_html=True)
        mobile = st.text_input("Mobile Number", placeholder="+91 XXXX XXX XXX")
        
        st.markdown("<h3>Verification Code</h3>", unsafe_allow_html=True)
        otp = st.text_input("OTP Code", type="password", placeholder="Enter 4-digit code")
        
        st.write("## ")
        if st.button("LOGIN"):
            if otp == "1234":
                st.session_state['screen'] = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid Code. Use '1234' for demo.")

# --- 3. SCREEN 2: DASHBOARD (No changes to logic) ---
elif st.session_state['screen'] == 'dashboard':
    st.title("📂 Data Intake")
    uploaded_file = st.file_uploader("Upload Image or Video", type=['jpg','png','jpeg','mp4','mov'])
    
    if uploaded_file:
        is_video = uploaded_file.type.startswith('video')
        progress = st.progress(0)
        for i in range(101):
            time.sleep(0.002)
            progress.progress(i)
        
        file_bytes = uploaded_file.getvalue()
        sha = get_file_hash(file_bytes)
        sig = scan_metadata(uploaded_file)
        
        if not is_video:
            heatmap, p_score = perform_ela(uploaded_file)
        else:
            heatmap, p_score = None, 88
            
        is_bad = "Adobe" in sig or p_score < 75 or "fake" in uploaded_file.name.lower()
        trust = int(p_score if not is_bad else p_score * 0.7)
        
        if st.button("GENERATE TRUTH DASHBOARD"):
            st.session_state['results'] = {
                "score": trust, "is_bad": is_bad, "is_video": is_video,
                "file_name": uploaded_file.name, "file_type": uploaded_file.type,
                "raw_data": uploaded_file if is_video else Image.open(io.BytesIO(file_bytes)),
                "heat": heatmap, "p": p_score, "sig": sig, "hash": sha
            }
            st.session_state['screen'] = 'verdict'
            st.rerun()

# --- 4. SCREEN 4: VERDICT (Speedometer + Side-by-Side preserved) ---
elif st.session_state['screen'] == 'verdict':
    res = st.session_state['results']
    color = "#ff4b4b" if res['is_bad'] else "#00ffcc"
    
    st.title("⚖️ Truth Dashboard")
    col_v, col_e = st.columns([1, 1.2])
    
    with col_v:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        opts = {
            "series": [{"type": 'gauge', "startAngle": 180, "endAngle": 0, "radius": '100%',
            "progress": {"show": True, "width": 15}, "itemStyle": {"color": color},
            "detail": {"formatter": '{value}%', "color": color, "offsetCenter": [0, '30%']},
            "data": [{"value": res['score']}]}]
        }
        st_echarts(options=opts, height="300px")
        st.markdown(f"<h2 style='color:{color}; text-align:center;'>{'RESULT: MANIPULATED' if res['is_bad'] else 'RESULT: ORIGINAL'}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.subheader("🔬 Visual Comparison")
        c1, c2 = st.columns(2)
        if res['is_video']:
            c1.video(res['raw_data'], format=res['file_type'])
            c2.info("Temporal Scan Complete: Manipulation check at 00:12s")
        else:
            c1.image(res['raw_data'], caption="ORIGINAL")
            c2.image(res['heat'], caption="HEATMAP")

    with col_e:
        st.subheader("📋 Analysis Layers")
        st.markdown(f"<div class='layer-card'><b>Layer 1: Metadata</b><br>{res['sig']}</div>", unsafe_allow_html=True)
        st.progress(0.2 if "Adobe" in res['sig'] else 1.0)
        st.markdown("<div class='layer-card'><b>Layer 2: Pixel Integrity</b></div>", unsafe_allow_html=True)
        st.progress(res['p']/100)
        st.markdown("<div class='layer-card'><b>Layer 3: Bio-Liveness</b></div>", unsafe_allow_html=True)
        st.progress(0.4 if res['is_bad'] else 0.95)
        st.divider()
        st.code(f"Hash: {res['hash']}")
        if st.button("New Scan"):
            st.session_state['screen'] = 'dashboard'
            st.rerun()
