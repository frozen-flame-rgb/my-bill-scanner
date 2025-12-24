import streamlit as st
from PIL import Image
import io
import datetime
import re
import cv2
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Document Scanner", layout="centered")

st.title("📑 Pro Document Scanner")
st.write("Upload photos. **Document Mode** will try to auto-crop and straighten them.")

# --- SCANNING LOGIC (Document Mode) ---
def scan_document(image):
    """Detects edges and warps perspective to create a flat 'Document' look."""
    # Convert PIL to OpenCV format (BGR)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    orig = img_cv.copy()
    
    # 1. Grayscale and Blur
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 2. Edge Detection
    edged = cv2.Canny(blurred, 75, 200)
    
    # 3. Find Contours
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    
    doc_cnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc_cnt = approx
            break
            
    # If no 4-sided document found, return original
    if doc_cnt is None:
        return image 

    # 4. Perspective Warp (The 'Straightening' magic)
    def order_points(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # Top-left
        rect[2] = pts[np.argmax(s)] # Bottom-right
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # Top-right
        rect[3] = pts[np.argmax(diff)] # Bottom-left
        return rect

    pts = doc_cnt.reshape(4, 2)
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute width and height of new document
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
    
    # Convert back to PIL RGB
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    return Image.fromarray(warped_rgb)

# --- THE COMPRESSION LOGIC (Same as before) ---
def compress_to_multi_page_pdf(image_list, target_kb=98):
    scale, quality = 1.0, 90
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            w, h = img.size
            resized = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            processed.append(resized)
        
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size = buf.tell() / 1024
        if size <= target_kb or scale < 0.1:
            return buf.getvalue(), size
        scale -= 0.1
        if scale < 0.5: quality -= 5

# --- THE INTERFACE ---
st.divider()
user_filename = st.text_input("1. File Name:", "My_Document")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

doc_mode = st.toggle("✨ Enable Document Mode (Auto-Crop)", value=True)

uploaded_files = st.file_uploader("2. Upload Photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    raw_images = [Image.open(f).convert('RGB') for f in uploaded_files]
    
    st.subheader(f"3. Preview ({len(raw_images)} pages)")
    angle = st.radio("Rotate all clockwise:", [0, 90, 180, 270], horizontal=True)
    
    final_processed_list = []
    cols = st.columns(3)
    
    for i, img in enumerate(raw_images):
        # Rotate first
        if angle != 0:
            img = img.rotate(-angle, expand=True)
            
        # Apply Document Mode if enabled
        if doc_mode:
            with st.spinner(f"Scanning page {i+1}..."):
                img = scan_document(img)
        
        final_processed_list.append(img)
        cols[i % 3].image(img, caption=f"Page {i+1}", use_container_width=True)

    st.divider()
    if st.button("🚀 Merge into 100KB PDF", type="primary"):
        pdf_data, final_size = compress_to_multi_page_pdf(final_processed_list)
        st.success(f"Final Size: {final_size:.2f} KB")
        st.download_button(f"⬇️ Download {clean_name}.pdf", pdf_data, f"{clean_name}.pdf", "application/pdf")
