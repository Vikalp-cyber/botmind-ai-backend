from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Public. Returns `{ \"status\": \"ok\" }` when the process is up.",
)
async def healthcheck():
    return {"status": "ok"}
