from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.etudes import router as etudes_router
from app.routes.resultats import router as resultats_router

app = FastAPI(title="MedSemantic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(etudes_router)
app.include_router(resultats_router)


@app.get("/")
def read_root():
    return {"status": "success", "message": "API MedSemantic opérationnelle"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
