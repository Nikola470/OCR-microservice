import shutil
import time
from app.main import app, BASE_DIR, UPLOAD_DIR
from fastapi.testclient import TestClient
from PIL import Image, ImageChops
import io

client = TestClient(app)


def test_get_home():
    response = client.get("/")
    assert response.text != "<h1>test</h1>"
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']


def test_post_home():
    response = client.post("/")
    assert response.status_code == 200
    assert "application/json" in response.headers['content-type']


def test_img_upload_echo():
    img_saved_path = BASE_DIR / "images"
    for path in img_saved_path.glob("*"):
        try:
            img = Image.open(path)
        except:
            img = None
        response = client.post("/img-echo/", files={"file": open(path, 'rb')})
        if img is None:
            assert response.status_code == 400
        else:
            # Returning a valid image
            assert response.status_code == 200
            response_stream = io.BytesIO(response.content)
            echo_img = Image.open(response_stream)
            difference = ImageChops.difference(echo_img, img).getbbox()
            assert difference is None

    # time.sleep(3)
    shutil.rmtree(UPLOAD_DIR)
