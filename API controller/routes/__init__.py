from fastapi import APIRouter
from routes.fmus import fmus
from routes.schemas import schemas
from routes.simulations import simulations
from loguru import logger


try:

    BaseRouter = APIRouter(prefix='/fmi', tags=['fmi'])

    BaseRouter.include_router(fmus)
    BaseRouter.include_router(schemas)
    BaseRouter.include_router(simulations)

except asyncpg.exceptions.UniqueViolationError as e:
    logger.error(e)