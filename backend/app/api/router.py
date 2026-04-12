from fastapi import APIRouter

from app.api.endpoints import admin_skills, agent, auth, health, skill_plaza, skills, user_llm_profiles, users

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router)
router.include_router(user_llm_profiles.router)
router.include_router(agent.router)
router.include_router(skills.router)
router.include_router(skill_plaza.router)
router.include_router(admin_skills.router)
