import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Scanner", layout="centered")

st.title("📑Scanner")
st.write("Take/Upload a photo, **manually crop any side**, and add it to your 100KB PDF.")

# --- THE COMPRESSION LOGIC (High Quality, No Filters) ---
def compress_to_100kb(image_list, target_kb=98):
    """Shrinks raw images using pro-grade LANCZOS resizing to keep text sharp."""
    scale, quality = 1.0, 95
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            width, height = img.size
            # Use LANCZOS to maintain native camera sharpness
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            processed.append(resized)
        
        # Merge all pages into a single PDF
        processed[0].save(
            buf, 
            format="PDF", 
            save_all=True, 
            append_images=processed[1:], 
            quality=quality, 
            optimize=True
        )
        size_kb = buf.tell() / 1024
        
        if size_kb <= target_kb or scale < 0.1:
            return buf.getvalue(), size_kb
        
        # Iteratively shrink to hit the 100KB goal
        scale -= 0.05
        if scale < 0.5:
            quality -= 5

# --- INITIALIZE SESSION STATE ---
if 'scanned_pages' not in st.session_state:
    st.session_state.scanned_pages = []

# --- THE INTERFACE ---
st.divider()

# 1. Custom Naming (Letters and Numbers)
st.subheader("1. Name Your Bill")
user_name = st.text_input("Enter Name (e.g., GasBill01):", "My_Scan")
# Sanitize filename
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_name)

# 2. Upload and Crop
st.subheader("2. Add & Crop Page")
uploaded_file = st.file_uploader("📸 Tap 'Browse' then 'Camera' for full power", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Open native photo - NO FILTERS
    img = Image.open(uploaded_file).convert('RGB')
    
    st.info("📐 **Crop:** Drag any blue line or corner. Click the middle to move the whole box.")
    
    # aspect_ratio=None allows you to drag sides independently
    cropped_img = st_cropper(
        img, 
        realtime_update=True, 
        box_color='#007bff', 
        aspect_ratio=None,
        should_resize_canvas=True
    )
    
    if st.button("➕ Add This Cropped Page"):
        st.session_state.scanned_pages.append(cropped_img)
        st.success(f"Page {len(st.session_state.scanned_pages)} added!")

# 3. Preview & Download
if st.session_state.scanned_pages:
    st.divider()
    st.subheader(f"3. Final PDF Preview ({len(st.session_state.scanned_pages)} pages)")
    
    # Show thumbnails of added pages
    cols = st.columns(3)
    for i, p in enumerate(st.session_state.scanned_pages):
        cols[i % 3].image(p, caption=f"Page {i+1}", use_container_width=True)
    
    st.write("---")
    col_run, col_clear = st.columns(2)
    
    with col_run:
        if st.button("🚀 Create 100KB PDF", type="primary"):
            with st.spinner("Processing..."):
                pdf_data, final_size = compress_to_100kb(st.session_state.scanned_pages)
                
                st.success(f"Final Size: {final_size:.2f} KB")
                
                # Combine name with date
                date_str = datetime.datetime.now().strftime('%d_%m_%y')
                file_to_download = f"{clean_name}_{date_str}.pdf"
                
                st.download_button(
                    label=f"⬇️ Download {file_to_download}",
                    data=pdf_data,
                    file_name=file_to_download,
                    mime="application/pdf"
                )
    
    with col_clear:
        if st.button("🗑️ Reset All Pages"):
            st.session_state.scanned_pages = []
            st.rerun()
