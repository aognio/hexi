from fastapi import FastAPI

app = FastAPI(title="sample-fastapi-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
