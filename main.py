import streamlit as st
import google.generativeai as genai
import uuid
import time
from streamlit_local_storage import LocalStorage

# --- 1. SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")

# CSS: Border-radiusları və dizaynı geri qaytarırıq
st.markdown("""
    <style>
    .stChatMessage {
        border-radius: 20px !important;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stButton>button {
        border-radius: 12px !important;
    }
    .stTextInput>div>div>input {
        border-radius: 15px !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)

storage = LocalStorage()

# --- 2. YADDAŞ FUNKSİYALARI ---
def save_to_local():
    storage.setItem("omar_chats", st.session_state.all_chats)

def load_from_local():
    try:
        data = storage.getItem("omar_chats")
        if data:
            return dict(data)
        return {}
    except:
        return {}

# --- 3. SESSION STATE BAŞLATMA ---
if "all_chats" not in st.session_state:
    # LocalStorage-in oyanması üçün vaxt veririk
    with st.spinner("Yaddaş yüklənir..."):
        time.sleep(0.8) 
        st.session_state.all_chats = load_from_local()

if not st.session_state.all_chats:
    # Əgər heç bir söhbət yoxdursa, avtomatik birini yarat (Hazır gözləsin)
    init_id = str(uuid.uuid4())
    st.session_state.all_chats[init_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.active_id = init_id
elif "active_id" not in st.session_state or st.session_state.active_id is None:
    st.session_state.active_id = list(st.session_state.all_chats.keys())[0]

# --- 4. MODEL QURULUŞU ---
try:
    # DİQQƏT: Model adı mütləq gemini-2.5-flash olmalıdır!
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("API Key tapılmadı və ya model adı səhvdir!")
    model = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id
        save_to_local()
        st.rerun()
    st.divider()
    for c_id in list(st.session_state.all_chats.keys()):
        chat_data = st.session_state.all_chats[c_id]
        cols = st.columns([0.8, 0.2])
        if cols[0].button(chat_data["title"][:18], key=f"btn_{c_id}", use_container_width=True):
            st.session_state.active_id = c_id
            st.rerun()
        if cols[1].button("🗑️", key=f"del_{c_id}"):
            del st.session_state.all_chats[c_id]
            st.session_state.active_id = None
            save_to_local()
            st.rerun()

# --- 6. ƏSAS EKRAN ---
if st.session_state.active_id and st.session_state.active_id in st.session_state.all_chats:
    current_chat = st.session_state.all_chats[st.session_state.active_id]
    
    # Köhnə mesajları göstər
    for msg in current_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Giriş sahəsi
    if prompt := st.chat_input("Nə düşünürsən?"):
        current_chat["messages"].append({"role": "user", "content": prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:15]
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if model:
                try:
                    with st.spinner("Düşünürəm..."):
                        response = model.generate_content(prompt)
                        res_text = response.text
                        st.markdown(res_text)
                        current_chat["messages"].append({"role": "assistant", "content": res_text})
                        save_to_local()
                except Exception as e:
                    st.error(f"Xəta baş verdi: {e}")
            else:
                st.error("API sistemi qoşulmayıb.")