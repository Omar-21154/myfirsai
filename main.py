import streamlit as st
import google.generativeai as genai
import uuid
import json
import os
import time
import re
from PIL import Image

# --- 1. DAİMİ YADDAŞ (Stabil Versiya) ---
DB_FILE = "omar_chat_history.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception:
        return {}

def save_data():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.archives, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.toast(f"Yaddaş xətası: {e}", icon="⚠️")

if "archives" not in st.session_state:
    st.session_state.archives = load_data()

if not st.session_state.archives:
    uid = str(uuid.uuid4())
    st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
    st.session_state.active_id = uid
    save_data()

if "active_id" not in st.session_state or st.session_state.active_id not in st.session_state.archives:
    st.session_state.active_id = list(st.session_state.archives.keys())[0]

# Mesajları session_state-ə bağlayırıq
st.session_state.messages = st.session_state.archives[st.session_state.active_id]["msgs"]

# --- 2. CSS: DİZAYN ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarCollapse"] svg { transform: scaleX(-1) !important; }
    .stButton button { border-radius: 10px !important; height: 38px !important; }
    button[key^="del_"] {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: #ff4b4b !important;
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
    }
    button[key^="del_"]:hover { background-color: #ff4b4b !important; color: white !important; }
    html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100vw; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API SETUP (Ehtiyat Key Sistemi) ---
# Secrets-də həm GEMINI_API_KEY, həm də GEMINI_API_KEY_2 qoya bilərsən
primary_key = st.secrets.get("GEMINI_API_KEY")
secondary_key = st.secrets.get("GEMINI_API_KEY_2", primary_key) # İkinci yoxdursa birincini işlət

if "current_key" not in st.session_state:
    st.session_state.current_key = primary_key

genai.configure(api_key=st.session_state.current_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    st.subheader("🖼️ Şəkil Analizi")
    
    uploaded_file = st.file_uploader("Şəkil yüklə", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Seçilən şəkil", use_container_width=True)
    
    st.divider()
    
    if st.button("➕ Yeni söhbət", use_container_width=True):
        uid = str(uuid.uuid4())
        st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
        st.session_state.active_id = uid
        save_data()
        st.rerun()

    st.subheader("📚 Keçmiş")
    for chat_id, chat_data in list(st.session_state.archives.items()):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(chat_data["title"], key=f"sel_{chat_id}", use_container_width=True):
                st.session_state.active_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}", use_container_width=True):
                del st.session_state.archives[chat_id]
                save_data()
                if st.session_state.active_id == chat_id:
                    st.session_state.active_id = list(st.session_state.archives.keys())[0] if st.session_state.archives else None
                st.rerun()

# --- 5. ÇAT SAHƏSİ ---
if st.session_state.active_id and st.session_state.active_id in st.session_state.archives:
    active_chat = st.session_state.archives[st.session_state.active_id]
    st.subheader(f"📍 {active_chat['title']}")

    for m in active_chat['msgs']:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Mesajınızı yazın..."):
        if not active_chat['msgs'] or active_chat['title'] == "Yeni Söhbət 💬":
            active_chat['title'] = (prompt[:25] + "..") if len(prompt) > 25 else prompt
        
        active_chat['msgs'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("AI düşünür..."):
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        res = model.generate_content([prompt, img])
                    else:
                        history_for_api = []
                        for m in active_chat['msgs'][:-1]:
                            role = "user" if m["role"] == "user" else "model"
                            history_for_api.append({"role": role, "parts": [m["content"]]})
                        
                        chat_session = model.start_chat(history=history_for_api)
                        res = chat_session.send_message(prompt)
                    
                    full_res = res.text
                
                placeholder = st.empty()
                disp = ""
                words = full_res.split(" ")
                for i, word in enumerate(words):
                    disp += word + " "
                    if i % 3 == 0 or i == len(words) - 1:
                        placeholder.markdown(disp + "▌")
                        time.sleep(0.01)
                placeholder.markdown(full_res)
                
                active_chat['msgs'].append({"role": "assistant", "content": full_res})
                save_data()
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    # Əgər ehtiyat key varsa, ona keçid edirik
                    if st.session_state.current_key == primary_key and secondary_key != primary_key:
                        st.info("🔄 Birinci limit doldu, ehtiyat sistemə keçid edilir...")
                        st.session_state.current_key = secondary_key
                        st.rerun()
                    
                    st.error("🚫 **Limit doldu!**")
                    wait_time = 35
                    match = re.search(r"retry in ([\d\.]+)", error_msg)
                    if match:
                        wait_time = int(float(match.group(1))) + 1
                    
                    timer_place = st.empty()
                    for i in range(wait_time, 0, -1):
                        timer_place.warning(f"⏳ Yenidən cəhd üçün gözləyin: {i} saniyə")
                        time.sleep(1)
                    timer_place.success("✅ İndi yenidən yoxlaya bilərsiniz!")
                else:
                    st.error(f"⚠️ Xəta: {error_msg}")
else:
    st.info("Sol tərəfdən söhbət seçin və ya yenisini yaradın.")