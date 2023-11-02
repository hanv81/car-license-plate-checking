import uvicorn
from fastapi import FastAPI
from router import user_controller, system_controller
from util import config

app = FastAPI()
app.include_router(user_controller.user_router)
app.include_router(system_controller.system_router)

if __name__ == "__main__":
    host, port, _ = config.read_env()
    uvicorn.run("main:app", host=host, port=port, reload=True)