from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from errors import DatabaseError, SchemaNotFoundError, SimulationError, SimulationAlreadyExistsError, DeleteSimulationError, FMUError
from dependencies import get_sql_client
from routes import BaseRouter


__name__ = "OpenTwins FMI simulator 2.0"
__name__ = "0.1.0"

app = FastAPI()
app.include_router(BaseRouter)


@app.on_event("startup")
async def create_schema_table():
    """ Create the (SQLite-backed) table that stores simulation schemas if it doesn't exist yet -
        there's no separate migration step to run before deploying the API. """
    engine = get_sql_client()
    async with engine.begin() as connection:
        await connection.execute(text("""
            CREATE TABLE IF NOT EXISTS fmi_sim_schemmas (
                id          VARCHAR NOT NULL,
                context     VARCHAR NOT NULL,
                name        VARCHAR,
                sim_schemme TEXT,
                PRIMARY KEY (id, context)
            )
        """))
    await engine.dispose()


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Centralized error handling: any of these exceptions raised from a route/service is turned into a
# proper JSON response instead of propagating as an unhandled 500. Handlers for the more specific
# exceptions are registered so they take precedence over their base class (e.g. SchemaNotFoundError
# over DatabaseError, SimulationAlreadyExistsError over SimulationError).

@app.exception_handler(SchemaNotFoundError)
async def schema_not_found_handler(request: Request, exc: SchemaNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(SimulationAlreadyExistsError)
async def simulation_already_exists_handler(request: Request, exc: SimulationAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(DeleteSimulationError)
async def delete_simulation_error_handler(request: Request, exc: DeleteSimulationError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(SimulationError)
async def simulation_error_handler(request: Request, exc: SimulationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(FMUError)
async def fmu_error_handler(request: Request, exc: FMUError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="OpenTwins FMI simulator 2.0",
        version="0.1.0",
        description="This is the OpenTwins FMI simulator 2.0 API",
        routes=app.routes,
    )
    openapi_schema["servers"] = [
        {"url": "/", "description": "Default"},
        {"url": "https//localhost:8000", "description": "Localhost"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi