from fastapi import APIRouter
from . import upload, categories, results

router = APIRouter(prefix="/api", tags=["products"])
router.include_router(upload.router)
router.include_router(categories.router)
router.include_router(results.router)
