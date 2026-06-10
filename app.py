import streamlit as st
import google.genai as genai
import os
import base64

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Transparentní 1x1 px PNG obrázek v Base64 pro skrytí uživatelského avataru
BLANK_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# --- CSS PRO SPRÁVNÝ DARK MODE, ZAROVNÁNÍ A SMAZÁNÍ PRÁZDNÉHO MÍSTA ---
st.markdown("""
    <style>
    /* Ponecháme pozadí podle nastavení Streamlitu (Dark/Light podle systému) */
    [data-testid="stSidebar"] { 
        background-color: var(--background-color); 
        border-right: 1px solid var(--secondary-background-color);
    }
    
    /* Zarovnání tlačítek v sidebaru */
    .stButton>button { 
        border: 1px solid var(--secondary-background-color); 
        border-radius: 8px; 
        width: 100%; 
        text-align: left; 
    }

    /* CSS pro perfektní zarovnání loga a textu v sidebaru */
    .sidebar-header-container {
        display: flex;
        align-items: center;  /* Vertikální zarovnání na střed */
        gap: 12px;            /* Mezera mezi logem a textem */
        margin-bottom: 20px;  /* Mezera pod hlavičkou */
        padding-left: 5px;
    }
    .sidebar-logo {
        width: 32px;
        height: 32px;
        object-fit: contain;
    }
    .sidebar-title {
        font-size: 22px;
        font-weight: 600;
        margin: 0 !important; 
        line-height: 1 !important; 
    }

    /* --- ODSTRANĚNÍ PRÁZDNÉHO MÍSTA PO AVATARU --- */
    /* Najde obrázek s průhledným 1x1 px src a smrští celý jeho kruhový kontejner na nulu */
    div[data-testid="stChatMessageAvatar"]:has(img[src*="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"]) {
        display: none !important;
    }
    /* Odstranění marginu u textu uživatele, aby začínal hned od kraje */
    div[data-testid="stChatMessage"]:has(img[src*="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"]) div[data-testid="stChatMessageContent"] {
        margin-left: 0 !important;
        padding-left: 5px !important;
    }
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
    header_html = '<div class="sidebar-header-container">'
    if os.path.exists("koregis_logo.png"):
        with open("koregis_logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        header_html += f'<img src="data:image/png;base64,{encoded_string}" class="sidebar-logo">'
    header_html += '<p class="sidebar-title">Koregis AI</p></div>'
    
    st.markdown(header_html, unsafe_allow_html=True)

    if st.button("Nový chat"):
        new_id = len(st.session_state.chats) + 1
        new_name = f"Chat {new_id}"
        st.session_state.chats[new_name] = {"history": [], "api_history": []}
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
    
    # Vykreslení historie zpráv
    for msg in active_chat["history"]:
        if msg["role"] == "assistant":
            avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(msg["content"])
        else:
            # Vložíme průhledný 1x1 obrázek
            with st.chat_message("user", avatar=BLANK_AVATAR):
                st.markdown(msg["content"])

# Vstupní pole pro psaní
if prompt := st.chat_input("Ask Koregis..."):
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temp"
        st.session_state.chats["Temp"] = {"history": [], "api_history": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Vykreslení zprávy uživatele ihned na obrazovku
    with st.chat_message("user", avatar=BLANK_AVATAR):
        st.markdown(prompt)
        
    # Automatické přejmenování chatu, pokud je to první zpráva
    if len(active_chat["history"]) == 0:
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Name this chat: '{prompt}'. Max 3 words.")
            new_title = resp.text.strip().replace('"', '')
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            active_chat = st.session_state.chats[new_title]
        except: 
            pass

    # Přidání zprávy uživatele do historie
    active_chat["history"].append({"role": "user", "content": prompt})

    # Určení jazyka pro hlášku o přemýšlení
    czech_chars = set("ěščřžýáíéóúůďťň")
    if any(char in czech_chars for char in prompt.lower()):
        thinking_text = "Koregis přemýšlí..."
    else:
        thinking_text = "Koregis is thinking..."

    # Generování odpovědi od Koregis AI s animací přemýšlení
    avatar_ai = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
    with st.chat_message("assistant", avatar=avatar_ai):
        with st.spinner(thinking_text):
            try:
                chat_session = client.chats.create(
                    model="gemini-2.5-flash",
                    history=active_chat["api_history"],
                    config={"system_instruction": SYSTEM_PROMPT}
                )
                
                resp = chat_session.send_message(prompt)
                full_text = resp.text
                
                active_chat["api_history"] = chat_session.get_history()
                active_chat["history"].append({"role": "assistant", "content": full_text})
                st.markdown(full_text)
                
            except Exception as e:
                st.error(f"Chyba API: {e}")
                st.stop()
            
    st.rerun()
