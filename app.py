import streamlit as st
import google.genai as genai
import os

st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Čistý design bez emoji
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stApp { background-color: #ffffff; }
    div[data-testid="stChatInput"] { border-radius: 8px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
col1, col2 = st.sidebar.columns([1, 4])
with col1:
    if os.path.exists("koregis_logo.png"):
        st.image("koregis_logo.png", width=40)
with col2:
    st.markdown("## Koregis AI")

if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if st.sidebar.button("New Chat"):
    new_id = len(st.session_state.chats) + 1
    new_name = f"New Chat {new_id}"
    st.session_state.chats[new_name] = {"history": [], "raw": []}
    st.session_state.current_chat = new_name
    st.rerun()

st.sidebar.write("---")
for chat_name in list(st.session_state.chats.keys()):
    if st.sidebar.button(chat_name):
        st.session_state.current_chat = chat_name
        st.rerun()

# --- AI CONFIG ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- HLAVNÍ ČÁST ---
if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center;'>How can I help you today?</h1>", unsafe_allow_html=True)

# Vykreslení historie (aby zprávy zůstaly vidět)
if st.session_state.current_chat:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    for msg in active_chat["history"]:
        with st.chat_message(msg["role"], avatar="koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else None):
            st.markdown(msg["content"])

# Vstupní pole
if prompt := st.chat_input("Ask Koregis..."):
    # Pokud není vybrán chat, vytvoříme nový
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temporary"
        st.session_state.chats["Temporary"] = {"history": [], "raw": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Změna názvu chatu podle prvního promptu
    if len(active_chat["history"]) == 0:
        try:
            name_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Vymysli krátký název (max 3 slova) pro konverzaci, která začíná takto: '{prompt}'. Odpověz POUZE názvem."
            )
            new_title = name_resp.text.strip().replace('"', '')
            # Přesuneme data pod nový název
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            active_chat = st.session_state.chats[new_title]
        except: pass

    # Uložení a odeslání zprávy
    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="koregis_logo.png" if os.path.exists("koregis_logo.png") else None):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=active_chat["raw"],
                config={"system_instruction": "You are Koregis AI, created by Mejrax. You are intelligent, faithful, and you communicate fluently in all languages."}
            )
            full_text = response.text
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            st.markdown(full_text)
        except Exception as e:
            st.error(f"Error: {e}")
    st.rerun()
