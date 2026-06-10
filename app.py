import streamlit as st
import google.genai as genai
import os

st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# CSS pro čistý vzhled a ikonu tužky
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stApp { background-color: #ffffff; }
    /* Styl pro Nový chat */
    .new-chat-btn { cursor: pointer; color: #000; font-weight: 500; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
    .new-chat-btn:hover { color: #555; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
# Logo a název
col1, col2 = st.sidebar.columns([1, 4])
with col1:
    if os.path.exists("koregis_logo.png"):
        st.image("koregis_logo.png", width=40)
with col2:
    st.markdown("## Koregis AI")

# Tlačítko Nový chat s ikonou tužky
if st.sidebar.button("✍️ Nový chat"):
    new_id = len(st.session_state.get("chats", {})) + 1
    new_name = f"Nový chat {new_id}"
    if "chats" not in st.session_state: st.session_state.chats = {}
    st.session_state.chats[new_name] = {"history": [], "raw": []}
    st.session_state.current_chat = new_name
    st.rerun()

st.sidebar.write("---")

# Seznam chatů
if "chats" in st.session_state:
    for chat_name in list(st.session_state.chats.keys()):
        if st.sidebar.button(chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

# --- AI CONFIG ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- HLAVNÍ ČÁST ---
if "current_chat" not in st.session_state: st.session_state.current_chat = None

if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center; font-weight:400; margin-top: -20px;'>How can I help you today?</h1>", unsafe_allow_html=True)

# Vykreslení chatu
if st.session_state.current_chat:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    for msg in active_chat["history"]:
        avatar = "koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else None
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
            name_resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Název pro: '{prompt}' (max 3 slova).")
            new_title = name_resp.text.strip().replace('"', '')
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            active_chat = st.session_state.chats[new_title]
        except: pass

    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    
    with st.chat_message("assistant", avatar="koregis_logo.png" if os.path.exists("koregis_logo.png") else None):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=active_chat["raw"],
                config={"system_instruction": "You are Koregis AI, created by Mejrax. Intelligent, faithful, multilingual."}
            )
            full_text = response.text
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            st.markdown(full_text)
        except: st.error("Chyba při komunikaci.")
    st.rerun()
