from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect



app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# estado simples das mesas
import time

mesas = {
    1: {"status": "livre", "timestamp": None},
    2: {"status": "livre", "timestamp": None},
    3: {"status": "livre", "timestamp": None},
    4: {"status": "livre", "timestamp": None},
}


# conexões websocket do painel
connections = []




@app.get("/mesa/{mesa_id}", response_class=HTMLResponse)
async def mesa_page(request: Request, mesa_id: int):
    return templates.TemplateResponse(
        "mesa.html",
        {"request": request, "mesa": mesa_id}
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "painel.html",
        {"request": request, "mesas": mesas}
    )



@app.post("/chamar/{mesa_id}")
async def chamar_mesa(mesa_id: int):
    mesas[mesa_id]["status"] = "chamando"
    mesas[mesa_id]["timestamp"] = time.time()

    for ws in connections:
        await ws.send_json({
            "mesa": mesa_id,
            "status": "chamando",
            "timestamp": mesas[mesa_id]["timestamp"]
        })

    return {"ok": True}



@app.post("/atendido/{mesa_id}")
async def atender_mesa(mesa_id: int):
    mesas[mesa_id]["status"] = "livre"
    mesas[mesa_id]["timestamp"] = None

    for ws in connections:
        await ws.send_json({
            "mesa": mesa_id,
            "status": "livre",
            "timestamp": None
        })

    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)
    except:
        connections.remove(websocket)
