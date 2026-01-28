from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import accounts, threads, ai

app = FastAPI(title="MailPilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(accounts.router)
app.include_router(threads.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"ok": True}
