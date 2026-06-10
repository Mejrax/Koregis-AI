import streamlit as st
import google.genai as genai
from PIL import Image
import os

# 1. Konfigurace stránky
st.set_page_config(page_title="Koregis", page_icon="💬", layout="wide")

# CSS pro moderní minimalistický design
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stButton>button { border-radius: 10px; width: 100%; text-align: left; border: none; background-color: transparent; }
    .stButton>button:hover { background-color: #eef1f6; }
    div[data-testid="stChatInput"] { border-radius: 30px; }
    </style>
""", unsafe_allow_html=True)

# Načtení loga
logo_path = "koregis_logo.png"
bot_avatar = Image.open(logo_path) if os.path.exists(logo_path) else "💬"

# --- SIDEBAR ---
col_logo, col_title = st.sidebar.columns([1, 4])
with col_logo:
    if os.path.exists(logo_path): st.image(bot_avatar, width=32)
with col_title:
    st.markdown("<h3 style='margin:0; font-weight: 500;'>Koregis</h3>", unsafe_allow_html=True)

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
    st.error("Missing GEMINI_API_KEY")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- HLAVNÍ CHAT ---
active_chat = st.session_state.chats[st.session_state.current_chat]

if len(active_chat["history"]) == 0:
    st.markdown("<br><br><h1 style='text-align:center; font-weight:400;'>Let's do this</h1>", unsafe_allow_html=True)

for msg in active_chat["history"]:
    avatar = bot_avatar if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask Koregis..."):
    # 1. Pokud je to první zpráva, přejmenuj chat
    if len(active_chat["history"]) == 0:
        # AI vygeneruje krátký název (max 20 znaků)
        title_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Vymysli krátký název (max 3 slova) pro tento dotaz: '{prompt}'"
        )
        new_name = title_resp.text.strip().replace('"', '')
        # Přejmenování klíče v dictu
        old_data = st.session_state.chats.pop(st.session_state.current_chat)
        st.session_state.chats[new_name] = old_data
        st.session_state.current_chat = new_name

    # 2. Ulož zprávu
    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [prompt]})
    st.rerun()

# 3. Odpověď asistenta
if len(active_chat["history"]) > 0 and active_chat["history"][-1]["role"] == "user":
    with st.chat_message("assistant", avatar=bot_avatar):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=active_chat["raw"],
            config=genai.types.GenerateContentConfig(
                system_instruction="Jsi Koregis, stvořený Mejraxem. Buď stručný, inteligentní a věrný.",
                tools=[{"google_search": {}}]
            )
        )
        full_text = response.text
        st.markdown(full_text)
    
    active_chat["history"].append({"role": "assistant", "content": full_text})
    active_chat["raw"].append({"role": "assistant", "parts": [full_text]})
    st.rerun()
