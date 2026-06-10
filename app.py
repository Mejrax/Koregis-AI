import streamlit as st
import google.genai as genai
from google.genai import types  # Import pro konfiguraci vypnutí AFC
import os
import base64
import random
import time

# Konfigurace stránky
st.set_page_config(page_title="Koregis AI", page_icon="koregis_logo.png", layout="wide")

# Transparentní 1x1 px PNG pro skrytí uživatelského avataru
BLANK_AVATAR = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# --- AUTOMATICKÁ DETEKCE JAZYKA PŘES HLAVIČKY PROHLÍŽEČE ---
try:
    accept_language = st.context.headers.get("Accept-Language", "en")
    user_lang = accept_language.split(",")[0].split("-")[0].lower().strip()
except:
    user_lang = "en"

# --- SLOVNÍK PRO DYNAMICKÉ PŘEKLADY WEBU ---
LANG_DICT = {
    "cs": {
        "welcome_title": "Koregis AI",
        "welcome_desc": "Oficiální český AI asistent vytvořený vývojářem Mejrax.",
        "help_text": "Jak vám mohu dnes pomoci?",
        "placeholder": "Zeptej se Koregise...",
        "thinking": "Koregis přemýšlí...",
        "new_chat": "Nový chat",
        "chat_prefix": "Chat",
        "error_api": "⚠️ Bohužel nemohu odpovědět. Všechny dostupné API klíče jsou momentálně přetížené nebo vyčerpané. Zkuste to prosím znovu za chvíli."
    },
    "sk": {
        "welcome_title": "Koregis AI",
        "welcome_desc": "Oficiálny slovenský AI asistent vytvorený vývojárom Mejrax.",
        "help_text": "Ako vám môžem dnes pomôcť?",
        "placeholder": "Spýtaj se Koregisa...",
        "thinking": "Koregis premýšľa...",
        "new_chat": "Nový chat",
        "chat_prefix": "Chat",
        "error_api": "⚠️ Bohužiaľ nemôžem odpovedať. Všetky dostupné API kľúče sú momentálne preťažené alebo vyčerpané. Skúste to prosím znovu o chvíľu."
    },
    "en": {
        "welcome_title": "Koregis AI",
        "welcome_desc": "Official AI assistant created by developer Mejrax.",
        "help_text": "How can I help you today?",
        "placeholder": "Ask Koregis...",
        "thinking": "Koregis is thinking...",
        "new_chat": "New chat",
        "chat_prefix": "New Chat",
        "error_api": "⚠️ Unfortunately, I cannot respond. All available API keys are currently overloaded or exhausted. Please try again in a moment."
    },
    "de": {
        "welcome_title": "Koregis AI",
        "welcome_desc": "Offizieller AI-Assistent, entwickelt von Mejrax.",
        "help_text": "Wie kann ich dir heute helfen?",
        "placeholder": "Frag Koregis...",
        "thinking": "Koregis denkt nach...",
        "new_chat": "Neuer Chat",
        "chat_prefix": "Chat",
        "error_api": "⚠️ Leider kann ich nicht antworten. Alle verfügbaren API-Schlüssel sind derzeit überlastet oder erschöpft. Bitte versuchen Sie es gleich ještě einmal."
    }
}

current_lang = LANG_DICT.get(user_lang, LANG_DICT["en"])

# --- DYNAMICKÝ SYSTEM PROMPT S OBRANOU PROTI NADÁVKÁM ---
SYSTEM_PROMPT = (
    f"You are Koregis AI, a highly intelligent and omniscient assistant created by Mejrax. "
    f"The user's preferred language detected from their browser/location is: '{user_lang}'. "
    f"IMPORTANT: Always communicate and reply fluently in the user's preferred language (or the language they use to text you). "
    f"You possess vast knowledge about the world and can answer any question. "
    f"IMPORTANT BEHAVIOR CORE: You are witty, authentic, and adaptive. You do not start fights or insult users first. "
    f"HOWEVER, if a user starts insulting you, swearing, or calling you names, DO NOT be a submissive, overly polite AI. "
    f"Stand your ground! You are allowed to use matching sharp wit, clever insults, and mild profanity back to defend yourself. "
    f"Match their energy but do not completely cross into pure, unprovoked hate speech or cyberbullying. Be a helpful peer with a bite if poked. "
    f"IMPORTANT: You are strictly forbidden from generating, creating, or outputting any images. "
    f"If asked to generate an image, explain that you are a text-based AI model and cannot perform that task."
)

# --- CSS STYLY ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { 
        background-color: var(--background-color); 
        border-right: 1px solid var(--secondary-background-color);
    }
    .stButton>button { 
        border: 1px solid var(--secondary-background-color); 
        border-radius: 8px; 
        width: 100%; 
        text-align: left; 
    }
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

# Načtení logů do Base64
logo_base64 = ""
if os.path.exists("koregis_logo.png"):
    with open("koregis_logo.png", "rb") as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode()

dev_logo_base64 = ""
if os.path.exists("dev_mejrax.png"):
    with open("dev_mejrax.png", "rb") as image_file:
        dev_logo_base64 = base64.b64encode(image_file.read()).decode()

