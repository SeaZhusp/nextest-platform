from fastapi import APIRouter

from app.schemas.common import ApiResponse, HealthData

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthData])
def health_check() -> ApiResponse[HealthData]:
    return ApiResponse(data=HealthData())
