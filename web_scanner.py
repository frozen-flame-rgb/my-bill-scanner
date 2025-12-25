import streamlit as st
from PIL import Image
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Mobile Precision Scanner", layout="centered")

st.title("📑 Mobile Precision Scanner")
st.write("Use the sliders to crop your notes. This is much easier on small screens than dragging boxes.")

# --- THE COMPRESSION LOGIC ---
def compress_to_100kb(image_list, target_kb=98):
    """Shrinks images using high-quality LANCZOS resizing."""
    scale, quality = 1.0, 95
    resample_method = getattr(Image, 'Resampling', Image).LANCZOS

    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            width, height = img.size
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, resample_method)
            processed.append(resized)
        
        # Merge all pages into a single PDF
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

# --- INITIALIZE SESSION STATE ---
if 'scanned_pages' not in st.session_state:
    st.session_state.scanned_pages = []

# --- THE INTERFACE ---
st.divider()

# 1. File Naming
user_filename = st.text_input("1. PDF Name:", "My_Notes")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

# 2. Upload and Crop
st.subheader("2. Upload & Precision Crop")
uploaded_file = st.file_uploader("Upload or Take Photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file).convert('RGB')
    width, height = img.size
    
    st.info("💡 **Mobile Tip:** Use the sliders below to trim the edges of your photo.")
    
    # Precision Sliders for Mobile
    left = st.slider("Left Crop", 0, width // 2, 0)
    right = st.slider("Right Crop", width // 2, width, width)
    top = st.slider("Top Crop", 0, height // 2, 0)
    bottom = st.slider("Bottom Crop", height // 2, height, height)
    
    # Apply the crop based on slider values
    # left, top, right, bottom
    cropped_img = img.crop((left, top, right, bottom))
    
    st.image(cropped_img, caption="Crop Preview", use_container_width=True)
    
    if st.button("➕ Add This Page"):
        st.session_state.scanned_pages.append(cropped_img)
        st.success(f"Page {len(st.session_state.scanned_pages)} added!")

# 3. Final Multi-Page Preview & Download
if st.session_state.scanned_pages:
    st.divider()
    st.subheader(f"3. PDF Preview ({len(st.session_state.scanned_pages)} pages)")
    
    cols = st.columns(3)
    for i, p in enumerate(st.session_state.scanned_pages):
        cols[i % 3].image(p, caption=f"Page {i+1}", use_container_width=True)
    
    if st.button("🚀 Create 100KB PDF", type="primary"):
        with st.spinner("Processing..."):
            pdf_data, final_size = compress_to_100kb(st.session_state.scanned_pages)
            st.success(f"Final Size: {final_size:.2f} KB")
            
            date_str = datetime.datetime.now().strftime('%d_%m')
            st.download_button(label="⬇️ Download PDF", 
                               data=pdf_data, 
                               file_name=f"{clean_name}_{date_str}.pdf", 
                               mime="application/pdf")
    
    if st.button("🗑️ Reset Everything"):
        st.session_state.scanned_pages = []
        st.rerun()
