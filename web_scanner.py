import streamlit as st
from PIL import Image
import io
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pure Photo Scanner", layout="centered")

st.title("📷 Pure Photo to PDF")
st.write("This version uses NO filters. It keeps your photo exactly as your camera took it.")

# --- THE COMPRESSION LOGIC ---
def pure_compression(image, target_kb=95):
    """Resizes the raw photo to fit under 100KB with zero filters."""
    # We start at 100% size and 90% quality
    scale = 1.0
    quality = 90
    
    while True:
        output_buffer = io.BytesIO()
        
        # Calculate new dimensions
        width, height = image.size
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        # 1. High-quality resize (LANCZOS) to keep text sharp
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 2. Save as PDF with native color profile
        resized_img.save(output_buffer, format="PDF", quality=quality, optimize=True)
        size_kb = output_buffer.tell() / 1024
        
        # 3. Check if target is met
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # 4. If still over 100KB, shrink the size slightly and try again
        scale -= 0.1
        if scale < 0.4:  # If too small, start reducing internal quality
            quality -= 5
            
        if quality < 30 or scale < 0.1:
            return output_buffer.getvalue(), size_kb

# --- THE INTERFACE ---
st.subheader("1. Capture or Upload")
col1, col2 = st.columns(2)

with col1:
    camera_file = st.camera_input("Take a photo")
with col2:
    upload_file = st.file_uploader("Or upload from PC", type=['jpg', 'jpeg', 'png'])

source = camera_file if camera_file else upload_file

if source:
    # Open the image exactly as it is (RGB mode)
    raw_image = Image.open(source).convert('RGB')
    
    st.subheader("2. Preview (Natural)")
    st.image(raw_image, caption="Original Photo Quality", use_container_width=True)
    
    if st.button("🚀 Convert to PDF (<100KB)"):
        with st.spinner("Shrinking file size while keeping clarity..."):
            pdf_bytes, final_size = pure_compression(raw_image)
            
            st.success(f"Final PDF Size: {final_size:.2f} KB")
            
            # Use date for filename
            file_name = f"Scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            st.download_button(
                label="📥 Download Natural PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf"
            )
