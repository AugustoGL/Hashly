from fastapi import FastAPI

from database.database import Base, engine
from database import models

from users.routes import router as users_router

from packages.routes import router as packages_router

# Crear las tablas de la base de datos
Base.metadata.create_all(bind=engine)


app = FastAPI()

app.include_router(users_router)
app.include_router(packages_router)