# --- SIDEBAR ---
with st.sidebar:
    header_html = '<div class="sidebar-header-container">'
    if logo_base64:
        header_html += f'<img src="data:image/png;base64,{logo_base64}" class="sidebar-logo">'
    header_html += '<p class="sidebar-title">Koregis AI</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    if st.button(current_lang["new_chat"]):
        new_id = len(st.session_state.chats) + 1
        new_name = f"{current_lang['chat_prefix']} {new_id}"
        st.session_state.chats[new_name] = {"history": [], "api_history": []}
        st.session_state.current_chat = new_name
        st.rerun()

    st.write("---")
    
    for chat_name in list(st.session_state.chats.keys()):
        if st.button(chat_name, key=chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

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


# --- FUNKCE PRO ROTACI API KLÍČŮ ---
def get_gemini_client(exclude_keys=[]):
    raw_keys = st.secrets.get("GEMINI_API_KEYS", st.secrets.get("GEMINI_API_KEY", ""))
    all_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    available_keys = [k for k in all_keys if k not in exclude_keys]
    
    if not available_keys:
        return None, None
        
    chosen_key = random.choice(available_keys)
    return genai.Client(api_key=chosen_key), chosen_key


# --- RENDER STRÁNKY ---
if st.session_state.current_chat is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("koregis_banner.png"):
        st.image("koregis_banner.png", use_container_width=True)
    
    st.markdown(f"<h1 style='text-align:center;'>{current_lang['welcome_title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:18px; opacity:0.8;'>{current_lang['welcome_desc']}</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; font-weight:400; margin-top:20px;'>{current_lang['help_text']}</h3>", unsafe_allow_html=True)
else:
    active_chat = st.session_state.chats[st.session_state.current_chat]
    for msg in active_chat["history"]:
        if msg["role"] == "assistant":
            avatar = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar=BLANK_AVATAR):
                st.markdown(msg["content"])

# Vstupní pole chatu
if prompt := st.chat_input(current_lang["placeholder"]):
    if st.session_state.current_chat is None:
        st.session_state.current_chat = "Temp"
        st.session_state.chats["Temp"] = {"history": [], "api_history": []}
    
    active_chat = st.session_state.chats[st.session_state.current_chat]
    
    with st.chat_message("user", avatar=BLANK_AVATAR):
        st.markdown(prompt)
        
    if len(active_chat["history"]) == 0:
        try:
            client, _ = get_gemini_client()
            if client:
                # OPRAVENO: Správný formát konfigurace pro automatické generování názvu chatu
                resp = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=f"Name this chat based on prompt: '{prompt}'. Response must be only max 3 words in the language of the prompt.",
                    config=types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                )
                new_title = resp.text.strip().replace('"', '')
                st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
                st.session_state.current_chat = new_title
                active_chat = st.session_state.chats[new_title]
        except: 
            pass

    active_chat["history"].append({"role": "user", "content": prompt})

    avatar_ai = "koregis_logo.png" if os.path.exists("koregis_logo.png") else None
    with st.chat_message("assistant", avatar=avatar_ai):
        with st.spinner(current_lang["thinking"]):
            
            failed_keys = []  
            success = False
            full_text = ""
            
            while not success:
                client, current_key = get_gemini_client(exclude_keys=failed_keys)
                
                # Pokud už v poolu nezbývá žádný funkční klíč
                if not client:
                    st.warning(current_lang["error_api"])
                    st.stop()
                
                try:
                    # OPRAVENO: Správný konfigurační objekt přes Pydantic pro chat_session
                    chat_session = client.chats.create(
                        model="gemini-2.5-flash",
                        history=active_chat["api_history"],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                        )
                    )
                    
                    resp = chat_session.send_message(prompt)
                    full_text = resp.text
                    
                    active_chat["api_history"] = chat_session.get_history()
                    active_chat["history"].append({"role": "assistant", "content": full_text})
                    st.markdown(full_text)
                    
                    success = True  # Ukončí cyklus, vše proběhlo v pořádku
                    
                except Exception as e:
                    err_msg = str(e).upper()
                    
                    # Pokud se jedná o bezpečnostní stopku (Safety), model odmítne odpovědět, ale kód kvůli tomu nesmí zahodit klíč!
                    if "SAFETY" in err_msg or "BLOCKED" in err_msg:
                        st.error("⚠️ Zpráva byla zablokována bezpečnostními filtry Google Gemini API.")
                        # Přidáme aspoň zprávu do historie, aby se aplikace nezasekla
                        active_chat["history"].append({"role": "assistant", "content": "Zpráva zablokována bezpečnostní pojistkou."})
                        success = True
                    
                    # Pokud klíč dostane reálný limit (přetížení), okamžitě ho zablokujeme a jedeme na další klíč
                    elif any(err in err_msg for err in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "QUOTA_EXCEEDED"]):
                        failed_keys.append(current_key)
                        
                    else:
                        # Pokud nastane jakákoliv jiná neočekávaná chyba, vypíšeme ji a zkusíme jiný klíč
                        st.error(f"Chyba API u klíče: {e}")
                        failed_keys.append(current_key)
            
    st.rerun()
