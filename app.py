import streamlit as st
import google.genai as genai
import os

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# CSS pro vzhled
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stApp { background-color: #ffffff; }
    .stButton>button { border: 1px solid #e0e0e0; border-radius: 8px; width: 100%; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# Inicializace stavu
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = None

# --- SYSTÉMOVÁ INSTRUKCE (Základní nastavení AI) ---
SYSTEM_PROMPT = (
    "You are Koregis AI, a highly intelligent and omniscient assistant created by Mejrax. "
    "You are capable of communicating fluently in any language. "
    "You possess vast knowledge about the world and can answer any question. "
    "IMPORTANT: You are strictly forbidden from generating, creating, or outputting any images. "
    "If asked to generate an image, explain that you are a text-based AI model and cannot perform that task."
)

# --- SIDEBAR ---
with st.sidebar:
    col1, col2 = st.columns([1, 4])
    with col1:
        if os.path.exists("koregis_logo.png"):
            st.image("koregis_logo.png", width=30)
    with col2:
        st.markdown('<p style="color:black; font-size:20px; font-weight:600; margin-top:5px;">Koregis AI</p>', unsafe_allow_html=True)

    if st.button("Nový chat"):
        new_id = len(st.session_state.chats) + 1
        new_name = f"Chat {new_id}"
        st.session_state.chats[new_name] = {"history": [], "raw": []}
        st.session_state.current_chat = new_name
        st.rerun()

    st.write("---")
    for chat_name in list(st.session_state.chats.keys()):
        if st.button(chat_name, key=chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

# --- HLAVNÍ LOGIKA ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center;'>How can I help you today?</h1>", unsafe_allow_html=True)
else:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    for msg in active_chat["history"]:
        avatar = "koregis_logo.png" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# Vstupní pole
if prompt := st.chat_input("Ask Koregis..."):
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temp"
        st.session_state.chats["Temp"] = {"history": [], "raw": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Automatické pojmenování
    if len(active_chat["history"]) == 0:
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Name this chat: '{prompt}'. Max 3 words.")
            new_title = resp.text.strip().replace('"', '')
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            active_chat = st.session_state.chats[new_title]
        except: pass

    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    
    with st.chat_message("assistant", avatar="koregis_logo.png" if os.path.exists("koregis_logo.png") else None):
        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=active_chat["raw"], 
                config={"system_instruction": SYSTEM_PROMPT}
            )
            full_text = resp.text
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            st.markdown(full_text)
        except Exception as e:
            st.error("Chyba API.")
    st.rerun()
