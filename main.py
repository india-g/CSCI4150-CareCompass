from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.post("/api/test")
async def test(body: dict):
    return {"message": body["text"].upper()}

# Mount last so it doesn't shadow the /api routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")
