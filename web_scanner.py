import streamlit as st
from PIL import Image
import io
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Direct High-Res Scanner", layout="centered")

st.title("📷 Direct High-Res Scanner")
st.write("Click below. It should trigger your **Phone's Main Camera** immediately.")

# --- THE COMPRESSION LOGIC (Highest Quality Resampling) ---
def compress_to_100kb(image, target_kb=98):
    """Shrinks the photo size while keeping text sharp with LANCZOS math."""
    scale = 1.0
    quality = 95
    
    while True:
        output_buffer = io.BytesIO()
        width, height = image.size
        
        # Using LANCZOS to keep text edges crisp
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        # Stop if we get to an absurdly small size
        if new_w < 50: break

        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # optimize=True finds hidden ways to save space without losing detail
        resized_img.save(output_buffer, format="PDF", quality=quality, optimize=True)
        size_kb = output_buffer.tell() / 1024
        
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # Slowly shrink to find the perfect 100KB balance
        scale -= 0.05
        if scale < 0.5 and quality > 45:
            quality -= 5
        
        if scale < 0.1: break
    
    return output_buffer.getvalue(), size_kb

# --- THE INTERFACE ---
st.divider()

# IMPORTANT: This line tells your phone to open the REAL camera app
# 'capture' parameter is what triggers the native camera app
source_file = st.camera_input("📸 CLICK HERE TO OPEN YOUR FULL-POWER CAMERA")

# If camera_input still fails on your specific phone, this is the backup:
if not source_file:
    st.write("--- OR ---")
    source_file = st.file_uploader("📂 Upload from Gallery if Camera didn't open", type=['jpg', 'png', 'jpeg'])

if source_file:
    # Open exactly as taken - NO FILTERS
    raw_image = Image.open(source_file).convert('RGB')
    
    st.subheader("Preview")
    st.image(raw_image, caption="Original Quality", use_container_width=True)
    
    if st.button("🚀 Convert to 100KB PDF", type="primary"):
        with st.spinner("Processing..."):
            pdf_data, final_size = compress_to_100kb(raw_image)
            
            if pdf_data:
                st.success(f"Final Size: {final_size:.2f} KB")
                
                # Dynamic filename with time
                timestamp = datetime.datetime.now().strftime('%H%M%S')
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"FullRes_Scan_{timestamp}.pdf",
                    mime="application/pdf"
                )
