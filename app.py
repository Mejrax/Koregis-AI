import streamlit as st
import google.genai as genai
import os
import base64
import random

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Transparentní 1x1 px PNG pro skrytí uživatelského avataru (odzkoušené, stabilní)
BLANK_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# --- CSS PRO SPRÁVNÝ DARK MODE, ZAROVNÁNÍ A SMAZÁNÍ PRÁZDNÉHO MÍSTA ---
st.markdown("""
    <style>
    /* Pozadí a ohraničení sidebaru */
    [data-testid="stSidebar"] { 
        background-color: var(--background-color); 
        border-right: 1px solid var(--secondary-background-color);
    }
    
    /* Design tlačítek v sidebaru */
    .stButton>button { 
        border: 1px solid var(--secondary-background-color); 
        border-radius: 8px; 
        width: 100%; 
        text-align: left; 
    }

    /* Perfektní zarovnání loga a textu v sidebaru na střed */
    .sidebar-header-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
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

    /* --- SKRYTÍ VOLNÉHO MÍSTA PO UŽIVATELSKÉM AVATARU --- */
    div[data-testid="stChatMessageAvatar"]:has(img[src*="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"]) {
        display: none !important;
    }
    div[data-testid="stChatMessage"]:has(img[src*="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"]) div[data-testid="stChatMessageContent"] {
        margin-left: 0 !important;
        padding-left: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializace stavu chatu
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = None

# --- SYSTEM PROMPT ---
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


# --- HLAVNÍ FUNKCE PRO ROTACI API KLÍČŮ ---
def get_gemini_client(exclude_keys=[]):
    """Načte seznam klíčů ze secrets a vybere náhodný, který ještě neselhal."""
    raw_keys = st.secrets.get("GEMINI_API_KEYS", st.secrets.get("GEMINI_API_KEY", ""))
    
    # Rozsekáme klíče podle čárek a vyčistíme mezery
    all_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    # Vyfiltrujeme ty, které v aktuálním průchodu selhaly na limit 429
    available_keys = [k for k in all_keys if k not in exclude_keys]
    
    if not available_keys:
        return None, None
        
    chosen_key = random.choice(available_keys)
    return genai.Client(api_key=chosen_key), chosen_key


# --- RENDER STRÁNKY / CHATU ---
if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center;'>How can I help you today?</h1>", unsafe_allow_html=True)
else:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Zobrazení historie
    for msg in active_chat["history"]:
        if msg["role"] == "assistant":
            avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar=BLANK_AVATAR):
                st.markdown(msg["content"])

# Vstup od uživatele
if prompt := st.chat_input("Ask Koregis..."):
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temp"
        st.session_state.chats["Temp"] = {"history": [], "api_history": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    # Okamžité vykreslení zprávy uživatele na plochu
    with st.chat_message("user", avatar=BLANK_AVATAR):
        st.markdown(prompt)
        
    # Automatické pojmenování chatu na začátku
    if len(active_chat["history"]) == 0:
        try:
            client, _ = get_gemini_client()
            if client:
                resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Name this chat: '{prompt}'. Max 3 words.")
                new_title = resp.text.strip().replace('"', '')
                st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
                st.session_state.current_chat = new_title
                active_chat = st.session_state.chats[new_title]
        except: 
            pass

    # Uložení zprávy uživatele do paměti aplikace
    active_chat["history"].append({"role": "user", "content": prompt})

    # Výběr textu pro spinner podle přítomnosti české diakritiky
    czech_chars = set("ěščřžýáíéóúůďťň")
    thinking_text = "Koregis přemýšlí..." if any(char in czech_chars for char in prompt.lower()) else "Koregis is thinking..."

    # Generování odpovědi od AI
    avatar_ai = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
    with st.chat_message("assistant", avatar=avatar_ai):
        with st.spinner(thinking_text):
            
            failed_keys = []
            success = False
            
            # Smyčka zkouší klíče, dokud jeden neuspěje nebo dokud nedojdou
            while not success:
                client, current_key = get_gemini_client(exclude_keys=failed_keys)
                
                if not client:
                    st.error("⚠️ Všechny dostupné API klíče jsou momentálně přehlcené limitem Googlu. Počkej prosím minutu.")
                    st.stop()
                
                try:
                    chat_session = client.chats.create(
                        model="gemini-2.5-flash",
                        history=active_chat["api_history"],
                        config={"system_instruction": SYSTEM_PROMPT}
                    )
                    
                    resp = chat_session.send_message(prompt)
                    full_text = resp.text
                    
                    # Uložení stavu zpět do historie
                    active_chat["api_history"] = chat_session.get_history()
                    active_chat["history"].append({"role": "assistant", "content": full_text})
                    st.markdown(full_text)
                    success = True 
                    
                except Exception as e:
                    # Pokud je to chyba zahlcení (429), vyřadíme klíč pro tento průchod a zkusíme jiný
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        failed_keys.append(current_key)
                    else:
                        # Pokud je to jiná chyba (např. neplatný klíč), vypíšeme ji a zastavíme aplikaci
                        st.error(f"Chyba API: {e}")
                        st.stop()
            
    st.rerun()
