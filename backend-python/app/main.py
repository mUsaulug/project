from fastapi import FastAPI, Request
import uuid
from app.api.routes import router as api_router
from app.core.logging import configure_logging, request_id_var

# Initialize FastAPI app
app = FastAPI(title="ComplaintOps AI Service", version="0.1.0")

configure_logging()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/")
def read_root():
    return {"message": "ComplaintOps AI Service is running"}

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
