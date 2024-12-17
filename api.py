from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from aivc.config.config import settings, L
from aivc.api import ws
from aivc.api import router
import uvicorn
from aivc.model.embed.embed import EmbedModel

app = FastAPI()

app.mount("/ui", StaticFiles(directory="ui"), name="ui")
app.mount("/doc", StaticFiles(directory="docs"), name="docs")
app.mount("/upload", StaticFiles(directory="upload"), name="upload")

@app.get("/")
def read_root():
    return FileResponse("ui/index.html")

@app.get("/trace")
def read_trace():
    return FileResponse("ui/trace.html")

app.include_router(ws.router, tags=["ws"])
app.include_router(router.api_router_v1, prefix=settings.API_V1_STR, tags=["api_v1"])

def on_start():
    EmbedModel()

if __name__ == "__main__":
    on_start()
    L.debug(f"API Listen {settings.LISTEN_IP}:{settings.PORT}")
    uvicorn.run(app, host=settings.LISTEN_IP, port=settings.PORT)