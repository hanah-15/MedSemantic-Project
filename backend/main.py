from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import medicaments
from app.routes import recherche

app = FastAPI(title="MedSemantic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement de tes routes (Hana)
app.include_router(medicaments.router)
app.include_router(recherche.router)

@app.get("/")
def read_root():
    return {"status": "success", "message": "API MedSemantic opérationnelle"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)