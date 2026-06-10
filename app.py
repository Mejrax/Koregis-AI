import streamlit as st
import google.genai as genai
import os

# 1. Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Moderní minimalistický styl včetně zarovnání v sidebar
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stButton>button { border-radius: 10px; width: 100%; text-align: left; border: none; background-color: transparent; }
    .stButton>button:hover { background-color: #eef1f6; }
    div[data-testid="stChatInput"] { border-radius: 30px; }
    .stApp { background: radial-gradient(circle at 50% 50%, #f0f4f9 0%, #ffffff 100%); }
    
    /* CSS pro dokonalé vertikální zarovnání v sidebar */
    .sidebar-header { display: flex; align-items: center; gap: 10px; }
    .sidebar-header h2 { margin: 0 !important; line-height: 1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
# Použití divu s třídou sidebar-header pro perfektní zarovnání
st.sidebar.markdown("""
    <div class="sidebar-header">
        <img src="app/static/koregis_logo.png" width="40">
        <h2>Koregis AI</h2>
    </div>
""", unsafe_allow_html=True)

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

# --- HLAVNÍ CHAT ---
if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center; font-weight:400; color: #444;'>How can I help you today?</h1>", unsafe_allow_html=True)
else:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    for msg in active_chat["history"]:
        avatar = "koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else ("🤖" if msg["role"] == "assistant" else "👤")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Koregis..."):
        if len(active_chat["history"]) == 0:
            try:
                title_resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Vymysli krátký název pro: '{prompt}'. Odpověz POUZE názvem."
                )
                new_name = title_resp.text.strip().replace('"', '').replace("'", "")
                old_data = st.session_state.chats.pop(st.session_state.current_chat)
                st.session_state.chats[new_name] = old_data
                st.session_state.current_chat = new_name
            except: pass

        active_chat["history"].append({"role": "user", "content": prompt})
        active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
        st.rerun()

    if len(active_chat["history"]) > 0 and active_chat["history"][-1]["role"] == "user":
        avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else "🤖"
        with st.chat_message("assistant", avatar=avatar):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=active_chat["raw"],
                    config={"system_instruction": "You are Koregis AI, created by Mejrax. You are intelligent, faithful, and you communicate fluently in all languages."}
                )
                full_text = response.text
                active_chat["history"].append({"role": "assistant", "content": full_text})
                active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            except Exception as e:
                st.error(f"Error: {e}")
                full_text = "Sorry, I encountered an issue."
            st.markdown(full_text)
        st.rerun()
