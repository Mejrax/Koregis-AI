import streamlit as st
import google.genai as genai
from PIL import Image
import os

# 1. Konfigurace stránky na široké zobrazení + skrytí standardních prvků Streamlitu
st.set_page_config(page_title="Koregis AI", page_icon="💬", layout="wide")

# Vynucení moderního čistého stylu pomocí CSS (zakulacení oken, čisté barvy)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f8fafd; }
    .stButton>button { border-radius: 20px; width: 100%; font-weight: 500; }
    div[data-testid="stChatInput"] { border-radius: 30px; }
    </style>
""", unsafe_allow_html=True)

# Načtení tvého vlastního loga ze složky na GitHubu
logo_path = "koregis_logo.png"
if os.path.exists(logo_path):
    bot_avatar = Image.open(logo_path)
else:
    bot_avatar = "💬"

# --- LEVÝ SIDEBAR (PŘESNĚ PODLE GEMINI) ---
# Horní část: Nový chat
if st.sidebar.button("➕ New Chat", type="secondary"):
    if "chats_dict" in st.session_state and len(st.session_state.chats_dict) < 5:
        new_id = len(st.session_state.chats_dict) + 1
        st.session_state.chats_dict[f"Chat {new_id}"] = []
        st.session_state.current_chat = f"Chat {new_id}"
        st.rerun()
    elif "chats_dict" in st.session_state:
        st.sidebar.warning("Max 5 chats reached!")

st.sidebar.write("---")
st.sidebar.markdown("### 📂 Recent")

# Inicializace paměti chatů
if "chats_dict" not in st.session_state:
    st.session_state.chats_dict = {"Chat 1": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

# Seznam chatů (max 5) v historii sidebaru
for chat_name in list(st.session_state.chats_dict.keys()):
    is_active = chat_name == st.session_state.current_chat
    btn_type = "primary" if is_active else "secondary"
    if st.sidebar.button(f"💬 {chat_name}", key=f"side_{chat_name}", type=btn_type):
        st.session_state.current_chat = chat_name
        st.rerun()

# Spodní část sidebaru: Profil stvořitele
st.sidebar.markdown("<div style='position: fixed; bottom: 20px;'>", unsafe_allow_html=True)
st.sidebar.write("---")
col_user_ico, col_user_name = st.sidebar.columns([1, 4])
with col_user_ico:
    st.markdown("<h3 style='margin:0;'>👤</h3>", unsafe_allow_html=True)
with col_user_name:
    st.markdown("**MEJRAX**\n<small>Creator & Developer</small>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)


# --- AI CONFIG & SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
    MOJE_API_KLIC = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
    st.stop()

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=MOJE_API_KLIC)

instrukce_pro_bota = """
Jmenuješ se Koregis. Jsi přátelský, inteligentní a neformální AI asistent.
TVŮJ STVOŘITEL: Tvým jediným stvořitelem a šéfem je Mejrax. Odpovídej vždy v jazyce uživatele.
Máš přístup na internet přes Google vyhledávač, vyhledej si info vždy, když se tě někdo ptá na novinky.
"""

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = st.session_state.client.chats.create_chat(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=instrukce_pro_bota,
            tools=[{"google_search": {}}]
        )
    )

# --- HLAVNÍ OBRAZOVKA (GEMINI STYLE) ---
active_messages = st.session_state.chats_dict[st.session_state.current_chat]

# POKUD JE CHAT PRÁZDNÝ -> Zobrazí se vycentrované Gemini uvítání bez jména
if len(active_messages) == 0:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; font-weight: 400; color: #1e1e1e;'>Let's do this</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #444746; font-size: 1.2rem;'>Koregis AI is ready. How can I help you today?</p>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# POKUD UŽ CHAT BĚŽÍ -> Vykreslí se historie zpráv
else:
    for message in active_messages:
        current_avatar = bot_avatar if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=current_avatar):
            st.markdown(message["content"])

# Vstupní pole chatu
if prompt := st.chat_input("Ask Koregis..."):
    # Pokud byl chat prázdný, po stisknutí Enteru se stránka překreslí a uvítání zmizí
    if len(active_messages) == 0:
        st.session_state.chats_dict[st.session_state.current_chat].append({"role": "user", "content": prompt})
        st.rerun()

    # Zobrazení zprávy uživatele
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.chats_dict[st.session_state.current_chat].append({"role": "user", "content": prompt})

    # Odpověď bota
    with st.chat_message("assistant", avatar=bot_avatar):
        message_placeholder = st.empty()
        with st.spinner(""):
            try:
                odpoved = st.session_state.gemini_chat.send_message(prompt)
                full_response = odpoved.text
            except Exception as e:
                full_response = "Sorry, I encountered an issue. Please try again."
            
            message_placeholder.markdown(full_response)

    st.session_state.chats_dict[st.session_state.current_chat].append({"role": "assistant", "content": full_response})
    st.rerun()
