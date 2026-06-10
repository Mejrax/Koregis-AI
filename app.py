import streamlit as str

# Page configuration
str.set_page_config(page_title="Koregis AI", page_icon="🤖", layout="centered")

# Main header
str.title("🤖 Koregis AI")
str.subheader("Your smart assistant, programmed by Mejrax.")

str.write("---")

# VIP Section
str.markdown("### 👑 Want to get the most out of Koregis AI?")
str.write(
    "Get access to **Koregis VIP**! An advanced AI coding assistant "
    "that generates high-level code, fixes complex errors, and debugs like a pro."
)

# Stripe Payment Button
stripe_url = "https://buy.stripe.com/test_aFa14o5Xmasx6q947rcAo00"
str.markdown(
    f'<a href="{stripe_url}" target="_blank">'
    '<button style="'
    'background-color: #635bff;'
    'color: white;'
    'border: none;'
    'padding: 12px 24px;'
    'font-size: 18px;'
    'font-weight: bold;'
    'border-radius: 5px;'
    'cursor: pointer;'
    'width: 100%;'
    'box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11);'
    '">Activate Koregis VIP for 99 CZK / month</button>'
    '</a>',
    unsafe_allow_html=True
)

str.write("---")

# Basic Chat Interface
str.markdown("### 💬 Chat with standard version")
user_input = str.text_input("Ask a question or enter code for Koregis AI:")

if user_input:
    str.info("Koregis AI responds: 'Hello! Mejrax is currently working on integrating my core AI features here. For advanced coding, please use the VIP button above!'")
