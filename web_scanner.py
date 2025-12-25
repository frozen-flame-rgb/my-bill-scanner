import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Precision Scanner", layout="centered")

st.title("📑 Pro Precision Scanner")
st.write("Manually crop your notes for the best quality under 100KB.")

# --- THE COMPRESSION LOGIC (Compatible with all Pillow versions) ---
def compress_to_100kb(image_list, target_kb=98):
    scale, quality = 1.0, 95
    
    # Check for the correct Resampling attribute to avoid line 71 crashes
    resample_method = getattr(Image, 'Resampling', Image).LANCZOS

    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            width, height = img.size
            new_size = (int(width * scale), int(height * scale))
            # Safe resizing logic
            resized = img.resize(new_size, resample_method)
            processed.append(resized)
        
        # Save pages as a single PDF
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size = buf.tell() / 1024
        
        if size <= target_kb:
            return buf.getvalue(), size
        
        scale -= 0.05
        if scale < 0.5 and quality > 40:
            quality -= 5
        if scale < 0.05: 
            return buf.getvalue(), size

# --- INITIALIZE SESSION STATE ---
if 'scanned_pages' not in st.session_state:
    st.session_state.scanned_pages = []

# --- THE INTERFACE ---
st.divider()

# 1. File Naming
user_filename = st.text_input("1. Enter PDF Name:", "My_Notes_Scan")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

# 2. Upload and Crop
st.subheader("2. Add & Crop Pages")
uploaded_file = st.file_uploader("Upload or Take Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file).convert('RGB')
    
    st.info("📐 **Crop Logic:** Drag the sides of the box to select your notes. Tap the middle to move the box.")
    
    # The actual cropper call (Fixed for Line 71)
    cropped_img = st_cropper(
        img, 
        realtime_update=True, 
        box_color='#007bff', 
        aspect_ratio=None,
        should_resize_canvas=True
    )
    
    if st.button("➕ Add This Page"):
        st.session_state.scanned_pages.append(cropped_img)
        st.success(f"Page {len(st.session_state.scanned_pages)} added!")

# 3. Final Multi-Page Preview & Download
if st.session_state.scanned_pages:
    st.divider()
    st.subheader(f"3. Final PDF Preview ({len(st.session_state.scanned_pages)} pages)")
    
    cols = st.columns(3)
    for i, p in enumerate(st.session_state.scanned_pages):
        cols[i % 3].image(p, caption=f"Page {i+1}", use_container_width=True)
    
    col_run, col_clear = st.columns(2)
    
    with col_run:
        if st.button("🚀 Create 100KB PDF", type="primary"):
            with st.spinner("Processing sharp crops..."):
                pdf_data, final_size = compress_to_100kb(st.session_state.scanned_pages)
                
                st.success(f"Final Size: {final_size:.2f} KB")
                
                date_str = datetime.datetime.now().strftime('%d_%m')
                full_name = f"{clean_name}_{date_str}.pdf"
                
                st.download_button(label=f"⬇️ Download PDF", 
                                   data=pdf_data, 
                                   file_name=full_name, 
                                   mime="application/pdf")
    
    with col_clear:
        if st.button("🗑️ Reset Everything"):
            st.session_state.scanned_pages = []
            st.rerun()
