import streamlit as st
from PIL import Image
import io
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="High-Res Bill Scanner", layout="centered")

st.title("📷 High-Resolution Scanner")
st.write("Click below to use your **phone's actual camera** for the best quality.")

# --- THE COMPRESSION LOGIC (Highest Quality Resampling) ---
def compress_high_quality(image, target_kb=98):
    """Shrinks the image size while keeping the text as crisp as possible."""
    scale = 1.0
    quality = 95
    
    while True:
        output_buffer = io.BytesIO()
        width, height = image.size
        
        # We use LANCZOS because it is the most powerful resizing math available
        # It prevents the 'blur' you see in lower-quality apps
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Save as PDF with 'optimize=True' to find the smallest file size 
        # without touching the actual image pixels
        resized_img.save(output_buffer, format="PDF", quality=quality, optimize=True)
        size_kb = output_buffer.tell() / 1024
        
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # Reduce scale slowly to keep high resolution
        scale -= 0.05
        if scale < 0.5 and quality > 50:
            quality -= 5
        
        if scale < 0.1: # Absolute limit
            return output_buffer.getvalue(), size_kb

# --- THE NATIVE INTERFACE ---
st.divider()

# This is the "Magic" button. On mobile, this will let you choose 
# "Take Photo" which opens your REAL phone camera app.
source_file = st.file_uploader("📸 TAP HERE TO TAKE A PHOTO", type=['jpg', 'jpeg', 'png'])

if source_file:
    # 1. Open the original image exactly as your camera took it
    # No filters, no grayscale, no 'weird' enhancements.
    raw_image = Image.open(source_file).convert('RGB')
    
    st.subheader("2. Preview")
    st.image(raw_image, caption="Native Camera Quality", use_container_width=True)
    
    if st.button("🚀 Convert to 100KB PDF", type="primary"):
        with st.spinner("Processing high-res image..."):
            pdf_data, final_size = compress_high_quality(raw_image)
            
            if pdf_data:
                st.success(f"Success! Final Size: {final_size:.2f} KB")
                
                # Dynamic filename
                timestamp = datetime.datetime.now().strftime('%H%M%S')
                st.download_button(
                    label="⬇️ Download High-Res PDF",
                    data=pdf_data,
                    file_name=f"Clean_Scan_{timestamp}.pdf",
                    mime="application/pdf"
                )
