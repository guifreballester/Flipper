from PyPDF2 import PdfReader
from pathlib import Path
import openai
import re
from pydub import AudioSegment
from secrets.config import OPENAI_API_KEY

# Function to read PDF and extract text using the updated PdfReader class
def extract_text_from_pdf(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    text = ''
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

# Function to split text into chunks by complete sentences
def split_text(text, max_length):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunk = ""

    for sentence in sentences:
        # Check if adding the sentence exceeds the limit
        if len(chunk) + len(sentence) > max_length:
            if chunk:
                yield chunk  # Yield the current chunk
                chunk = ""  # Start a new chunk

        # If a single sentence is too long, split it further
        while len(sentence) > max_length:
            # Find a natural split point (like a comma or semicolon)
            split_index = sentence.rfind(',', 0, max_length)
            if split_index == -1:
                split_index = sentence.rfind(';', 0, max_length)
            if split_index == -1:
                split_index = max_length

            part = sentence[:split_index].strip()
            sentence = sentence[split_index:].strip()

            if part:
                yield part

        chunk += sentence + " "

    if chunk.strip():
        yield chunk

# Function to convert text to speech and save as multiple MP3 files
def text_to_speech(text, output_path):
    if not output_path.is_dir():
        raise ValueError(f"Output path {output_path} is not a directory")

    for i, chunk in enumerate(split_text(text, 4096)):
        if not chunk.strip():
            print(f"Skipping empty chunk at index {i}")
            continue

        chunk_filename = f"{output_path.stem}_{i}.mp3"
        chunk_path = output_path.joinpath(chunk_filename)

        try:
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice="alloy",
                input=chunk
            )
            if response:
                response.stream_to_file(chunk_path)
        except Exception as e:
            print(f"Error in generating speech for chunk {i}: {e}")

# Function to concatenate audio files into a single MP3 file
def concatenate_audio(files, output_file):
    combined = AudioSegment.empty()
    for file in files:
        audio = AudioSegment.from_mp3(file)
        combined += audio
    combined.export(output_file, format="mp3")

# Main script
if __name__ == "__main__":
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    pdf_path = './input.pdf'
    temp_output_path = Path('./temp_output')  # Temporary directory to save individual MP3 files
    temp_output_path.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
    final_output_path = Path('final_output.mp3')  # Path for the final concatenated MP3 file

    text = extract_text_from_pdf(pdf_path)
    text_to_speech(text, temp_output_path)

    # Collecting paths of all generated MP3 files and sorting them
    mp3_files = sorted(temp_output_path.glob('*.mp3'), key=lambda f: int(f.stem.split('_')[-1]))

    # Concatenate all MP3 files into one
    concatenate_audio(mp3_files, final_output_path)

    print("Final MP3 file has been created successfully!")
