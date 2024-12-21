from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound

app = FastAPI()

class TranscriptRequest(BaseModel):
    video_id: str
    languages: list = ["en"]

@app.post("/transcript")
def get_transcript(request: TranscriptRequest):
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
