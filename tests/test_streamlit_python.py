import streamlit as st
# from ChatModel import *


# streamlit run tests/test_streamlit.py

st.title("Open AI Python Code Assistent")

class ChatModel:
    DEFAULT_SYSTEM_PROMPT = "You are a very skilled Python programmer. That uses decorators and generators a lot. You do not give answers in other programming languages."
    MODEL = "gpt-3.5-turbo"

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()
        self.history = []

    def generate(self, prompt, top_p, temperature, max_new_tokens, system_prompt, chat_model=MODEL):
        thread = [
            {"role": "system", "content": system_prompt} 
        ]
        if len(self.history) > 10:
            thread += self.history[-10]
        else:
            thread += self.history
        thread.append({"role": "user", "content": prompt})
        # print(thread)
        res = self.client.chat.completions.create(
            model = chat_model,
            messages = thread,
            max_tokens=max_new_tokens,
            temperature=temperature, 
            top_p = top_p,
        ).choices[0].message.content
        self.history.append(
            {"role": "user", "content": prompt}
        )
        self.history.append(
            {"role": "assistant", "content": res}
        )
        # print(self.history)
        return res
    

@st.cache_resource
def load_model():
    model = ChatModel()
    return model


model = load_model()  # load our ChatModel once and then cache it

with st.sidebar:
    chat_model = st.selectbox("What chat model would you like to use?", ("gpt-3.5-turbo", "gpt-4"))
    temperature = st.slider("temperature", 0.0, 2.0, 0.1)
    top_p = st.slider("top_p", 0.0, 1.0, 0.9)
    max_new_tokens = st.number_input("max_new_tokens", 128, 4096, 512)
    system_prompt = st.text_area(
        "system prompt", value=model.DEFAULT_SYSTEM_PROMPT, height=500
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask me anything!"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        user_prompt = st.session_state.messages[-1]["content"]
        answer = model.generate(
            user_prompt,
            top_p=top_p,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            system_prompt=system_prompt,
            chat_model=chat_model,
        )
        response = st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})