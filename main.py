import streamlit as st
import google.generativeai as genai
import uuid
import time
from streamlit_local_storage import LocalStorage

# --- 1. AYARLAR ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")
storage = LocalStorage()

# --- 2. GÜCLÜ CSS (20px Radius və Boşluqların Tənzimlənməsi) ---
st.markdown("""
    <style>
        .stButton > button { border-radius: 20px !important; }
        [data-testid="stSidebar"] .stButton > button { border-radius: 20px !important; }
        [data-testid="stChatInput"] textarea { border-radius: 20px !important; }
        [data-testid="stChatMessage"] { border-radius: 20px !important; border: 1px solid #ddd !important; }
        div[data-testid="stHorizontalBlock"] { gap: 10px !important; align-items: center; }
        @media (prefers-color-scheme: dark) {
            [data-testid="stChatMessage"] { border: 1px solid #444 !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. TARİXCƏ MƏNTİQİ (GÜCLƏNDİRİLMİŞ) ---
if "all_chats" not in st.session_state:
    saved = storage.getItem("omar_chats")
    # Əgər yaddaş boşdursa və ya xətalıdırsa, boş lüğət yarat
    if saved and isinstance(saved, dict):
        st.session_state.all_chats = saved
    else:
        st.session_state.all_chats = {}

# Aktiv söhbəti təyin etmək
if "active_id" not in st.session_state or st.session_state.active_id not in st.session_state.all_chats:
    if st.session_state.all_chats:
        st.session_state.active_id = list(st.session_state.all_chats.keys())[0]
    else:
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id

# --- 4. MODEL ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    model = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id
        storage.setItem("omar_chats", st.session_state.all_chats)
        st.rerun()
    
    st.divider()
    
    # Tarixcə siyahısı
    for c_id in list(st.session_state.all_chats.keys()):
        chat_data = st.session_state.all_chats[c_id]
        cols = st.columns([0.8, 0.2 ], gap="small")
        
        # Söhbət düyməsi
        if cols[0].button(chat_data["title"][:18], key=f"btn_{c_id}", use_container_width=True):
            st.session_state.active_id = c_id
            st.rerun()
            
        # Silmə düyməsi (Smart Logic)
        if cols[1].button("🗑️", key=f"del_{c_id}"):
            del st.session_state.all_chats[c_id]
            
            # Əgər aktiv olanı sildiksə, başqasına keç
            if st.session_state.active_id == c_id:
                if st.session_state.all_chats:
                    st.session_state.active_id = list(st.session_state.all_chats.keys())[-1]
                else:
                    # Tamamilə boşdursa yenisini yarat
                    new_id = str(uuid.uuid4())
                    st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
                    st.session_state.active_id = new_id
            
            storage.setItem("omar_chats", st.session_state.all_chats)
            st.rerun()

# --- 6. ƏSAS EKRAN ---
active_id = st.session_state.active_id
current_chat = st.session_state.all_chats.get(active_id)

if current_chat:
    st.markdown(f"### {current_chat['title']}")

    # Mesajları göstər
    for m in current_chat["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Daxiletmə
    if prompt := st.chat_input("Nə düşünürsən?"):
        # Başlığı ilk suala görə dəyiş
        if not current_chat["messages"]:
            current_chat["title"] = prompt[:20]
        
        # İstifadəçi mesajını əlavə et
        current_chat["messages"].append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        # AI Cavabı
        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("AI Thinking..."):
                try:
                    # Tarixcəni AI-a ötür
                    history = []
                    for msg in current_chat["messages"][:-1]:
                        history.append({
                            "role": "model" if msg["role"] == "assistant" else "user",
                            "parts": [msg["content"]]
                        })
                    
                    chat_session = model.start_chat(history=history)
                    response = chat_session.send_message(prompt)
                    ai_text = response.text
                except Exception as e:
                    ai_text = f"Xəta: {str(e)}"

            # Spinner getdi, typing başladı
            full_res = ""
            for word in ai_text.split(" "):
                full_res += word + " "
                placeholder.markdown(full_res)
                time.sleep(0.05)

        # Cavabı yaddaşa at
        current_chat["messages"].append({"role": "assistant", "content": ai_text})
        storage.setItem("omar_chats", st.session_state.all_chats)
        st.rerun()