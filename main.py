import streamlit as st
import google.generativeai as genai
import uuid
import time
import os

# --- 1. SƏHİFƏ AYARLARI ---
# GitHub-dakı loqo faylının adı
sidebar_logo = "logo.png"

st.set_page_config(
    page_title="OMNI AI", 
    page_icon=sidebar_logo if os.path.exists(sidebar_logo) else "🤖", 
    layout="wide"
)

# Xüsusi CSS: Mesajların görünüşü və Sidebar dizaynı
st.markdown("""
    <style>
    .stChatMessage { border-radius: 20px !important; padding: 15px; margin-bottom: 10px; }
    .stButton>button { border-radius: 12px !important; }
    .stTextInput>div>div>input { border-radius: 15px !important; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa; }
    
    /* Sidebar loqo və yazı dizaynı */
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 25px;
        margin-top: -20px;
    }
    .sidebar-logo {
        height: 55px; /* Loqonu yekə etdik */
        width: auto;
        border-radius: 8px;
    }
    .sidebar-title {
        font-size: 28px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        color: #31333F;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. SESSION STATE (Söhbət Yaddaşı) ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if not st.session_state.all_chats:
    init_id = str(uuid.uuid4())
    st.session_state.all_chats[init_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.active_id = init_id

if "active_id" not in st.session_state or st.session_state.active_id not in st.session_state.all_chats:
    if st.session_state.all_chats:
        st.session_state.active_id = list(st.session_state.all_chats.keys())[0]


# --- 3. GOOGLE GEMINI MODEL QURULUŞU ---
try:
    # API Key Streamlit Secrets-dən götürülür
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception:
    st.error("API Key tapılmadı! Lütfən Streamlit Cloud-da Secrets hissəsini yoxlayın.")
    model = None


# --- 4. YARDIMÇI FUNKSİYALAR ---
def build_history(messages):
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history

def word_stream(response):
    """Cavabı ekranda söz-söz yazmaq üçün"""
    for chunk in response:
        if chunk.text:
            words = chunk.text.split(" ")
            for i, word in enumerate(words):
                yield ("" if i == 0 else " ") + word
                time.sleep(0.03)


# --- 5. SIDEBAR (Loqo və "OMNI AI") ---
with st.sidebar:
    # GitHub-dan birbaşa Raw linki istifadə edirik ki, itməsin
    logo_url = "https://raw.githubusercontent.com/Omar-21154/myfirsai/main/logo.png"
    
    st.markdown(f"""
        <div class="sidebar-header">
            <img src="{logo_url}" class="sidebar-logo">
            <h1 class="sidebar-title">OMNI AI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Yeni Söhbət düyməsi
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id
        st.rerun()

    st.divider()

    # Söhbətlərin siyahısı
    for c_id in list(st.session_state.all_chats.keys()):
        chat_data = st.session_state.all_chats[c_id]
        cols = st.columns([0.8, 0.2])
        is_active = (c_id == st.session_state.active_id)
        
        # Aktiv söhbəti işarələyirik
        label = ("▶ " if is_active else "") + chat_data["title"][:22]

        if cols[0].button(label, key=f"btn_{c_id}", use_container_width=True):
            st.session_state.active_id = c_id
            st.rerun()

        # Söhbəti silmə düyməsi
        if cols[1].button("🗑️", key=f"del_{c_id}"):
            del st.session_state.all_chats[c_id]
            remaining = list(st.session_state.all_chats.keys())
            if remaining:
                st.session_state.active_id = remaining[0]
            else:
                new_id = str(uuid.uuid4())
                st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
                st.session_state.active_id = new_id
            st.rerun()


# --- 6. ƏSAS ÇAT EKRANI ---
if st.session_state.active_id in st.session_state.all_chats:
    current_chat = st.session_state.all_chats[st.session_state.active_id]

    # Köhnə mesajları göstəririk
    for msg in current_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # İstifadəçi girişi
    if prompt := st.chat_input("Nə düşünürsən?"):
        # Söhbətə ilk mesajdan başlıq veririk
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:25]

        current_chat["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if model:
                try:
                    history = build_history(current_chat["messages"])
                    chat_session = model.start_chat(history=history)

                    with st.spinner("Düşünürəm..."):
                        response = chat_session.send_message(prompt, stream=True)
                        # Akıcı yazılma effekti
                        full_text = st.write_stream(word_stream(response))

                    current_chat["messages"].append({"role": "assistant", "content": full_text})
                except Exception as e:
                    st.error(f"Xəta baş verdi: {e}")
            else:
                st.error("AI Model hazır deyil.")