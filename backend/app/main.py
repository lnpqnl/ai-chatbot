from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.domains.transport.application.chat_route import router as chat_router

app = FastAPI(title="AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
