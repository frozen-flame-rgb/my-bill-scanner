import streamlit as st
from PIL import Image
from rembg import remove
import io
import datetime
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Smart Scanner", layout="centered")

st.title("🤖 AI Smart Scanner")
st.write("The AI will automatically find your notes and remove the background.")

# --- THE AI COMPRESSION LOGIC ---
def ai_smart_process(image_list, target_kb=98):
    scale, quality = 1.0, 95
    while True:
        buf = io.BytesIO()
        processed = []
        for img in image_list:
            # High-quality resize
            width, height = img.size
            new_size = (int(width * scale), int(height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            processed.append(resized)
        
        # Merge into PDF
        processed[0].save(buf, format="PDF", save_all=True, append_images=processed[1:], 
                          quality=quality, optimize=True)
        size_kb = buf.tell() / 1024
        
        if size_kb <= target_kb:
            return buf.getvalue(), size_kb
        
        scale -= 0.05
        if scale < 0.5 and quality > 40:
            quality -= 5
        if scale < 0.05: return buf.getvalue(), size_kb

# --- SESSION STATE ---
if 'ai_pages' not in st.session_state:
    st.session_state.ai_pages = []

# --- THE INTERFACE ---
st.divider()
user_filename = st.text_input("1. File Name:", "AI_Scan")
clean_name = re.sub(r'[^a-zA-Z0-9]', '_', user_filename)

st.subheader("2. Upload Photos (AI will Auto-Crop)")
uploaded_files = st.file_uploader("Select photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    if st.button("🧠 Run AI Auto-Crop"):
        st.session_state.ai_pages = [] # Reset for new batch
        
        for f in uploaded_files:
            with st.spinner(f"AI is analyzing {f.name}..."):
                # 1. Load Image
                input_img = Image.open(f).convert('RGB')
                
                # 2. AI Background Removal
                # This 'sees' the paper and deletes the table background
                no_bg = remove(input_img)
                
                # 3. Auto-Crop to Content
                # We find the edges of the paper left behind by the AI
                bbox = no_bg.getbbox()
                if bbox:
                    # Crop to the exact area the AI found
                    cropped = no_bg.crop(bbox).convert('RGB')
                    st.session_state.ai_pages.append(cropped)
                else:
                    # Backup: if AI fails, use the original
                    st.session_state.ai_pages.append(input_img)

    # Preview what the AI did
    if st.session_state.ai_pages:
        st.subheader(f"Preview ({len(st.session_state.ai_pages)} pages)")
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.ai_pages):
            cols[i % 3].image(p, caption=f"AI Result {i+1}", use_container_width=True)
        
        st.divider()
        if st.button("🚀 Create 100KB PDF", type="primary"):
            with st.spinner("Finalizing PDF..."):
                pdf_data, final_size = ai_smart_process(st.session_state.ai_pages)
                st.success(f"Final Size: {final_size:.2f} KB")
                
                date_str = datetime.datetime.now().strftime('%d_%m')
                st.download_button(f"⬇️ Download {clean_name}_{date_str}.pdf", 
                                   pdf_data, f"{clean_name}_{date_str}.pdf", "application/pdf")

    if st.button("🗑️ Clear AI Memory"):
        st.session_state.ai_pages = []
        st.rerun()
