# ABOUTME: Test fixture — FastAPI app and APIRouter decorated endpoints
# ABOUTME: Exercises the fastapi-routes rule: get/post with kwargs, router prefix

from fastapi import APIRouter, FastAPI

app = FastAPI()
router = APIRouter(prefix="/items")


@app.get("/health")
def health():
    return {"ok": True}


@router.post("/", response_model=dict)
def create_item(item: dict):
    return item
