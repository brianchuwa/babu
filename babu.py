import streamlit as st
from openai import OpenAI
import time

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set your Assistant ID
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]

# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Set up the Streamlit page
st.title("Babu wa Selous, niulize chochote...")

# Initialize the thread if it doesn't exist
if st.session_state.thread_id is None:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# Create chat input
if prompt := st.chat_input("Karibu, unaweza kuniuliza swali lolote kuhusu Selous Marathon..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response with loading indicator
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Add message to thread
            message = client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
            
            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )
            
            # Wait for the assistant to complete its response
            while run.status == "queued" or run.status == "in_progress":
                time.sleep(0.5)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
            
            # Get the assistant's messages
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            
            # Get assistant's response
            assistant_message = messages.data[0].content[0].text.value
            
            # Display the response
            st.write(assistant_message)
            
            # Add to message history
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})

# Display chat history (excluding the last exchange which we already displayed)
for message in st.session_state.messages[:-2] if len(st.session_state.messages) > 2 else []:
    with st.chat_message(message["role"]):
        st.write(message["content"])