import streamlit as st
from PIL import Image
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Multi-Page Bill Scanner", layout="centered")

st.title("📑 Multi-Page Bill Scanner")
st.write("Upload one or more photos. They will be merged into a single PDF under 100KB.")

# --- THE COMPRESSION LOGIC (Multi-Page Support) ---
def compress_to_multi_page_pdf(image_list, target_kb=98):
    """Combines multiple images into one PDF and shrinks them to fit 100KB."""
    scale = 1.0
    quality = 90
    
    while True:
        output_buffer = io.BytesIO()
        processed_images = []
        
        for img in image_list:
            width, height = img.size
            new_w = int(width * scale)
            new_h = int(height * scale)
            
            # High-quality resize for each page
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            processed_images.append(resized)
        
        # Save all images into one PDF
        processed_images[0].save(
            output_buffer, 
            format="PDF", 
            save_all=True, 
            append_images=processed_images[1:], 
            quality=quality, 
            optimize=True
        )
        
        size_kb = output_buffer.tell() / 1024
        
        if size_kb <= target_kb:
            return output_buffer.getvalue(), size_kb
        
        # Reduce scale and quality to fit more pages under 100KB
        scale -= 0.1
        if scale < 0.5:
            quality -= 5
            
        if scale < 0.1 or quality < 20:
            return output_buffer.getvalue(), size_kb

# --- THE INTERFACE ---
st.divider()

# 1. Custom Naming Section
st.subheader("1. File Name")
user_filename = st.text_input("Enter PDF Name (Letters & Numbers only):", "My_Bill_Scan")
# Clean the filename to remove any weird characters
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

# 2. Multi-Upload Section
st.subheader("2. Upload Bills")
st.caption("On mobile, click 'Browse' then 'Camera'. You can select multiple files from gallery.")
uploaded_files = st.file_uploader("Select one or more images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    # Load all images into a list
    all_images = []
    for f in uploaded_files:
        img = Image.open(f).convert('RGB')
        all_images.append(img)
    
    st.subheader(f"3. Preview & Rotate ({len(all_images)} pages)")
    
    # Rotation Control (Applies to ALL images in this session)
    angle = st.radio("Rotate all images clockwise:", options=[0, 90, 180, 270], horizontal=True)
    
    final_images = []
    cols = st.columns(3) # Show 3 images per row in preview
    for i, img in enumerate(all_images):
        if angle != 0:
            img = img.rotate(-angle, expand=True)
        final_images.append(img)
        cols[i % 3].image(img, caption=f"Page {i+1}", use_container_width=True)

    # 3. Execution
    st.divider()
    if st.button("🚀 Merge into 100KB PDF", type="primary"):
        with st.spinner(f"Merging {len(final_images)} pages into one PDF..."):
            pdf_data, final_size = compress_to_multi_page_pdf(final_images)
            
            if pdf_data:
                st.success(f"Final Size: {final_size:.2f} KB")
                
                # Combine user name with date
                date_str = datetime.datetime.now().strftime('%d_%m_%y')
                full_filename = f"{clean_name}_{date_str}.pdf"
                
                st.download_button(
                    label=f"⬇️ Download {full_filename}",
                    data=pdf_data,
                    file_name=full_filename,
                    mime="application/pdf"
                )
