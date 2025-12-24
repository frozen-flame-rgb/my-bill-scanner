import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import io
import datetime
import re
import cv2
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Bill Scanner", layout="centered")

st.title("📑 Pro Document Scanner")
st.write("Since browsers can't use your phone's native hardware sensors, use **'Clean Mode'** to fix lighting and shadows.")

# --- THE "DEVELOPER" ENHANCEMENT LOGIC ---
def apply_clean_filter(image):
    """Uses OpenCV to remove shadows and brighten the 'paper' look."""
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # 1. Convert to Grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # 2. Adaptive Thresholding (This removes shadows and makes it look like a 'scan')
    # It calculates lighting locally, so it handles shadows in the corner of the page.
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2)
    
    # Convert back to PIL
    return Image.fromarray(th)

# --- COMPRESSION LOGIC (LANCZOS for Sharpness) ---
def compress_to_multi_page_pdf(image_list, target_kb=98):
    scale, quality = 1.0, 90
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            w, h = img.size
            # LANCZOS keeps text edges sharp
            resized = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            processed.append(resized)
        
        # Merge pages
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size = buf.tell() / 1024
        if size <= target_kb or scale < 0.1:
            return buf.getvalue(), size
        scale -= 0.1
        if scale < 0.5: quality -= 5

# --- THE INTERFACE ---
st.divider()
user_filename = st.text_input("1. File Name:", "My_Bill")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

# Feature selection
st.subheader("2. Enhancement Settings")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    use_clean_mode = st.toggle("✨ Enable Clean Mode (B&W Scan)", value=False)
with col_opt2:
    rotation_angle = st.radio("Rotate Clockwise:", [0, 90, 180, 270], horizontal=True)

uploaded_files = st.file_uploader("3. Upload Photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    raw_images = [Image.open(f).convert('RGB') for f in uploaded_files]
    final_processed_list = []
    
    st.subheader(f"Preview ({len(raw_images)} pages)")
    cols = st.columns(3)
    
    for i, img in enumerate(raw_images):
        # Apply Rotation
        if rotation_angle != 0:
            img = img.rotate(-rotation_angle, expand=True)
            
        # Apply Clean Filter if toggled
        if use_clean_mode:
            img = apply_clean_filter(img)
        
        final_processed_list.append(img)
        cols[i % 3].image(img, caption=f"Page {i+1}", use_container_width=True)

    st.divider()
    if st.button("🚀 Merge into 100KB PDF", type="primary"):
        with st.spinner("Processing..."):
            pdf_data, final_size = compress_to_multi_page_pdf(final_processed_list)
            st.success(f"Final Size: {final_size:.2f} KB")
            
            # Save name with current date
            date_str = datetime.datetime.now().strftime('%d_%m')
            st.download_button(f"⬇️ Download {clean_name}_{date_str}.pdf", pdf_data, f"{clean_name}_{date_str}.pdf", "application/pdf")
