from fastapi import FastAPI


app = FastAPI(
    docs_url="/swagger"
)

@app.get("/")
async def root():
    return {"message": "Welcome"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }