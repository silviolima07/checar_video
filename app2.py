import os
import time
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import whisper
import tempfile
from utils import convert_video_to_audio
from dotenv import load_dotenv
import ffmpeg
from pydub import AudioSegment

MEDIA_FOLDER = 'medias'
AUDIO_FILE = 'audio.wav'
TEXT_FILE =  'audio.txt'

load_dotenv()  ## load all the environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def extrair_audio(video_path):
    st.write('Video File: ', video_path)
    video = AudioSegment.from_file(video_path, format="mp4")
    audio = video.set_channels(1).set_frame_rate(16000)
    audio.export(f'{MEDIA_FOLDER}/{AUDIO_FILE}', format="wav")
    st.audio(f'{MEDIA_FOLDER}/{AUDIO_FILE}')
    st.success("🎧 Audio: Extração  concluida e salva!")
    st.write(f'Audio File: {MEDIA_FOLDER}/{AUDIO_FILE}')

# Função para processar áudio capturado
def process_audio_data(audio_file):

    #st.audio(audio_file)
    with st.spinner(' 🎧 Transformando Audio em Texto...'): # Transcricao
        
        try:
            model = whisper.load_model("small")
            result = model.transcribe(audio_file)
            transcribed_text = result["text"]
            #if st.button('Text File'):
            st.text(transcribed_text[:1000])  # Exibir os primeiros 1000 caracteres do texto 
            #st.write("Transcricao ok")
        except Exception as e:
            st.error(f'Checar modulo transcricao: {e}')
        
        
        try:            
            file_path = f'{MEDIA_FOLDER}/{TEXT_FILE}'
            with open(file_path, 'w', encoding='utf-8') as f: # 'w' para texto
                f.write(transcribed_text)
            st.success("🎧 Audio -> Texto: Transcricao  concluida e salva!")  
            st.write(f'Text File: {MEDIA_FOLDER}/{TEXT_FILE}')
            
            
        except Exception as e:
            st.error(f'Checar modulo de salvamento do txt: {e}')        
        

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

def get_insights(video_path):
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
    
    goals = 'Level of education, English level, Experience with languages such as Python'
    
    prompt = f"Answer always in Portuguese. Describe the video. Provides the insights from the video. At the end shows the main points according to this list:{goals}"

    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
    with st.spinner("..."):
        st.write("Making LLM inference request...")
    response = model.generate_content([prompt, video_file],
                                    request_options={"timeout": 600})
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
    
    lista_model = ["llama-3.1-70b-versatile", 'gemini-1.5-flash']
    MODEL = st.sidebar.selectbox(
        "Selecione o modelo:",
        lista_model
    )
    st.sidebar.markdown("### LLM: " )
    st.sidebar.markdown("## " + MODEL)
    
    
    
    # Initialize LLM
    llm = ChatGroq(
            model=MODEL,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )


    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov", "mkv"])

    if uploaded_file is not None:
        video_path = save_uploaded_file(uploaded_file)
        #st.video(file_path)
        #if os.path.exists(file_path):  ## Optional: Removing uploaded files from the temporary location
        #    os.remove(file_path)
        
        if st.button("Start Analysis"):
           if MODEL == lista_model[0]:
               try:
                   st.markdown("#### Extrair audio")
                   with st.spinner("Extraindo audio"):
                       # Extrair audio from video
                       audio = extrair_audio(video_path)
               except Exception as e:
                   st.error(f'Checar extrair_audio: {e}')
                   
               if audio:
                   try:
                       st.markdown('#### Processar audio e gerar txt') 
                       #with st.spinner("Transcrever audio"):
                       # Extrair audio from video
                       process_audio_data(f'{MEDIA_FOLDER}/{AUDIO_FILE}')
                   except Exception as e:
                       st.error(f'Checar process_audio_data: {e}')
                                       
                        
        
__init__()
app()