import streamlit as st
import google.generativeai as genai

# --- 1. SESSION STATE (Xətasız Başlanğıc) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. API SETUP ---
# Secrets-dən açarı götürürük
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("API Key tapılmadı! Secrets hissəsini yoxlayın.")
    st.stop()

# --- 3. UI ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀")
st.title("🚀 Omar's AI")

# Əvvəlki mesajları göstər
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Yeni mesaj daxil etmə
if prompt := st.chat_input("Mesajınızı yazın..."):
    # İstifadəçi mesajını əlavə et
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Cavabı
    with st.chat_message("assistant"):
        try:
            res = model.generate_content(prompt)
            full_res = res.text
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"Xəta: {e}")