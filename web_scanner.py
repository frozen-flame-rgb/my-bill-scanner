import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import io
import datetime

# --- UI SETUP ---
st.set_page_config(page_title="UltraScan Desktop", layout="wide")

st.markdown("""
    <style>
    .stCamera { border: 5px solid #007bff; border-radius: 15px; }
    div.stButton > button { height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 Professional Bill Scanner")
st.caption("Optimized for Desktop with Phone-Webcam support")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("🛠️ Image Fixers")
    st.write("Adjust these if the photo looks 'weird'")
    
    # Target Size
    target_kb = st.slider("Max File Size (KB)", 40, 150, 95)
    
    # Toned down defaults to avoid 'weird' look
    bright_val = st.slider("Light Boost (Digital Flash)", 0.8, 2.5, 1.2)
    cont_val = st.slider("Text Contrast", 1.0, 3.0, 1.5)
    sharp_val = st.slider("Fix Blur (Sharpness)", 1.0, 5.0, 1.5)
    
    st.divider()
    if st.button("Clear Memory"):
        st.rerun()

# --- MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Capture Scan")
    input_mode = st.radio("Input Source:", ["Live Camera", "Upload File"], horizontal=True)
    
    if input_mode == "Live Camera":
        st.info("🔦 Tip: If it's too dark, turn on your room lights or use the 'Light Boost' slider.")
        raw_file = st.camera_input("Scanner Window")
    else:
        raw_file = st.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])

with col2:
    st.subheader("2. Final PDF Preview")
    if raw_file:
        # Load Image
        img = Image.open(raw_file).convert('RGB')
        
        # --- ENHANCEMENT LOGIC ---
        def professional_clean(image):
            # 1. Soft Grayscale (Prevents 'weird' pixelation)
            processed = ImageOps.grayscale(image)
            
            # 2. Apply User Adjustments
            processed = ImageEnhance.Brightness(processed).enhance(bright_val)
            processed = ImageEnhance.Contrast(processed).enhance(cont_val)
            processed = ImageEnhance.Sharpness(processed).enhance(sharp_val)
            
            return processed

        cleaned_img = professional_clean(img)
        st.image(cleaned_img, caption="How the PDF will look", use_container_width=True)

        # --- COMPRESSION ENGINE ---
        if st.button("💾 Generate Optimized PDF"):
            scale = 1.0
            qual = 90
            
            while True:
                buf = io.BytesIO()
                # Resize based on scale
                w, h = cleaned_img.size
                resized = cleaned_img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
                
                resized.save(buf, format="PDF", quality=qual, optimize=True)
                size_kb = buf.tell() / 1024
                
                if size_kb <= target_kb or scale < 0.2:
                    st.success(f"Final Size: {size_kb:.1f} KB")
                    
                    # File naming
                    filename = f"Scan_{datetime.date.today().strftime('%b%d')}.pdf"
                    
                    st.download_button(
                        label=f"📥 Download {filename}",
                        data=buf.getvalue(),
                        file_name=filename,
                        mime="application/pdf"
                    )
                    break
                
                scale -= 0.1
                qual -= 5
    else:
        st.warning("Awaiting image input...")
