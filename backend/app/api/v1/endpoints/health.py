from fastapi import APIRouter, Request

from app.schemas.common import ApiResponse, HealthData

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthData])
def health_check(request: Request) -> ApiResponse[HealthData]:
    return ApiResponse(
        data=HealthData(),
        request_id=getattr(request.state, "request_id", None),
    )
