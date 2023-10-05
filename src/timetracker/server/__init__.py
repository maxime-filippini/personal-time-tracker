import uvicorn


def run(port: int):
    uvicorn.run(app="timetracker.server.main:app", port=port, reload=True)
