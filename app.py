import streamlit as st
import google.genai as genai
import os
import base64
import random

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Transparentní 1x1 px PNG pro skrytí uživatelského avataru
BLANK_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# --- CSS PRO PERFEKTNÍ POZICOVÁNÍ A VELIKOST ---
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

    /* Perfektní zarovnání hlavního loga a textu v sidebaru na střed */
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

    /* --- ABSOLUTNÍ UKOTVENÍ PATIČKY NA DNĚ SIDEBARU --- */
    .sidebar-footer-container {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 210px;
        font-size: 15px;
        color: var(--text-color);
        line-height: 1.5;
        z-index: 100;
        background-color: var(--background-color);
    }
    
    .footer-line {
        border-top: 1px solid var(--secondary-background-color);
        margin-bottom: 15px;
        opacity: 0.6;
    }

    .footer-dev-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
        font-weight: 600;
        font-size: 18px;
    }
    .footer-dev-logo {
        width: 26px;
        height: 26px;
        object-fit: contain;
        border-radius: 50%;
    }
    .footer-version {
        font-size: 14px;
        opacity: 0.8;
        font-weight: 500;
        padding-left: 2px;
    }
    .footer-powered {
        font-size: 12px;
        opacity: 0.5;
        font-style: italic;
        padding-left: 2px;
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

# Načtení a zakódování hlavního loga (Koregis AI)
logo_base64 = ""
if os.path.exists("koregis_logo.png"):
    with open("koregis_logo.png", "rb") as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode()

# Načtení a zakódování loga vývojáře (dev_mejrax.png)
dev_logo_base64 = ""
if os.path.exists("dev_mejrax.png"):
    with open("dev_mejrax.png", "rb") as image_file:
        dev_logo_base64 = base64.b64encode(image_file.read()).decode()

# --- SIDEBAR ---
with st.sidebar:
    # Hlavička sidebaru (Koregis AI)
    header_html = '<div class="sidebar-header-container">'
    if logo_base64:
        header_html += f'<img src="data:image/png;base64,{logo_base64}" class="sidebar-logo">'
    header_html += '<p class="sidebar-title">Koregis AI</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # Tlačítko pro nový chat
    if st.button("Nový chat"):
        new_id = len(st.session_state.chats) + 1
        new_name = f"Chat {new_id}"
        st.session_state.chats[new_name] = {"history": [], "api_history": []}
        st.session_state.current_chat = new_name
        st.rerun()

    st.write("---")
    
    # Seznam chatů
    for chat_name in list(st.session_state.chats.keys()):
        if st.button(chat_name, key=chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

    # --- FIXNÍ PATIČKA ---
    footer_html = '<div class="sidebar-footer-container">'
    footer_html += '<div class="footer-line"></div>'
    footer_html += '<div class="footer-dev-row">'
    if dev_logo_base64:
        footer_html += f'<img src="data:image/png;base64,{dev_logo_base64}" class="footer-dev-logo">'
    elif logo_base64:
        footer_html += f'<img src="data:image/png;base64,{logo_base64}" class="footer-dev-logo">'
    footer_html += 'Developer Mejrax</div>'
    footer_html += '<div class="footer-version">Koregis - 1.0</div>'
    footer_html += '<div class="footer-powered">Powered By Google</div>'
    footer_html += '</div>'
    
    st.markdown(footer_html, unsafe_allow_html=True)


# --- HLAVNÍ FUNKCE PRO ROTACI API KLÍČŮ ---
def get_gemini_client(exclude_keys=[]):
    """Načte seznam klíčů ze secrets a vybere náhodný, který ještě neselhal."""
    raw_keys = st.secrets.get("GEMINI_API_KEYS", st.secrets.get("GEMINI_API_KEY", ""))
    all_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
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
    st.markdown("<h1 style='text-align:center;'>Koregis AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:18px; opacity:0.8;'>Oficiální český AI asistent vytvořený vývojářem Mejrax. Jak vám mohu dnes pomoci?</p>", unsafe_allow_html=True)
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
            
            while not success:
                client, current_key = get_gemini_client(exclude_keys=failed_keys)
                
                if not client:
                    st.error("⚠️ Všechny dostupné API klíče jsou momentálně přehlcené limity nebo mají výpadek u Googlu. Počkej prosím minutu.")
                    st.stop()
                
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
                    success = True 
                    
                except Exception as e:
                    err_msg = str(e)
                    # Rotujeme klíč pokud je limit vyčerpán (429) NEBO pokud má Google dočasný výpadek (503 / UNAVAILABLE)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg or "UNAVAILABLE" in err_msg:
                        failed_keys.append(current_key)
                    else:
                        # Pokud je to vyloženě chyba v syntaxi nebo neplatný klíč, teprve tehdy to zastavíme
                        st.error(f"Chyba API: {e}")
                        st.stop()
            
    st.rerun()
