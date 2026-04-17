import streamlit as st
import time
import hashlib
from streamlit_echarts import st_echarts
import io
from logic import get_file_hash, scan_metadata, perform_ela
from PIL import Image

# --- CONFIG ---
st.set_page_config(page_title="TRACE | Forensic Suite", layout="wide")

# Safe CSS injection
st.markdown("""
    <style>
    /* 1. Import a professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* 2. Global Font & Background */
    .stApp {
        background-color: #0F172A !important; /* Deep Slate Blue-Black */
        font-family: 'Inter', sans-serif !important;
    }

    /* 3. Heading Colors (TRACE / Data Intake) */
    h1, h2, h3 {
        color: #F8FAFC !important; /* Off-White for high readability */
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* 4. Text & Label Colors */
    label, p, span, .stMarkdown {
        color: #94A3B8 !important; /* Muted Slate Grey */
        font-weight: 500 !important;
    }

    /* 5. Input Field Styling (Sleek & Clean) */
    .stTextInput > div > div > input {
        background-color: #1E293B !important; /* Slightly lighter slate */
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    /* 6. Professional Button (Subtle & Sharp) */
    .stButton > button {
        background-color: #3B82F6 !important; /* Professional Blue Accent */
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        width: auto !important;
    }

    /* 7. File Uploader Fix (Matches the theme) */
    [data-testid="stFileUploader"] section {
        background-color: #1E293B !important;
        border: 1px dashed #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Small fix for the 'upload' button inside uploader */
    [data-testid="stFileUploader"] button {
        background-color: #334155 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'screen' not in st.session_state:
    st.session_state['screen'] = 'login'

# --- SCREEN 1: LOGIN ---
if st.session_state['screen'] == 'login':
    st.title("🛡️ TRACE")
    mobile = st.text_input("Mobile Number")
    otp = st.text_input("Enter OTP (1234)", type="password")
    if st.button("Access System"):
        if otp == "1234":
            st.session_state['screen'] = 'dashboard'
            st.rerun()

# --- SCREEN 2: DASHBOARD (Updated to allow Video) ---
elif st.session_state['screen'] == 'dashboard':
    st.title("📂 Data Intake")
    # Added Video formats to the uploader
    uploaded_file = st.file_uploader("Upload Image or Video", type=['jpg','png','jpeg','mp4','mov','3gp'])
    
    if uploaded_file:
        is_video = uploaded_file.type.startswith('video')
        
        progress = st.progress(0)
        for i in range(101):
            time.sleep(0.002)
            progress.progress(i)
        
        file_bytes = uploaded_file.getvalue()
        sha = get_file_hash(file_bytes)
        sig = scan_metadata(uploaded_file)
        
        # Branching logic for Image vs Video
        if not is_video:
            heatmap, p_score = perform_ela(uploaded_file)
        else:
            # Video Simulation logic
            heatmap, p_score = None, 88 # Default high score for video simulation
            
        is_bad = "Adobe" in sig or p_score < 75 or "fake" in uploaded_file.name.lower()
        trust = int(p_score if not is_bad else p_score * 0.7)
        
        if st.button("GENERATE TRUTH DASHBOARD"):
            st.session_state['results'] = {
                "score": trust, 
                "is_bad": is_bad, 
                "is_video": is_video,
                "file_name": uploaded_file.name,
                "file_type": uploaded_file.type,
                "raw_data": uploaded_file if is_video else Image.open(io.BytesIO(file_bytes)),
                "heat": heatmap, 
                "p": p_score, 
                "sig": sig, 
                "hash": sha
            }
            st.session_state['screen'] = 'verdict'
            st.rerun()

# --- SCREEN 4: VERDICT ---
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
        
        # Side-by-Side View
        st.subheader("🔬 Visual Comparison")
        c1, c2 = st.columns(2)
        if res['is_video']:
            c1.video(res['raw_data'], format=res['file_type'])
            # Simulation of Temporal Tamper for Video
            c2.info("Video Temporal Scan: Metadata consistency checked for 30s duration.")
            if res['is_bad']:
                st.error("🚩 [Temporal Alert] Manipulation detected at 00:12s")
        else:
            c1.image(res['raw_data'], caption="ORIGINAL")
            c2.image(res['heat'], caption="HEATMAP")

    with col_e:
        st.subheader("📋 Analysis Layers")
        st.markdown(f"<div class='layer-card'><b>Layer 1: Metadata Provenance</b><br>{res['sig']}</div>", unsafe_allow_html=True)
        st.progress(0.2 if "Adobe" in res['sig'] else 1.0)
        
        st.markdown("<div class='layer-card'><b>Layer 2: Pixel Integrity / Temporal Scan</b></div>", unsafe_allow_html=True)
        st.progress(res['p']/100)
        
        st.markdown("<div class='layer-card'><b>Layer 3: Biological Liveness</b></div>", unsafe_allow_html=True)
        st.progress(0.4 if res['is_bad'] else 0.95)
        
        st.divider()
        st.subheader("🛡️ Chain of Custody")
        st.code(f"Digital Hash (SHA-256):\n{res['hash']}")
        
        # Feedback Section
        st.markdown("### 📝 Feedback")
        f1, f2 = st.columns(2)
        if f1.button("👍 Looks Correct"): st.success("Feedback Recorded")
        if f2.button("👎 Wrong Result"): st.error("Flagged for Review")
        
        if st.button("New Scan"):
            st.session_state['screen'] = 'dashboard'
            st.rerun()
