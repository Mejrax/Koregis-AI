import streamlit as st
import google.genai as genai
import os

# 1. Konfigurace stránky
st.set_page_config(page_title="Koregis", page_icon="🤖", layout="wide")

# Moderní minimalistický styl s jemným přechodem
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
st.sidebar.markdown("<h2 style='font-weight: 500;'>🤖 Koregis</h2>", unsafe_allow_html=True)
st.sidebar.write("<br>", unsafe_allow_html=True)

# Inicializace stavu
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": {"history": [], "raw": []}}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

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
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- HLAVNÍ CHAT ---
active_chat = st.session_state.chats[st.session_state.current_chat]

# ÚVODNÍ OBRAZOVKA S BANNEREM
if len(active_chat["history"]) == 0:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h2 style='text-align:center; font-weight:400; color: #444;'>Jak ti dnes můžu pomoci, MEJRAX?</h2>", unsafe_allow_html=True)

# Vykreslení historie
for msg in active_chat["history"]:
    # Místo robota použijeme logo, pokud existuje
    avatar = "koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else ("🤖" if msg["role"] == "assistant" else "👤")
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask Koregis..."):
    # 1. Přejmenování při první zprávě
    if len(active_chat["history"]) == 0:
        try:
            title_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Vymysli krátký název (max 3 slova) pro: '{prompt}'. Odpověz POUZE názvem."
            )
            new_name = title_resp.text.strip().replace('"', '').replace("'", "")
            old_data = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.chats[new_name] = old_data
            st.session_state.current_chat = new_name
        except: pass

    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    st.rerun()

# 2. Odpověď asistenta
if len(active_chat["history"]) > 0 and active_chat["history"][-1]["role"] == "user":
    avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else "🤖"
    with st.chat_message("assistant", avatar=avatar):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=active_chat["raw"],
                config={"system_instruction": "Jsi Koregis, stvořený Mejraxem. Buď stručný, inteligentní a věrný."}
            )
            full_text = response.text
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
except Exception as e:
            st.error(f"Error: {e}")
            full_text = "Sorry, I encountered an issue."
        
        st.markdown(full_text)
    st.rerun()
        st.markdown(full_text)
    st.rerun()
