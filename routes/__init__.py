from fastapi import APIRouter
from routes.fmus import fmus
from routes.simulations import simulations

BaseRouter = APIRouter()

BaseRouter.include_router(fmus)
BaseRouter.include_router(simulations)