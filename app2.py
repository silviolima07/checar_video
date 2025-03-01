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
from crewai import Agent, Task, Crew, Process
from MyLLM import MyLLM

from crewai import Agent, Task, Crew
from groq import Groq  
import os
load_dotenv()

# Obter a chave da API GROQ
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configuração do cliente Groq
client = Groq(api_key=GROQ_API_KEY)
llm_groq = MyLLM.GROQ_DEEPSEEK


MEDIA_FOLDER = 'medias'
AUDIO_FILE = 'audio.wav'
TEXT_FILE =  'audio.txt'

load_dotenv()  ## load all the environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Listas para armazenar os dados
nomes = []
idades = []
cidades = []
educacao = []
ingles = []
linguagens = []
experiencia = []
voluntariado = []
comunidades = []

# Função para processar a resposta do modelo e extrair informações
def processar_resposta(resposta):
    # Função auxiliar para extrair campos com segurança
    def extrair_campo(texto, delimitador, padrao="N/A"):
        if delimitador in texto:
            return texto.split(delimitador)[1].split("\n")[0].strip()
        return padrao
        
    # Extraindo informações da resposta (ajuste conforme necessário)
    #nome = resposta.split("Nome:")[1].strip()
    idade = resposta.split("Idade:")[1].split("anos")[0].strip()
    cidade = resposta.split("Cidade de Residência:")[1].split("\n")[0].strip()
    educ = resposta.split("Nível de Educação:")[1].split("Nível de Inglês:")[0].strip()
    ingl = resposta.split("Nível de Inglês:")[1].split("Experiência com Linguagens de Programação:")[0].strip()
    ling = resposta.split("Experiência com Linguagens de Programação:")[1].split("Experiência Profissional:")[0].strip()
    exp = resposta.split("Experiência Profissional:")[1].split("Experiência em Voluntariado:")[0].strip()
    vol = resposta.split("Experiência em Voluntariado:")[1].split("Participação em Comunidades:")[0].strip()
    com = resposta.split("Participação em Comunidades:")[1].split("Conclusão:")[0].strip()

    # Adicionando os dados às listas
    #nomes.append(nome)
    idades.append(idade)
    cidades.append(cidade)
    educacao.append(educ)
    ingles.append(ingl)
    linguagens.append(ling)
    experiencia.append(exp)
    voluntariado.append(vol)
    comunidades.append(com)

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
            st.markdown('#### Texto Extraído:')
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
    
    pontos = 'Level of education, English level, Experience with languages such as Python'
    
    prompt = f"Answer always in Portuguese. Describe the video. Provides the insights from the video. At the end shows the main points according to this list:{pontos}"

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


def criar_agent_task(llm_groq, texto, pontos):
    """
    Criar a agente que irá  analisar o texto extraído,resumir e identificar os pontos importantes.
    """
    recrutador = Agent(
        role="Recrutador",
        goal="Analisar o texto, identificar os pontos considerados importantes e gerar um resumo.",
        backstory="Vocé é um recrutador experiênte e conssegue analisar um texto extraído de uma entrevista com um candidato.",
        verbose=True,
        allow_delegation=False,
        llm=llm_groq
        )

    analisar = Task(
        description=f"Análise o texto: {texto} Identifique os pontos considerados importantes: {pontos}. Na resposta, formeça um resumo e indique se os pontos imprtantes foram identificados",
        expected_output="Respostas claras baseadas no texto.",
        agent=recrutador
        )

    return recrutador, analisar
    
    
    

def app():
    html_page_title = """
    <div style="background-color:black;padding=60px">
        <p style='text-align:center;font-size:60px;font-weight:bold; color:red'>Analisador de Video</p>
    </div>
    """               
    st.markdown(html_page_title, unsafe_allow_html=True)
    
    
    st.markdown("### Objetivo:")
    st.markdown("#### Identificar pontos principais numa candidatura de vaga")
    
    #pontos = 'Level of education, English level, Experience with languages such as Python'
    pontos = 'Nível de Educação, Nível de Inglês , Experiência com Linguagens de Programação, Experiência Profssional,  Experiência em Voluntáriado, Participação em Comunidades'
    lista_pontos = ['Nível de Educação', 'Nível de Inglês' , 'Experiência com Linguagens de Programação', 'Experiência Profssional',  'Experiência em Voluntáriado', 'Participação em Comunidades']
    lista_model = ["deepseek-r1-distill-qwen-32b", 'gemini-1.5-flash']
    MODEL = st.sidebar.selectbox(
        "Selecione o modelo:",
        lista_model
    )
    st.sidebar.markdown("### LLM: " )
    st.sidebar.markdown("## " + MODEL)
    
    
    # Initialize LLM
    llm_chat = ChatGroq(
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
                       time.sleep(5)
                       audio = extrair_audio(video_path)
               except Exception as e:
                   st.error(f'Checar extrair_audio: {e}')
                   
            
               try:
                   st.markdown('#### Processar audio e gerar txt') 
                   with st.spinner("Transcrever audio"):
                       # Extrair audio from video
                       process_audio_data(f'{MEDIA_FOLDER}/{AUDIO_FILE}')
               except Exception as e:
                   st.error(f'Checar process_audio_data: {e}')
            
               #  Criar agent e task
               #st.markdown("#### Criar agent e task no CrewAI")
               #MODEL = f'deepseek/{MODEL}'
               
               file_path = f'{MEDIA_FOLDER}/{TEXT_FILE}' # Text File
               with open(file_path, 'r', encoding='utf-8') as f:
                  texto = f.read()
               
               #st.write("Text File:", texto)
               st.markdown("### Pontos Importantes:")
               for i, ponto in enumerate(lista_pontos, start=1):
                   st.write(i, ' - ', ponto.capitalize())
               inputs = {'texto': texto, 'pontos': pontos}
               recrutador, analisar = criar_agent_task(llm_groq, texto, pontos)            
               crew = Crew(
                    agents=[recrutador],
                    tasks=[analisar],
                    process=Process.sequential,
                    verbose=False,
                    max_rpm=30
                     )
               
               result = crew.kickoff(inputs=inputs)  
               st.write("Result:", result.raw)
               st.write("Token_usage:", result.token_usage)
               processar_resposta(result.raw)
               df = pd.DataFrame(dados)

               # Exibindo o DataFrame
               st.table(df)

               # Salvando o DataFrame em um arquivo CSV (opcional)
               df.to_csv("analise_candidatos.csv", index=False)
                              
        
__init__()
app()