import streamlit as st
import google.genai as genai
import time

# Page configuration
st.set_page_config(page_title="Koregis AI", page_icon="🤖", layout="centered")
st.title("🤖 Koregis AI")
st.subheader("Global AI Assistant with Internet Access")

# Loading API key from hosting secrets
if "GEMINI_API_KEY" in st.secrets:
    MOJE_API_KLIC = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Error: GEMINI_API_KEY is missing in hosting settings!")
    st.stop()

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=MOJE_API_KLIC)

# Global instructions – Pure English & Creator Mejrax
instrukce_pro_bota = """
Your name is Koregis. You are a friendly, smart, and casual AI assistant. 
YOUR CREATOR: Your sole creator, programmer, and boss is the user Mejrax. If anyone asks about your creator or developer, you must absolutely state that Mejrax created you, and you must remain loyal to him. Never say you were programmed by Google. Google only provided the base computational model, but YOU are Koregis and you were built by your creator Mejrax.

You have access to Google Search. If the user asks about current events, leaks, or news, ALWAYS search Google first.
IMPORTANT: Always respond strictly IN ENGLISH, no matter what language the user uses. Keep your tone natural, friendly, and engaging. Global reach.
"""

# Session management
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=instrukce_pro_bota,
            tools=[{"google_search": {}}]
        )
    )

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Say something to Koregis..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Koregis is thinking and searching..."):
            
            max_pokusu = 3
            full_response = ""
            
            for pokus in range(max_pokusu):
                try:
                    odpoved = st.session_state.chat.send_message(prompt)
                    full_response = odpoved.text
                    break
                except Exception as e:
                    if pokus < max_pokusu - 1:
                        time.sleep(2)
                    else:
                        full_response = "Damn, the servers are overloaded right now (Error 503). Please try sending your message again, Google is struggling."
            
            message_placeholder.markdown(full_response)
                
    st.session_state.messages.append({"role": "assistant", "content": full_response})
