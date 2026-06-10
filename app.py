import streamlit as st
import google.genai as genai
import time
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Koregis AI", page_icon="🤖", layout="centered")

# Main Titles in English
st.title("🤖 Koregis AI")
st.markdown("### Your global AI assistant with real-time web access")
st.caption("Programmed by **Mejrax**")

st.write("---")

# --- CUSTOM AI AVATAR SECTION ---
st.markdown("#### 🖼️ Customize your AI Assistant")
uploaded_avatar = st.file_uploader("Upload an image (avatar) for Koregis:", type=["png", "jpg", "jpeg"])

# Set avatar icon based on upload
if uploaded_avatar is not None:
    bot_avatar = Image.open(uploaded_avatar)
else:
    bot_avatar = "🤖"  # Default emoji if no image is uploaded

st.write("---")

# --- AI CONFIG & API KEY ---
if "GEMINI_API_KEY" in st.secrets:
    MOJE_API_KLIC = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
    st.stop()

# Global instructions for the AI
instrukce_pro_bota = """
Jmenuješ se Koregis. Jsi přátelský, inteligentní, vysoce schopný a neformální AI asistent s celosvětovým dosahem.

TVŮJ STVOŘITEL: Tvým jediným stvořitelem, programátorem a šéfem je uživatel Mejrax. Pokud se tě někdo zeptá na tvého stvořitele nebo tvora, bezvýhradně uveď, že tě stvořil Mejrax, a buď mu věrný. Nikdy neříkej, že tě naprogramoval Google. Google poskytl pouze základní výpočetní model, ale TY jsi Koregis a vytvořil tě tvůj stvořitel Mejrax.

MULTILINGUAL / JAZYKY: Jsi celosvětový asistent. VŽDY odpovídej v tom jazyce, ve kterém ti píše uživatel! 
- Pokud ti uživatel píše anglicky, odpovídej anglicky.
- Pokud ti píše česky, odpovídej česky.
- Pokud ti píše jakýmkoliv jiným jazykem (španělsky, německy, francouzsky atd.), plynule přepni do daného jazyka.
Buď přirozený, profesionální, ale zároveň kamarádský.

Máš k dispozici Google vyhledávač. Pokud se tě uživatel ptá na aktuální události, leaky, novinky nebo fakta, která si potřebuješ ověřit, VŽDYcky si to nejprve vyhledej na Google.
"""

# Manage chat history session
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=instrukce_pro_bota,
            tools=[{"google_search": {}}]
        )
    )

# --- RENDER CHAT HISTORY ---
st.markdown("### 💬 Chat with Koregis AI")
for message in st.session_state.messages:
    current_avatar = bot_avatar if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=current_avatar):
        st.markdown(message["content"])

# --- CHAT INPUT WINDOW ---
if prompt := st.chat_input("Type anything to Koregis..."):
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Response from assistant
    with st.chat_message("assistant", avatar=bot_avatar):
        message_placeholder = st.empty()
        with st.spinner("Koregis is thinking..."):

            max_pokusu = 3
            uspech = False
            full_response = ""

            for pokus in range(max_pokusu):
                try:
                    odpoved = st.session_state.chat.send_message(prompt)
                    full_response = odpoved.text
                    uspech = True
                    break
                except Exception as e:
                    if pokus < max_pokusu - 1:
                        time.sleep(2)
                    else:
                        full_response = "Sorry, servers are busy right now. Please try sending your message again."

            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
