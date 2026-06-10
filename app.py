import streamlit as st
import google.genai as genai
import os
import base64

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# --- CSS PRO SPRÁVNÝ DARK MODE, ZAROVNÁNÍ A SKRYTÍ IKONKY UŽIVATELE ---
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
        margin: 0 !important; /* Vynulování defaultního marginu p tagu */
        line-height: 1 !important; /* Aby text neutíkal nahoru/dolu */
    }

    /* Trikové CSS pro úplné skrytí avataru POUZE u uživatele (user) */
    [data-testid="stChatMessage"] {
        flex-direction: row;
    }
    
    /* Když st.chat_message dostane prázdný avatar pro usera, schováme jeho placeholder */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatar"] span:empty) div[data-testid="stChatMessageAvatar"] {
        display: none !important;
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
    # Sestavení HTML pro hlavičku (Logo + Text vedle sebe na střed)
    header_html = '<div class="sidebar-header-container">'
    
    if os.path.exists("koregis_logo.png"):
        with open("koregis_logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        header_html += f'<img src="data:image/png;base64,{encoded_string}" class="sidebar-logo">'
    
    header_html += '<p class="sidebar-title">Koregis AI</p></div>'
    
    # Vykreslení hlavičky
    st.markdown(header_html, unsafe_allow_html=True)

    # Tlačítko pro nový chat
    if st.button("Nový chat"):
        new_id = len(st.session_state.chats) + 1
        new_name = f"Chat {new_id}"
        st.session_state.chats[new_name] = {"history": [], "raw": []}
        st.session_state.current_chat = new_name
        st.rerun()

    st.write("---")
    
    # Seznam chatů
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
    
    # Vykreslení historie zpráv ze session_state
    for msg in active_chat["history"]:
        if msg["role"] == "assistant":
            avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(msg["content"])
        else:
            # Předáním mezery do avataru a s pomocí CSS schováme ikonku uživatele
            with st.chat_message("user", avatar=" "):
                st.markdown(msg["content"])

# Vstupní pole pro psaní
if prompt := st.chat_input("Ask Koregis..."):
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temp"
        st.session_state.chats["Temp"] = {"history": [], "raw": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Okamžité uložení uživatelské zprávy do historie
    active_chat["history"].append({"role": "user", "content": prompt})
    active_chat["raw"].append({"role": "user", "parts": [{"text": prompt}]})
    
    # Vykreslení zprávy uživatele ihned na obrazovku (aby nečekala na odpověď AI)
    with st.chat_message("user", avatar=" "):
        st.markdown(prompt)
        
    # Automatické přejmenování chatu, pokud je to první zpráva
    if len(active_chat["history"]) == 1:
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Name this chat: '{prompt}'. Max 3 words.")
            new_title = resp.text.strip().replace('"', '')
            # Přejmenování klíče v dictionary chatu
            st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
            # Aktualizace reference na active_chat pod novým jménem
            active_chat = st.session_state.chats[new_title]
        except Exception as e: 
            pass

    # Generování odpovědi od Koregis AI
    avatar_ai = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
    with st.chat_message("assistant", avatar=avatar_ai):
        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=active_chat["raw"], 
                config={"system_instruction": SYSTEM_PROMPT}
            )
            full_text = resp.text
            
            # Uložení odpovědi AI do historie chatu
            active_chat["history"].append({"role": "assistant", "content": full_text})
            active_chat["raw"].append({"role": "assistant", "parts": [{"text": full_text}]})
            st.markdown(full_text)
        except Exception as e:
            st.error("Chyba API.")
            
    # Znovunačtení stránky, aby se aktualizovalo i menu a rozvržení chatu
    st.rerun()
