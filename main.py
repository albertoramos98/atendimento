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
    1: {"status": "livre", "tipo": None, "timestamp": None},
    2: {"status": "livre", "tipo": None, "timestamp": None},
    3: {"status": "livre", "tipo": None, "timestamp": None},
    4: {"status": "livre", "tipo": None, "timestamp": None},
    5: {"status": "livre", "tipo": None, "timestamp": None},
    6: {"status": "livre", "tipo": None, "timestamp": None},
    7: {"status": "livre", "tipo": None, "timestamp": None},
    8: {"status": "livre", "tipo": None, "timestamp": None},
    9: {"status": "livre", "tipo": None, "timestamp": None},
    10: {"status": "livre", "tipo": None, "timestamp": None},
    11: {"status": "livre", "tipo": None, "timestamp": None},
    12: {"status": "livre", "tipo": None, "timestamp": None},
    13: {"status": "livre", "tipo": None, "timestamp": None},
    14: {"status": "livre", "tipo": None, "timestamp": None},
    15: {"status": "livre", "tipo": None, "timestamp": None},
    16: {"status": "livre", "tipo": None, "timestamp": None},
    17: {"status": "livre", "tipo": None, "timestamp": None},
    18: {"status": "livre", "tipo": None, "timestamp": None},
    19: {"status": "livre", "tipo": None, "timestamp": None},
    20: {"status": "livre", "tipo": None, "timestamp": None},
    21: {"status": "livre", "tipo": None, "timestamp": None},
    22: {"status": "livre", "tipo": None, "timestamp": None},
    23: {"status": "livre", "tipo": None, "timestamp": None},
    4: {"status": "livre", "tipo": None, "timestamp": None},
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



import time
from fastapi import Body

@app.post("/chamar/{mesa_id}")
async def chamar_mesa(mesa_id: int, payload: dict = Body(...)):
    tipo = payload.get("tipo")  # "garcom" ou "conta"

    # evita spam
    if mesas[mesa_id]["status"] == "chamando":
        return {"ok": False, "message": "Já solicitado"}

    mesas[mesa_id] = {
        "status": "chamando",
        "tipo": tipo,
        "timestamp": time.time()
    }

    for ws in connections:
        await ws.send_json({
            "mesa": mesa_id,
            "status": "chamando",
            "tipo": tipo,
            "timestamp": mesas[mesa_id]["timestamp"]
        })

    return {"ok": True}


@app.post("/atendido/{mesa_id}")
async def atender_mesa(mesa_id: int):
    mesas[mesa_id] = {
        "status": "livre",
        "tipo": None,
        "timestamp": None
    }

    for ws in connections:
        await ws.send_json({
            "mesa": mesa_id,
            "status": "livre",
            "tipo": None,
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
