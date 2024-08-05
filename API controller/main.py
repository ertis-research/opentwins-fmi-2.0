from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from errors import DatabaseError
from routes import BaseRouter


__name__ = "OpenTwins FMI simulator 2.0"
__name__ = "0.1.0"

app = FastAPI()
app.include_router(BaseRouter)


#TODO: Poner aqui todos los errores. El altair es el mas meho
# Mirar también el heredar de HTTPException

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