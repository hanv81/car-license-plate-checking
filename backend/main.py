import uvicorn
from fastapi import FastAPI
from router import user_controller, system_controller

app = FastAPI()
app.include_router(user_controller.user_router)
app.include_router(system_controller.system_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)