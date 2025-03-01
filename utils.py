import os
import subprocess
from pydub import AudioSegment
from groq import Groq
import argparse
from dotenv import load_dotenv

load_dotenv()  ## load all the environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq()


def teste():
    pass

def convert_video_to_audio(video_path, audio_path):
    """Convert video file to audio file using ffmpeg"""
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ar", "16000",  # Set sample rate to 16000 Hz
        "-ac", "1",      # Set to mono
        "-f", "wav",     # Output format
        audio_path
    ]
    subprocess.run(command, check=True)

def segment_audio(audio_path, segment_length_ms=30000, output_dir="segments"):
    """Segment audio file into smaller chunks"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    audio = AudioSegment.from_wav(audio_path)
    duration_ms = len(audio)
    segments = []

    for i in range(0, duration_ms, segment_length_ms):
        segment = audio[i:i+segment_length_ms]
        segment_path = os.path.join(output_dir, f"segment_{i//segment_length_ms}.wav")
        segment.export(segment_path, format="wav")
        segments.append(segment_path)
    
    return segments

def transcribe_segment(segment_path):
    """Transcribe a single audio segment using Groq API"""
    with open(segment_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(segment_path, file.read()),
            model="distil-whisper-large-v3-en",
            response_format="json"
        )
        print(transcription)
    return transcription.text

def transcribe_course_video(video_path, output_dir):
    """Transcribe a course video and save the transcription"""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the base name of the video file (without extension)
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Set paths for temporary files
    audio_path = os.path.join(output_dir, f"{video_name}_temp_audio.wav")
    segments_dir = os.path.join(output_dir, f"{video_name}_segments")

    # Convert video to audio
    convert_video_to_audio(video_path, audio_path)

    # Segment audio
    segments = segment_audio(audio_path, output_dir=segments_dir)

    # Transcribe segments
    full_transcription = ""
    for segment in segments:
        transcription = transcribe_segment(segment)
        full_transcription += transcription + " "

    # Clean up temporary files
    os.remove(audio_path)
    for segment in segments:
        os.remove(segment)
    os.rmdir(segments_dir)

    # Save the transcription to a file
    transcription_path = os.path.join(output_dir, f"{video_name}_transcription.txt")
    with open(transcription_path, "w") as f:
        f.write(full_transcription.strip())

    return transcription_path

def process_video_directory(input_dir, output_dir):
    """Process all videos in the input directory"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing videos from: {input_dir}")
    print(f"Saving transcriptions to: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith((".mp4", ".avi", ".mov", ".mkv")):  # Add more video extensions if needed
            video_path = os.path.join(input_dir, filename)
            print(f"Processing video: {filename}")
            transcription_path = transcribe_course_video(video_path, output_dir)
            print(f"Transcription saved to: {transcription_path}")