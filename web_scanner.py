import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import io
import datetime

# --- MODERN UI CONFIG ---
st.set_page_config(page_title="UltraScan Desktop", layout="wide", page_icon="🚀")

# Custom CSS for a sleek 'Developer' look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e2129; border-radius: 10px; color: white; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; }
    div.stButton > button:first-child { background-color: #007bff; color: white; border-radius: 8px; width: 100%; border: none; }
    div.stDownloadButton > button:first-child { background-color: #28a745; color: white; border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 UltraScan Pro")
st.caption("Desktop Edition | Version 2.0 | High-Compression Logic")

# --- SIDEBAR: GLOBAL SETTINGS ---
with st.sidebar:
    st.header("⚙️ Tech Settings")
    target_kb = st.number_input("Target Size (KB)", min_value=10, max_value=500, value=95)
    
    with st.expander("Scanner Filters"):
        contrast = st.slider("Contrast Boost", 1.0, 3.0, 1.8)
        brightness = st.slider("Brightness", 0.5, 2.0, 1.1)
        sharpness = st.slider("Sharpness", 1.0, 5.0, 2.0)
    
    st.divider()
    if st.button("🔄 Reset App"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN INTERFACE TABS ---
tab1, tab2 = st.tabs(["📸 1. CAPTURE & UPLOAD", "🪄 2. ENHANCE & DOWNLOAD"])

with tab1:
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Source Input")
        src_type = st.radio("Select Input Device:", ["Phone Webcam", "PC File Upload"], horizontal=True)
        bill_label = st.text_input("Bill Reference Name", placeholder="e.g. Amazon_Receipt")
        
        if src_type == "Phone Webcam":
            st.info("💡 Pro Tip: Select your phone (Iriun/DroidCam) in your browser camera settings.")
            raw_img = st.camera_input("Scanner View")
        else:
            raw_img = st.file_uploader("Drop image here", type=['jpg', 'jpeg', 'png'])

    with col_b:
        st.subheader("Orientation")
        rotation = st.segmented_control("Rotate Image", [0, 90, 180, 270], default=0)
        if raw_img:
            preview_img = Image.open(raw_img).convert('RGB')
            if rotation != 0:
                preview_img = preview_img.rotate(rotation, expand=True)
            st.image(preview_img, caption="Aligned Scan", use_container_width=True)

# --- TAB 2: THE MAGIC ---
with tab2:
    if raw_img:
        st.subheader("Scanner Processing Engine")
        
        def process_image(image, kb_limit, c, b, s):
            scale = 1.0
            qual = 90
            while True:
                buf = io.BytesIO()
                # 1. Grayscale & Enhance
                work_img = ImageOps.grayscale(image)
                work_img = ImageEnhance.Contrast(work_img).enhance(c)
                work_img = ImageEnhance.Brightness(work_img).enhance(b)
                work_img = ImageEnhance.Sharpness(work_img).enhance(s)
                
                # 2. Resizing Loop
                new_w = int(work_img.width * scale)
                new_h = int(work_img.height * scale)
                work_img = work_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # 3. Save as PDF
                work_img.save(buf, format="PDF", quality=qual, optimize=True)
                current_size = buf.tell() / 1024
                
                if current_size <= kb_limit or scale < 0.15:
                    return buf.getvalue(), current_size
                
                scale -= 0.1
                qual -= 5

        if st.button("⚡ EXECUTE COMPRESSION"):
            with st.status("Analyzing document texture...", expanded=True) as status:
                st.write("Applying Grayscale filters...")
                st.write("Optimizing pixel density...")
                final_pdf, final_kb = process_image(preview_img, target_kb, contrast, brightness, sharpness)
                status.update(label=f"Complete! Final Size: {final_kb:.1f} KB", state="complete")
            
            st.success(f"File optimized successfully to {final_kb:.1f} KB")
            
            # Smart Naming
            date_str = datetime.date.today().strftime("%d-%m-%y")
            clean_name = bill_label.replace(" ", "_") if bill_label else "scan"
            final_filename = f"{clean_name}_{date_str}.pdf"
            
            st.download_button(
                label=f"⬇️ Download {final_filename}",
                data=final_pdf,
                file_name=final_filename,
                mime="application/pdf"
            )
    else:
        st.warning("⚠️ Please capture or upload an image in Tab 1 first.")
