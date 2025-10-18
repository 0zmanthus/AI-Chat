import streamlit as st
import json
# LLM Interaction
# from openai import OpenAI # Original library
from google import genai # New library for Gemini
from google.genai import types
from google.genai.errors import APIError as GeminiAPIError
import os # To access the API key

# --- Configuration ---
DEFAULT_MODEL = "gemini-2.5-flash" # Changed default model to Gemini

# Initialize client in the global scope. We will set its value (Gemini client object or None) later.
if "client" not in st.session_state:
    st.session_state["client"] = None

# We rely on session state for initialization, but check environment/secrets first
# to populate the sidebar text input's initial value.
# Changed environment variable name from OPENAI_API_KEY to GEMINI_API_KEY
initial_api_key = os.getenv("GEMINI_API_KEY") 

if not initial_api_key:
    try:
        # Check secrets only if environment variable is not set
        initial_api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        # Catch the exception (StreamlitSecretNotFoundError) and ensure the key is None
        initial_api_key = None

# Ensure initial_api_key is an empty string if it remains None/falsy
initial_api_key = initial_api_key or ""


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        # System instruction is handled separately for the Gemini API call
        {"role": "system", "content": "You are a concise and are a helpful AI assistant"}, 
        {"role": "assistant", "content": "Hey! What can we accomplish today?"}
    ]

# Changed session state key from openai_api_key to gemini_api_key
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = initial_api_key

if "model_name" not in st.session_state:
    st.session_state["model_name"] = DEFAULT_MODEL

# --- Initial Client Setup (if key is present but client is None) ---
if st.session_state["gemini_api_key"] and st.session_state["client"] is None:
    try:
        # Create the Gemini client object here and save it to session state
        st.session_state["client"] = genai.Client(api_key=st.session_state["gemini_api_key"])
    except Exception:
        # If the key is initially invalid, keep client as None and rely on user input
        st.session_state["client"] = None

# --- Core Logic: Calling the Gemini API ---

def generate_response():
    # Use the client object stored in session state
    client = st.session_state["client"]
    
    try:
        # Check if the client object itself was successfully initialized.
        if client is None:
            st.error("The Gemini client is not initialized. Please ensure your API key is valid and entered.")
            return

        # 1. Extract System Instruction (first message)
        system_instruction = st.session_state["messages"][0]["content"]
        
        # 2. Prepare the conversation history for the API call (skip system message)
        messages_for_api = []
        # Start from index 1 to skip the system message
        for msg in st.session_state["messages"][1:]:
            # Map 'assistant' role to 'model' for the Gemini API
            role = "model" if msg["role"] == "assistant" else msg["role"]
            
            # Gemini API expects 'parts' with 'text'
            # FIX: Changed types.Part.from_text(msg["content"]) to types.Part(text=msg["content"])
            messages_for_api.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                )
            )
        
        # 3. Call the Gemini API using streaming
        # We use generate_content_stream for a simple, single-call conversational turn.
        stream = client.models.generate_content_stream(
            model=st.session_state["model_name"],
            contents=messages_for_api,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        # 4. Create a placeholder in the chat interface to stream the response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in stream:
                # The Gemini stream returns text in chunk.text
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌") # Add blinking cursor effect
                    
            placeholder.markdown(full_response) # Final content

        # Append the complete assistant response to the session state history
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

    except GeminiAPIError as e:
        # Handle specific Gemini API errors
        if "API key not valid" in str(e):
            st.error("Error: The Gemini API key you provided is invalid. Please check and update it.")
        else:
            st.error(f"An API error occurred: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


# --- Streamlit UI Layout ---

st.set_page_config(page_title="Gemini Chat", layout="centered") # Updated title
st.title("Gemini AI Assistant") # Updated title

# Sidebar configuration 
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input(
        "Gemini API Key", # Updated text label
        type="password",
        value=st.session_state["gemini_api_key"],
        placeholder="AIza...", # Updated placeholder
        key="api_key_input"
    )

    # Update session state and client instance based on input
    if api_key_input != st.session_state["gemini_api_key"]:
        st.session_state["gemini_api_key"] = api_key_input
        # Reinitialize client with new key or set to None if key is empty
        if api_key_input:
            try:
                # Create the client object here and save it to session state
                st.session_state["client"] = genai.Client(api_key=api_key_input)
            except Exception as e:
                st.error(f"Error creating client: {e}")
                st.session_state["client"] = None
        else:
            st.session_state["client"] = None

        # Rerun to apply changes immediately (important for the client object)
        st.rerun()

    st.caption("Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)") # Updated link

    st.selectbox(
        "Select Model",
        # Updated models for Gemini
        options=["gemini-2.5-flash", "gemini-2.5-pro"],
        index=0,
        key="model_name"
    )

    if st.button("Clear History", use_container_width=True):
        st.session_state["messages"] = [
             {"role": "system", "content": "You are a helpful, professional, and friendly AI assistant. Keep your answers concise and informative."},
             {"role": "assistant", "content": "Conversation history cleared. How can I help you today?"}
        ]
        st.rerun()
        
# --- Display Chat History ---
# We skip the system message (index 0)
for message in st.session_state["messages"][1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input Handling ---
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
