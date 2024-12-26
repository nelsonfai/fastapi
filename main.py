from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import requests
from PIL import Image
from io import BytesIO
import pytesseract
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound

app = FastAPI()

# Models for requests
class OCRRequest(BaseModel):
    image_url: HttpUrl


class TranscriptRequest(BaseModel):
    video_id: str
    languages: list = ["en"]

@app.post("/extract-text")
def extract_text(request: OCRRequest):
    """
    Extract text from an image URL and determine if it's code or plain text.
    """
    try:
        # Fetch the image from the URL
        response = requests.get(request.image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch the image from the URL.")
        
        image = Image.open(BytesIO(response.content))
        
        # Perform OCR on the image
        raw_text = pytesseract.image_to_string(image)
        
        # Classify the text as code or plain text
        if any(line.startswith(" ") or "{" in line or "}" in line or ";" in line for line in raw_text.splitlines()):
            formatted_text = {"type": "code", "content": raw_text.strip()}
        else:
            formatted_text = {"type": "text", "content": raw_text.strip()}
        
        return formatted_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/transcript")
def get_transcript(request: TranscriptRequest):
    """
    Retrieve and group YouTube video transcripts into 20-second segments.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(request.video_id, languages=request.languages)
        
        grouped_transcript = []
        current_segment = {"start": 0, "end": 20, "text": ""}
        
        for entry in transcript:
            entry_start = entry['start']
            entry_end = entry['start'] + entry['duration']
            
            if entry_start >= current_segment['end']:
                grouped_transcript.append(current_segment)
                current_segment = {"start": current_segment['end'], "end": current_segment['end'] + 20, "text": ""}
            
            current_segment['text'] += (entry['text'] + " ")
        
        grouped_transcript.append(current_segment)
        return grouped_transcript

    except TranscriptsDisabled:
        raise HTTPException(status_code=400, detail="Transcripts are disabled for this video.")
    except VideoUnavailable:
        raise HTTPException(status_code=400, detail="The video is unavailable.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found for this video in the requested languages.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
