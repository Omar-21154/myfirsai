import streamlit as st
import google.generativeai as genai
import uuid
import time

# --- 1. SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")

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


# --- 2. SESSION STATE BAŞLATMA ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if not st.session_state.all_chats:
    init_id = str(uuid.uuid4())
    st.session_state.all_chats[init_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.active_id = init_id

if "active_id" not in st.session_state or st.session_state.active_id not in st.session_state.all_chats:
    st.session_state.active_id = list(st.session_state.all_chats.keys())[0]


# --- 3. MODEL QURULUŞU ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception:
    st.error("API Key tapılmadı!")
    model = None


# --- 4. YARDIMÇI FUNKSİYALAR ---
def build_history(messages):
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history

def word_stream(response):
    """Gemini chunk-larını söz-söz yield edir"""
    for chunk in response:
        if chunk.text:
            words = chunk.text.split(" ")
            for i, word in enumerate(words):
                # Sözlər arasına boşluq əlavə et (birinci söz istisna)
                yield ("" if i == 0 else " ") + word
                time.sleep(0.04)  # Söz-söz gecikmə (istəyə görə tənzimlə)


# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id
        st.rerun()

    st.divider()

    for c_id in list(st.session_state.all_chats.keys()):
        chat_data = st.session_state.all_chats[c_id]
        cols = st.columns([0.8, 0.2])
        is_active = c_id == st.session_state.active_id
        label = ("▶ " if is_active else "") + chat_data["title"][:20]

        if cols[0].button(label, key=f"btn_{c_id}", use_container_width=True):
            st.session_state.active_id = c_id
            st.rerun()

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


# --- 6. ƏSAS EKRAN ---
current_chat = st.session_state.all_chats[st.session_state.active_id]

for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nə düşünürsən?"):
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

                # Spinner — cavab gəlməmişdən əvvəl
                with st.spinner("Düşünürəm..."):
                    response = chat_session.send_message(prompt, stream=True)
                    # İlk chunk-u gözləyirik ki spinner görünsün
                    chunks = list(response)

                # Spinner bitdi, smooth typing başlayır
                full_text = st.write_stream(word_stream(iter(chunks)))

                current_chat["messages"].append({"role": "assistant", "content": full_text})

            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")
        else:
            st.error("API sistemi qoşulmayıb.")