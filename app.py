import streamlit as st
import google.genai as genai
import os

# 1. Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Moderní minimalistický styl
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stButton>button { border-radius: 10px; width: 100%; text-align: left; border: none; background-color: transparent; }
    .stButton>button:hover { background-color: #eef1f6; }
    div[data-testid="stChatInput"] { border-radius: 30px; }
    .stApp { background: radial-gradient(circle at 50% 50%, #f0f4f9 0%, #ffffff 100%); }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
# Opravené načítání loga přímo (bez app/static)
col1, col2 = st.sidebar.columns([1, 4])
with col1:
    if os.path.exists("koregis_logo.png"):
        st.image("koregis_logo.png", width=40)
with col2:
    st.markdown("<h2 style='font-weight: 500; margin-top: 2px;'>Koregis AI</h2>", unsafe_allow_html=True)

st.sidebar.write("<br>", unsafe_allow_html=True)

# Inicializace stavu
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if st.sidebar.button("➕ New Chat"):
    new_id = len(st.session_state.chats) + 1
    new_name = f"Chat {new_id}"
    st.session_state.chats[new_name] = {"history": [], "raw": []}
    st.session_state.current_chat = new_name
    st.rerun()

st.sidebar.write("---")
for chat_name in st.session_state.chats.keys():
    if st.sidebar.button(chat_name, key=chat_name):
        st.session_state.current_chat = chat_name
        st.rerun()

# --- AI CONFIG ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- HLAVNÍ ČÁST ---
# Pokud není vybrán chat, zobrazíme uvítání, ale POŘÁD povolíme vstup pro nový chat
if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center; font-weight:400; color: #444;'>How can I help you today?</h1>", unsafe_allow_html=True)
    
    # Automatické vytvoření chatu po prvním dotazu
    if prompt := st.chat_input("Ask Koregis..."):
        new_name = "Chat 1"
        st.session_state.chats[new_name] = {"history": [], "raw": []}
        st.session_state.current_chat = new_name
        active_chat = st.session_state.chats[new_name]
        active_chat["history"].append({"role": "user", "content": prompt})
        active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
        st.rerun()
else:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    # Vykreslení historie a chat_inputu... (zbytek logiky chatu)
    for msg in active_chat["history"]:
        avatar = "koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else ("🤖" if msg["role"] == "assistant" else "👤")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask Koregis..."):
        active_chat["history"].append({"role": "user", "content": prompt})
        active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
        st.rerun()
