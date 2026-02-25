import streamlit as st
import google.generativeai as genai
import uuid
import json
import os
import time
from PIL import Image

# --- 1. DAİMİ YADDAŞ (JSON) SİSTEMİ ---
DB_FILE = "omar_chat_history.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.archives, f, ensure_ascii=False, indent=4)

if "archives" not in st.session_state:
    st.session_state.archives = load_data()

if not st.session_state.archives:
    uid = str(uuid.uuid4())
    st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
    st.session_state.active_id = uid
    save_data()

if "active_id" not in st.session_state:
    st.session_state.active_id = list(st.session_state.archives.keys())[0]

# --- 2. CSS: SIDEBAR VƏ DÜYMƏ DİZAYNI ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarCollapse"] svg { transform: scaleX(-1) !important; }
    
    .stButton button {
        border-radius: 10px !important;
        height: 38px !important;
    }
    
    /* Zibil düyməsinin sidebar daxilində görünüşü */
    button[key^="del_"] {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: #ff4b4b !important;
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
    }
    button[key^="del_"]:hover {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API SETUP (Gemini 2.5 Flash) ---
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    
    st.subheader("🖼️ Şəkil Analizi")
    uploaded_file = st.file_uploader("Şəkil yüklə", type=["jpg", "png", "jpeg"])
    
    st.divider()
    
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        uid = str(uuid.uuid4())
        st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
        st.session_state.active_id = uid
        save_data()
        st.rerun()
    
    st.subheader("📚 Keçmiş")
    for c_id, data in list(st.session_state.archives.items()):
        col_btn, col_del = st.columns([0.8, 0.2])
        with col_btn:
            if st.button(f"💬 {data['title'][:14]}", key=f"sel_{c_id}", use_container_width=True):
                st.session_state.active_id = c_id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{c_id}"):
                del st.session_state.archives[c_id]
                if not st.session_state.archives:
                    uid = str(uuid.uuid4())
                    st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
                    st.session_state.active_id = uid
                elif st.session_state.active_id == c_id:
                    st.session_state.active_id = list(st.session_state.archives.keys())[0]
                save_data()
                st.rerun()

# --- 5. ÇAT SAHƏSİ ---
active_chat = st.session_state.archives[st.session_state.active_id]
st.subheader(f"📍 {active_chat['title']}")

for m in active_chat['msgs']:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Mesajınızı yazın...")

if prompt:
    if not active_chat['msgs']:
        active_chat['title'] = prompt[:15]
    
    active_chat['msgs'].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("AI thinking..."):
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
            
            # Sürətli typing (Söz-söz) - Axıcı və professional
            placeholder = st.empty()
            disp = ""
            words = full_res.split(" ")
            for i, word in enumerate(words):
                disp += word + " "
                if i % 2 == 0 or i == len(words) - 1:
                    placeholder.markdown(disp)
                    time.sleep(0.015)
            
            active_chat['msgs'].append({"role": "assistant", "content": full_res})
            save_data()
            
        except Exception as e:
            st.error(f"Xəta: {e}")
