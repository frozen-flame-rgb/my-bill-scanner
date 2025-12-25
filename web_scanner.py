import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Precision Scanner", layout="centered")

st.title("📑 Pro Precision Scanner")
st.write("Crop your notes manually to keep them clear under 100KB.")

# --- THE COMPRESSION LOGIC (Universal Version) ---
def compress_to_100kb(image_list, target_kb=98):
    # This detects if your system uses old or new Pillow names to prevent crashes
    resample_method = getattr(Image, 'Resampling', Image).LANCZOS
    
    scale, quality = 1.0, 95
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            width, height = img.size
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, resample_method)
            processed.append(resized)
        
        # Merge all pages into one PDF
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size_kb = buf.tell() / 1024
        
        if size_kb <= target_kb:
            return buf.getvalue(), size_kb
        
        scale -= 0.05
        if scale < 0.5 and quality > 40:
            quality -= 5
        if scale < 0.05:
            return buf.getvalue(), size_kb

# --- SESSION STATE ---
if 'scanned_pages' not in st.session_state:
    st.session_state.scanned_pages = []

# --- THE INTERFACE ---
st.divider()
user_filename = st.text_input("1. File Name:", "My_Notes_Scan")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

st.subheader("2. Add & Crop Pages")
uploaded_file = st.file_uploader("Upload a clear photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file).convert('RGB')
    
    st.info("📐 **Crop:** Drag the blue lines to select your notes. Tap the middle to move the box.")
    
    # FIXED: Removed 'should_resize_canvas' to stop the TypeError
    cropped_img = st_cropper(
        img, 
        realtime_update=True, 
        box_color='#007bff', 
        aspect_ratio=None  # Allows free cropping from all sides
    )
    
    if st.button("➕ Add This Page"):
        st.session_state.scanned_pages.append(cropped_img)
        st.success(f"Page {len(st.session_state.scanned_pages)} added!")

# --- FINAL PDF ---
if st.session_state.scanned_pages:
    st.divider()
    st.subheader(f"3. Final PDF Preview ({len(st.session_state.scanned_pages)} pages)")
    
    cols = st.columns(3)
    for i, p in enumerate(st.session_state.scanned_pages):
        cols[i % 3].image(p, use_container_width=True)
    
    if st.button("🚀 Create 100KB PDF", type="primary"):
        with st.spinner("Processing..."):
            pdf_data, final_size = compress_to_100kb(st.session_state.scanned_pages)
            st.success(f"Success! Final Size: {final_size:.2f} KB")
            
            date_str = datetime.datetime.now().strftime('%d_%m')
            st.download_button(label=f"⬇️ Download PDF", 
                               data=pdf_data, 
                               file_name=f"{clean_name}_{date_str}.pdf", 
                               mime="application/pdf")
    
    if st.button("🗑️ Reset All"):
        st.session_state.scanned_pages = []
        st.rerun()
