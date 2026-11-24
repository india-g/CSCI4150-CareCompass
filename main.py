# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    gemini_key: str
    gemini_model: str
    system_prompt: str


settings = Settings()
client = genai.Client(api_key=settings.gemini_key)
app = FastAPI()


class Message(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    messages: list[Message]


@app.post("/api/chat")
async def chat(body: ChatRequest):
    contents = [{"role": m.role, "parts": [{"text": m.text}]} for m in body.messages]

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=settings.system_prompt,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )
    return {"reply": response.text}


# Mount last so it doesn't shadow the /api routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")