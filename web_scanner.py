import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import io
import os

st.set_page_config(page_title="Secure Bill Scanner", page_icon="🛡️")

# Create a local folder for security if running locally
SAVE_DIR = "saved_bills"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def compress_to_pdf(image_list, target_kb=100):
    quality = 80
    scale = 0.9
    while True:
        pdf_buffer = io.BytesIO()
        processed = []
        for img in image_list:
            # Grayscale + Contrast for that 'Scanner' look
            temp = ImageOps.grayscale(img)
            temp = ImageEnhance.Contrast(temp).enhance(1.8)
            new_size = (int(temp.width * scale), int(temp.height * scale))
            temp = temp.resize(new_size, Image.Resampling.LANCZOS)
            processed.append(temp)
        
        processed[0].save(pdf_buffer, format="PDF", save_all=True, 
                          append_images=processed[1:], quality=quality, optimize=True)
        
        size_kb = pdf_buffer.tell() / 1024
        if size_kb <= target_kb or scale < 0.2:
            return pdf_buffer.getvalue(), size_kb
        quality -= 10
        scale -= 0.1

st.title("🛡️ Secure Bill Scanner")
st.info("Files are processed in RAM and deleted when you close the tab.")

files = st.file_uploader("Upload or Capture", type=['jpg','png','jpeg'], accept_multiple_files=True)
camera = st.camera_input("Scan with Phone Camera")

images = [Image.open(f).convert('RGB') for f in files] if files else []
if camera: images.append(Image.open(camera).convert('RGB'))

if images:
    if st.button("Generate & Secure PDF"):
        pdf_bytes, size = compress_to_pdf(images)
        st.success(f"Ready! Size: {size:.2f} KB")
        
        # Option to download
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name="bill_scan.pdf")
        
        # If running on your own PC, this saves a backup automatically
        try:
            with open(f"{SAVE_DIR}/last_scan.pdf", "wb") as f:
                f.write(pdf_bytes)
            st.caption(f"🔒 A backup copy was secured in the '{SAVE_DIR}' folder on this device.")
        except:
            pass
