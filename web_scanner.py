import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Mobile Pro Scanner", page_icon="📸")

st.title("📸 Direct Mobile Scanner")
st.write("Turn the camera on to scan, or upload existing photos.")

# --- 1. CAMERA CONTROLS ---
# This allows you to "turn off" the camera to save battery or data
use_camera = st.toggle("Enable Mobile Camera", value=True)

all_scans = []

if use_camera:
    camera_photo = st.camera_input("Scan your bill")
    if camera_photo:
        all_scans.append(Image.open(camera_photo).convert('RGB'))
        st.success("Photo captured! Add another or scroll down to generate PDF.")

# --- 2. UPLOAD OPTION ---
uploaded_files = st.file_uploader("Or upload images from gallery", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
if uploaded_files:
    for f in uploaded_files:
        all_scans.append(Image.open(f).convert('RGB'))

# --- 3. THE LOGIC (Scanner Processing & <100KB Compression) ---
def finalize_pdf(image_list, target_kb=100):
    quality = 80
    scale = 0.9
    
    while True:
        pdf_buffer = io.BytesIO()
        processed_images = []
        
        for img in image_list:
            # Apply 'Scanner Filter' (Grayscale + High Contrast)
            # This makes the PDF look professional and keeps size tiny
            temp = ImageOps.grayscale(img)
            temp = ImageEnhance.Contrast(temp).enhance(2.0)
            
            # Resize based on current scale
            new_size = (int(temp.width * scale), int(temp.height * scale))
            temp = temp.resize(new_size, Image.Resampling.LANCZOS)
            processed_images.append(temp)
        
        # Save as a multi-page PDF
        processed_images[0].save(
            pdf_buffer, 
            format="PDF", 
            save_all=True, 
            append_images=processed_images[1:], 
            quality=quality, 
            optimize=True
        )
        
        size_kb = pdf_buffer.tell() / 1024
        
        # Check if we hit the <100KB goal
        if size_kb <= target_kb or scale < 0.2:
            return pdf_buffer.getvalue(), size_kb
        
        # If too big, shrink quality and scale further
        quality -= 10
        scale -= 0.1

# --- 4. PREVIEW & DOWNLOAD ---
if all_scans:
    st.divider()
    st.subheader(f"Captured Pages: {len(all_scans)}")
    
    if st.button("✨ Create PDF (<100KB)"):
        with st.spinner("Processing..."):
            pdf_bytes, final_size = finalize_pdf(all_scans)
            
            st.success(f"PDF Created! Final Size: {final_size:.2f} KB")
            st.download_button(
                label="📥 Download Scanned Bill",
                data=pdf_bytes,
                file_name="mobile_scan.pdf",
                mime="application/pdf"
            )
            
    # Show small thumbnails of what you've scanned
    cols = st.columns(4)
    for i, img in enumerate(all_scans):
        cols[i % 4].image(img, use_container_width=True)

else:
    st.info("No images detected. Please take a photo or upload one.")
