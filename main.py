import streamlit as st
import google.generativeai as genai
import uuid
import time
from streamlit_local_storage import LocalStorage

# --- 1. AYARLAR ---
st.set_page_config(page_title="Omar's AI", page_icon="🚀", layout="wide")

# LocalStorage obyektini yaradırıq
storage = LocalStorage()

# --- 2. YADDAŞ FUNKSİYALARI ---
def save_to_local():
    """Bütün söhbətləri brauzer yaddaşına yazır"""
    storage.setItem("omar_chats", st.session_state.all_chats)

def load_from_local():
    """Brauzer yaddaşından söhbətləri oxuyur"""
    try:
        data = storage.getItem("omar_chats")
        if data:
            # Əgər data string kimidirsə, lüğətə çeviririk
            return dict(data)
        return {}
    except:
        return {}

# --- 3. SESSION STATE BAŞLATMA ---
# Proqram ilk açılanda yaddaşdan oxuyur
if "all_chats" not in st.session_state:
    # LocalStorage-in yüklənməsi üçün çox kiçik bir fasilə
    time.sleep(0.5) 
    st.session_state.all_chats = load_from_local()

if "active_id" not in st.session_state:
    st.session_state.active_id = None

# --- 4. MODEL QURULUŞU ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error("API açarı tapılmadı!")
    model = None

# --- 5. SIDEBAR (SOL MENYU) ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.all_chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.active_id = new_id
        save_to_local()
        st.rerun()

    st.divider()

    # Söhbətlərin siyahısı
    for c_id in list(st.session_state.all_chats.keys()):
        chat_data = st.session_state.all_chats[c_id]
        cols = st.columns([0.8, 0.2])
        
        # Söhbətə keçid düyməsi
        if cols[0].button(chat_data["title"][:20], key=f"btn_{c_id}", use_container_width=True):
            st.session_state.active_id = c_id
            st.rerun()
            
        # Silmə düyməsi
        if cols[1].button("🗑️", key=f"del_{c_id}"):
            del st.session_state.all_chats[c_id]
            if st.session_state.active_id == c_id:
                st.session_state.active_id = None
            save_to_local()
            st.rerun()

# --- 6. ƏSAS EKRAN ---
if st.session_state.active_id:
    current_chat = st.session_state.all_chats[st.session_state.active_id]
    
    # Mesajları göstər
    for msg in current_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # İstifadəçi girişi
    if prompt := st.chat_input("Nə düşünürsən?"):
        # Mesajı əlavə et
        current_chat["messages"].append({"role": "user", "content": prompt})
        
        # İlk mesajdırsa, söhbətin başlığını dəyiş
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:15]
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Cavabı
        with st.chat_message("assistant"):
            if model:
                # "Thinking" effekti üçün spinner
                with st.spinner("AI düşünür..."):
                    response = model.generate_content(prompt)
                    full_response = response.text
                
                # Cavabı göstər və yaddaşa yaz
                st.markdown(full_response)
                current_chat["messages"].append({"role": "assistant", "content": full_response})
                save_to_local()
            else:
                st.warning("Model işləmir.")
else:
    st.info("Söhbətə başlamaq üçün soldan 'Yeni Söhbət' düyməsinə sıxın.")