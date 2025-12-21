import streamlit as st
from PIL import Image
import io
import datetime

st.set_page_config(page_title="Natural Bill Scanner", layout="centered")

st.title("📷 Natural Photo Scanner")
st.write("No filters. No weird colors. Just your photo, kept clear and under 100KB.")

# --- THE LOGIC ---
def natural_compression(image, target_kb=95):
    """Only resizes the image to meet the 100KB limit without adding filters."""
    # We start with high quality settings
    quality = 90
    scale = 1.0
    
    while True:
        output_buffer = io.BytesIO()
        
        # Calculate new dimensions (keeping aspect ratio)
        width, height = image.size
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        # Safety: If image gets too tiny, the text will be unreadable no matter what
        if new_w < 500:
            return None, "Error: Image is too small to stay under 100KB with clarity."

        # Use LANCZOS - it's the highest quality resizing method for text sharpness
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Save as PDF using JPEG-style compression (best for photos)
        resized_img.save(output_buffer, format="PDF", quality=quality, optimize=True)
        size_kb = output_buffer.tell() / 1024
        
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # If still too big, we slowly reduce scale first, then quality
        scale -= 0.1
        if scale < 0.5:
            quality -= 5
        
        # Hard stop to prevent infinite loops
        if quality < 30:
            return output_buffer.getvalue(), size_kb

# --- THE INTERFACE ---
uploaded_file = st.file_uploader("Upload Bill Image", type=['jpg', 'png', 'jpeg'])
camera_file = st.camera_input("Take a photo of your bill")

target_source = camera_file if camera_file else uploaded_file

if target_source:
    # 1. Open the original, raw photo exactly as the camera took it
    original_image = Image.open(target_source).convert('RGB')
    st.image(original_image, caption="Current View", use_container_width=True)
    
    # 2. Action Button
    if st.button("🚀 Convert to 100KB PDF"):
        with st.spinner("Optimizing file size..."):
            pdf_bytes, final_size = natural_compression(original_image)
            
            if pdf_bytes:
                st.success(f"Optimized! Final Size: {final_size:.2f} KB")
                
                # Download with current date
                file_name = f"Bill_{datetime.datetime.now().strftime('%d_%m_%Y')}.pdf"
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf"
                )
            else:
                st.error(final_size)
