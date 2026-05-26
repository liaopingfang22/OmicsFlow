from fastapi import APIRouter
from api import auth, datasets, tasks, pipelines, skills, ai, sequencers, projects, results, public_data

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(datasets.router)
api_router.include_router(tasks.router)
api_router.include_router(pipelines.router)
api_router.include_router(skills.router)
api_router.include_router(ai.router)
api_router.include_router(sequencers.router)
api_router.include_router(projects.router)
api_router.include_router(results.router)
api_router.include_router(public_data.router)
