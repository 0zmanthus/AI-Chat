# My code

# Don't forget to do source .venv/bin/activate

# Key: gen-lang-client-0003236354
```
# Web Framework
import streamlit as st
import openai
# LLM Interaction
from openai import OpenAI
import os # To access the API key

# For potentially handling conversation history
import json

if "client" not in st.session_state:
    st.session_state["client"] = None
try:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    )
    if 'openai_api_key' in st.session_state and st.session_state['openai_api_key']:
        client.api_key = st.session_state['openai_api_key']

except Exception as e:
    # This try block handles initialization errors
    pass

#default model for the chat
DEFAULT_MODEL = "gpt-4o-mini"


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a concise and are a helpful AI assistant"}, 
        {"role": "assistant", "content": "Hey! What can we accomplish today?"}
    ]
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = ""
if "model_name" not in st.session_state:
    st.session_state["model_name"] = DEFAULT_MODEL

#core logic: using the OpenAi API
def generate_response():
    try:
        if not client.api_key:
            st.error("Please enter your OpenAI API Key in the sidebar to start chatting.")
            return

        #prepare the conversation history for the APU call
        messages_for_api = st.session_state["messages"]

        # Call the OpenAI API
        stream = client.chat.completions.create(
            model=st.session_state["model_name"],
            messages=messages_for_api,
            stream=True
        )

        # Ctreate a placeholder in the chat interface to stream the response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌") # Add blinking cursor effect
                    
            placeholder.markdown(full_response) # Final content

        # Append the complete assistant
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

    except Exception as e:
        # Display a user-friendly error message if the api call fails
        if "Invalid API key" in str(e):
            st.error("Error: The API key you provided is invalid. Please check and update it.")
        else:
            st.error(f"An API error occured: {e}")

# streamlit UI layout

st.set_page_config(page_title="Open AI Chat", layout="centered")
st.title("Open AI Assistant")

# Sidebar configuration 
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state["openai_api_key"],
        placeholder="sk-...",
        key="api_key_input"
    )

    # Update session state
    if api_key_input != st.session_state["openai_api_key"]:
        st.session_state["openai_api_key"] = api_key_input
        # Reinitialize client with new key
        try:
            client.api_key = api_key_input
        except Exception:
            pass # Ignore exception if key is invalid during setup

    st.caption("Get your key from [OpenAI](https://platform.openai.com/api-keys)")

    st.selectbox(
        "Select Model",
        options=["gpt-4o-mini", "gpt-3.5-turbo"],
        index=0,
        key="model_name"
    )

    if st.button("Clear History", use_container_width=True):
        st.session_state["messages"] = [
             {"role": "system", "content": "You are a helpful, professional, and friendly AI assistant. Keep your answers concise and informative."},
            {"role": "assistant", "content": "Conversation history cleared. How can I help you today?"}
        ]
        st.rerun()
        
for message in st.session_state["messages"][1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input handling
if prompt := st.chat_input("Ask me anything..."): 
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Displays the message the user sent out
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the function to generate and stream in the chat interface
    generate_response()

st.markdown("---")
st.caption("""
**JSON Usage Note:** We use Python dictionaries to structure the chat history (`{"role": "...", "content": "..."}`). This format is inherently JSON-compatible. If you wanted to *save* this history to a file, you would use `json.dump(st.session_state["messages"], file)` and `json.load(file)` to retrieve it, using the built-in `json` module.
""")
```
