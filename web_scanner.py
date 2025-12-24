import streamlit as st
from PIL import Image
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="High-Res Scanner", layout="centered")

st.title("📷 Quality Multi-Page Scanner")
st.write("No filters. Just your high-quality camera photos merged into a single 100KB PDF.")

# --- THE COMPRESSION LOGIC (Pure Quality) ---
def compress_to_100kb_pdf(image_list, target_kb=98):
    """Shrinks images with zero filters using pro-grade LANCZOS resizing."""
    scale, quality = 1.0, 95
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            width, height = img.size
            # Use LANCZOS to keep text and handwriting edges sharp
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            processed.append(resized)
        
        # Save pages as a multi-page PDF
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size = buf.tell() / 1024
        
        if size <= target_kb:
            return buf.getvalue(), size
        
        # Slowly reduce size to maintain resolution as long as possible
        scale -= 0.05
        if scale < 0.5 and quality > 40:
            quality -= 5
            
        if scale < 0.1: # Absolute floor
            return buf.getvalue(), size

# --- THE INTERFACE ---
st.divider()
user_filename = st.text_input("1. File Name (Letters/Numbers):", "My_Notes")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

st.subheader("2. Upload Photos")
st.caption("On your Vivo, click 'Browse' then 'Camera' to use your full 50MP/64MP power.")
uploaded_files = st.file_uploader("Select images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    # Open images exactly as they were taken
    raw_images = [Image.open(f).convert('RGB') for f in uploaded_files]
    
    st.subheader(f"3. Preview & Rotate ({len(raw_images)} pages)")
    rotation = st.radio("Fix orientation:", [0, 90, 180, 270], horizontal=True)
    
    final_list = []
    cols = st.columns(3)
    for i, img in enumerate(raw_images):
        if rotation != 0:
            img = img.rotate(-rotation, expand=True)
        final_list.append(img)
        cols[i % 3].image(img, caption=f"Page {i+1}", use_container_width=True)

    st.divider()
    if st.button("🚀 Merge to 100KB PDF", type="primary"):
        with st.spinner("Optimizing your Vivo photos..."):
            pdf_data, final_size = compress_to_100kb_pdf(final_list)
            st.success(f"Final Size: {final_size:.2f} KB")
            
            # Save with custom name + date
            date_str = datetime.datetime.now().strftime('%d_%m')
            st.download_button(f"⬇️ Download {clean_name}_{date_str}.pdf", pdf_data, 
                               f"{clean_name}_{date_str}.pdf", "application/pdf")
