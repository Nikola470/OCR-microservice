import pathlib
from functools import lru_cache
from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile
)
import pytesseract
import io
import uuid
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings
from PIL import Image


class Settings(BaseSettings):
    app_auth_token: str
    debug: bool = False
    echo_active: bool = False
    app_auth_token_prod: str = None
    skip_auth: bool = False

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
DEBUG = settings.debug

print(settings)

BASE_DIR = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def verify_auth(authorization=Header(None), settings: Settings = Depends(get_settings)):
    """
    :param authorization: Bearer <token>
    :param settings:
    :return:
    """

    if settings.debug and settings.skip_auth:
        return
    if authorization is None:
        raise HTTPException(detail="Invalid endpoint", status_code=401)
    label, token = authorization.split()
    if token != settings.app_auth_token:
        raise HTTPException(detail="Invalid endpoint", status_code=401)


@app.get("/", response_class=HTMLResponse)
def home_view(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/")
async def prediction_view(file: UploadFile = File(...), authorization = Header(None)):
    """
    :param file:
    :param authorization:
    :return:
    """
    verify_auth(authorization, settings)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original": preds}


@app.post("/img-echo/", response_class=FileResponse)
async def img_echo_view(file: UploadFile = File(...),
                        settings: Settings = Depends(get_settings)):
    if not settings.echo_active:
        raise HTTPException(detail="Invalid endpoint", status_code=400)
    UPLOAD_DIR.mkdir(exist_ok=True)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    file_name = pathlib.Path(file.filename)
    file_extension = file_name.suffix  # .jpeg, .txt
    dest = UPLOAD_DIR / f"{uuid.uuid1()}{file_extension}"
    img.save(dest)
    return dest
