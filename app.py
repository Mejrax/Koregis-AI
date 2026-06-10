import streamlit as st
import google.genai as genai
import os
import logging

# Nastavení logování pro lepší debugování
logging.basicConfig(level=logging.INFO)

# 1. Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# 2. Robustní CSS struktura
def inject_custom_css():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #f8fafd; }
        .stApp { background-color: #ffffff; }
        .logo-container { display: flex; align-items: center; gap: 12px; margin: 15px 0; }
        .new-chat-btn { cursor: pointer; display: flex; align-items: center; gap: 8px; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# 3. Inicializace stavu aplikace
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = None

# 4. Funkce pro práci s modelem
def get_ai_response(history, system_instr):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    return client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
        config={"system_instruction": system_instr}
    )

# --- SIDEBAR ---
with st.sidebar:
    # 1. Použijeme st.columns, abychom dostali logo a název vedle sebe
    # Logo dáme do col1, název do col2
    col_logo, col_text = st.columns([1, 4])
    
    with col_logo:
        # Tady Streamlit sám vyřeší cestu k souboru
        if os.path.exists("koregis_logo.png"):
            st.image("koregis_logo.png", width=30)
            
    with col_text:
        # Použijeme st.markdown s čistým CSS pro černou barvu
        st.markdown('<p style="color:black; font-size:20px; font-weight:600; margin-top:5px;">Koregis AI</p>', unsafe_allow_html=True)

    st.write("---")
    
    # Tlačítko pro nový chat
    if st.button("Nový chat", use_container_width=True):
        new_id = len(st.session_state.get("chats", {})) + 1
        new_name = f"Nový chat {new_id}"
        if "chats" not in st.session_state: st.session_state.chats = {}
        st.session_state.chats[new_name] = {"history": [], "raw": []}
        st.session_state.current_chat = new_name
        st.rerun()
    
    # Seznam chatů
    for chat_name in list(st.session_state.chats.keys()):
        # Použití key=chat_name zajistí, že Streamlit pozná, na které tlačítko klikáš
        if st.button(chat_name, use_container_width=True, key=chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

# --- HLAVNÍ LOGIKA ---
if not st.session_state.current_chat:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center;'>How can I help you today?</h1>", unsafe_allow_html=True)
else:
    # Vykreslení historie
    active_chat = st.session_state.chats[st.session_state.current_chat]
    for msg in active_chat["history"]:
        avatar = "koregis_logo.png" if (msg["role"] == "assistant" and os.path.exists("koregis_logo.png")) else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# Vstupní pole
if prompt := st.chat_input("Ask Koregis..."):
    if not st.session_state.current_chat:
        st.session_state.current_chat = "Nový chat"
        st.session_state.chats["Nový chat"] = {"history": [], "raw": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # 1. Přidání uživatelského vstupu
    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    
    # 2. Přejmenování při prvním dotazu
    if len(active_chat["history"]) == 1:
        try:
            name_resp = get_ai_response(f"Název pro: {prompt}", "Odpověz pouze krátkým názvem.")
            new_title = name_resp.text.strip().replace('"', '')
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            active_chat = st.session_state.chats[new_title]
        except Exception as e:
            logging.error(f"Chyba při přejmenování: {e}")

    # 3. Získání odpovědi
    with st.chat_message("assistant", avatar="koregis_logo.png" if os.path.exists("koregis_logo.png") else None):
        placeholder = st.empty()
        try:
            resp = get_ai_response(active_chat["raw"], "You are Koregis AI. Created by Mejrax.")
            full_text = resp.text
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            placeholder.markdown(full_text)
        except Exception as e:
            logging.error(f"Chyba AI: {e}")
            placeholder.error("Omlouvám se, došlo k chybě při generování odpovědi.")
    
    st.rerun()
