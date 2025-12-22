import streamlit as st
from PIL import Image
import io
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Simple Photo Scanner", layout="centered")

st.title("📷 Simple Photo to PDF")
st.write("Upload a photo. Rotate if needed. Get a clear, small PDF.")

# --- THE COMPRESSION LOGIC (High Quality, No Filters) ---
def compress_image(image, target_kb=98):
    """Shrinks the image using high-quality resizing until it fits."""
    scale = 1.0
    quality = 95
    
    while True:
        output_buffer = io.BytesIO()
        width, height = image.size
        
        # Calculate new dimensions
        new_w = int(width * scale)
        new_h = int(height * scale)
        
        # Stop if image gets too small to be readable
        if new_w < 300: return None, 0

        # Use LANCZOS for sharp text edges
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Save with optimization
        resized_img.save(output_buffer, format="PDF", quality=quality, optimize=True)
        size_kb = output_buffer.tell() / 1024
        
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # Slowly reduce scale and quality
        scale -= 0.05
        if scale < 0.6 and quality > 50:
            quality -= 5
        
        # Hard stop
        if scale < 0.15: return None, 0

# --- THE INTERFACE ---
st.divider()
st.subheader("1. Upload Photo")
st.caption("On mobile, click 'Browse' then choose 'Camera' for best results.")
uploaded_file = st.file_uploader("Choose your image file", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Open the image and convert to RGB (standard color mode)
    raw_image = Image.open(uploaded_file).convert('RGB')
    
    st.subheader("2. Rotate & Preview")
    
    # Add Rotation Controls
    angle = st.radio("Rotate Image clockwise:", options=[0, 90, 180, 270], horizontal=True)
    
    # Apply rotation if a value other than 0 is selected
    if angle != 0:
        # expand=True ensures the whole image fits after rotation
        raw_image = raw_image.rotate(-angle, expand=True) 
    
    st.image(raw_image, caption="Preview (Corrected Orientation)", use_container_width=True)
    
    st.divider()
    st.subheader("3. Create PDF")
    if st.button("🚀 Convert to 100KB PDF", type="primary"):
        with st.spinner("Processing image..."):
            pdf_data, final_size = compress_image(raw_image)
            
            if pdf_data:
                st.success(f"Success! Final Size: {final_size:.2f} KB")
                
                timestamp = datetime.datetime.now().strftime('%H%M%S')
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"Scan_{timestamp}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Could not compress the image under 100KB without losing too much quality.")
