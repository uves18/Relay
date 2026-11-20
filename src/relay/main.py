from fastapi import FastAPI
from relay.api.routes import health
from relay.api.routes import jobs

app=FastAPI(title="Relay")
app.include_router(health.router)
app.include_router(jobs.router, prefix='/api/v1')
