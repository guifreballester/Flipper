import openai
from pydub import AudioSegment
import os
from secrets.config import OPENAI_API_KEY

# Function to split large audio file into smaller chunks
def split_audio(file_path, chunk_size=10*60*1000):  # 10 minutes chunks
    audio = AudioSegment.from_mp3(file_path)
    chunks = [audio[i:i+chunk_size] for i in range(0, len(audio), chunk_size)]
    return chunks

# Function to transcribe audio
def transcribe_audio(client, audio_chunk):
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_chunk,
        response_format="text"
    )
    return transcript

if __name__ == "__main__":
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    audio_chunks = split_audio("./rsc35_rsc167_65-audio.mp3")

    # Open a file to write the transcriptions
    with open("transcription.txt", "w") as file:
        for idx, chunk in enumerate(audio_chunks):
            chunk.export(f"temp_chunk_{idx}.mp3", format="mp3")
            with open(f"temp_chunk_{idx}.mp3", "rb") as audio_file:
                transcription = transcribe_audio(client, audio_file)
                # Write each chunk's transcription to the file
                file.write(transcription + "\n\n")

    # Clean up temporary files
    for idx in range(len(audio_chunks)):
        os.remove(f"temp_chunk_{idx}.mp3")
