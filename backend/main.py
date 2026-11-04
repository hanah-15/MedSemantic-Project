from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.conditions import router as conditions_router
from app.routes.patients import router as patients_router
from app.routes.medicaments import router as medicaments_router
from app.routes.recherche import router as recherche_router

app = FastAPI(title="MedSemantic API", version="1.0.0")

# Local Vite dev servers. No cookies or private clinical datasets are used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173', 'http://localhost:5174',
        'http://127.0.0.1:5173', 'http://127.0.0.1:5174',
    ],
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*'],
)

app.include_router(patients_router)
app.include_router(conditions_router)
app.include_router(medicaments_router)
app.include_router(recherche_router)


@app.get('/')
def read_root():
    return {'status': 'success', 'message': 'API MedSemantic opérationnelle'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
