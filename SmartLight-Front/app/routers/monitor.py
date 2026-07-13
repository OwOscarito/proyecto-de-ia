from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import APP_DIR, BACKEND_PUBLIC_URL

router = APIRouter()
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@router.get("/")
async def index(request: Request, activada: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        conxtext={
            "backend_url": BACKEND_PUBLIC_URL,
            "camara_activada": activada == "1",
        },
    )
