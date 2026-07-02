from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="SHL Assessment Recommender API",
    description="Stateless Conversational Recommender API for SHL Individual Test Solutions",
    version="1.0.0"
)

# Include the main api router directly at the root level
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
