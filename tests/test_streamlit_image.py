import streamlit as st
from PIL import Image
# from paragraphica.dalle import get_picture
from base64 import b64decode

# from ChatModel import *

class ImageModel:
    DEFAULT_SYSTEM_PROMPT = "You are a very skilled Python programmer. That uses decorators and generators a lot. You do not give answers in other programming languages."
    MODEL = "gpt-3.5-turbo"

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()
        self.history = []
        self.size="1024x1024"
        self.quality="standard"

    def generate(self, prompt, model, image_quality, image_style, gen_style):
        prompt += "Use {} as image style.".format(image_style)
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=self.size,
            style=gen_style,
            quality=image_quality,
            response_format='b64_json',
            n=1,
        )

        image_data = b64decode(response.data[0].b64_json)
        prompt = response.data[0].revised_prompt
        return prompt, image_data
    

@st.cache_resource
def load_model():
    model = ImageModel()
    return model


# streamlit run tests/test_streamlit.py
if __name__ == '__main__':
    st.title("Paragraphica Converser")

    model = load_model()  # load our ChatModel once and then cache it

    with st.sidebar:
        image_model = st.selectbox("What chat model would you like to use?", ("dall-e-3", "dall-e-2"))
        image_size = st.selectbox("Select size", ("256x256", "1012x1012"))
        image_quality = st.selectbox("Select quality", ("standard", "hd"))
        gen_style = st.selectbox("Select generation style", ("natural", "vivid"))
        image_style = st.selectbox("What style would you like to use?", ("realistic", "film noir", "painting", "manga"))

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What shall I draw?"):
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
                image_style=image_style,
                image_quality=image_quality,
                gen_style=gen_style,
                model=image_model
            )
            st.image(answer[1], caption=answer[0])
        st.session_state.messages.append({"role": "assistant", "content": answer})