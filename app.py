import os
import time
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from PIL import Image


MEDIA_FOLDER = 'medias'

robo = Image.open('img/robo.png')

def __init__():
    if not os.path.exists(MEDIA_FOLDER):
        os.makedirs(MEDIA_FOLDER)

    load_dotenv()  ## load all the environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to the media folder and return the file path."""
    file_path = os.path.join(MEDIA_FOLDER, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.read())
    return file_path

def get_insights(video_path, pontos):
    """Extract insights from the video using Gemini Flash."""
    st.write(f"Processing video: {video_path}")
    with st.spinner("Wait for it..."):
        st.write(f"Uploading file...")
        video_file = genai.upload_file(path=video_path)
        st.write(f"Completed upload: {video_file.uri}")

        while video_file.state.name == "PROCESSING":
            st.write('video is processing.')
            time.sleep(10)
            video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)
    
    #goals = 'Level of education, English level, Experience with languages such as Python'
    
    prompt = f"Answer always in Portuguese. Use name of person in answers. Provides the insights from the video. At the end shows the main points according to this list:{pontos}"

    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
    with st.spinner("..."):
        st.write("Making LLM inference request...")
    response = model.generate_content([prompt, video_file],
                                    request_options={"timeout": 1200})
    st.write(f'Video processing complete')
    
    # Supondo que 'response' seja o objeto retornado pelo modelo
    response_data = response.candidates[0]
    
    # Acessando o consumo de tokens (se disponível)
    if hasattr(response, 'usage_metadata'):
        prompt_token_count = response.usage_metadata.prompt_token_count
        candidates_token_count = response.usage_metadata.candidates_token_count
        total_token_count = response.usage_metadata.total_token_count
    else:
        prompt_token_count = candidates_token_count = total_token_count = "N/A"

    # Acessando o nome do modelo e versão (se disponível)
    if hasattr(response, 'model_version'):
        model_version = response.model_version
    else:
        model_version = "N/A"

    st.markdown("#### Consumo de tokens:")
    st.write(f"  - Tokens do prompt: {prompt_token_count}")
    st.write(f"  - Tokens dos candidatos: {candidates_token_count}")
    st.write(f"  - Total de tokens: {total_token_count}")

    st.write(f"\nModelo e versão: {model_version}")
   
    st.subheader("Insights")
    st.write(response.text)
    genai.delete_file(video_file.name)


def app():
    html_page_title = """
    <div style="background-color:black;padding=60px">
        <p style='text-align:center;font-size:60px;font-weight:bold; color:red'>Analisador de Video</p>
    </div>
    """               
    st.markdown(html_page_title, unsafe_allow_html=True)
    
    
    st.markdown("### Objetivo:")
    st.markdown("#### Identificar pontos principais numa candidatura de vaga")
    st.sidebar.image(robo,caption="",use_container_width=False)
    
    pontos = ['Graduação', 'Pós', 'Inglês', 'Conhecimento em programação']
    st.sidebar.markdown('### Pontos inportantes:')
    for i in pontos:
        st.sidebar.write('-', i)
        
    options = st.multiselect('Selecione os pontos importantes',
                             ['Graduação', 'Pós','Inglês', 'Conhecimento em programação'],
                            ['Inglês'])
    
    pontos =' , '.join(options)
    #st.write(pontos)

    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov", "mkv"])

    if uploaded_file is not None:
        file_path = save_uploaded_file(uploaded_file)
        #st.video(file_path)
        get_insights(file_path, pontos)
        if os.path.exists(file_path):  ## Optional: Removing uploaded files from the temporary location
            os.remove(file_path)

__init__()
app()