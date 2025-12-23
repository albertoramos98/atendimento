from fastapi import FastAPI, Request, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import time

from auth import hash_senha
from models import Cliente, Mesa



from database import SessionLocal, engine
from models import Base
from auth import autenticar_cliente

# ========================
# APP
# ========================
app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="troque-essa-chave-em-producao"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========================
# BANCO
# ========================
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# ESTADO DAS MESAS (por cliente)
# ========================
mesas = {}

def get_mesas_cliente(cliente_id: int):
    if cliente_id not in mesas:
        mesas[cliente_id] = {
            1: {"status": "livre", "tipo": None, "timestamp": None},
            2: {"status": "livre", "tipo": None, "timestamp": None},
            3: {"status": "livre", "tipo": None, "timestamp": None},
        }
    return mesas[cliente_id]

# ========================
# WEBSOCKET MANAGER
# ========================
class ConnectionManager:
    def __init__(self):
        self.connections = {}  # cliente_id -> [websockets]

    async def connect(self, cliente_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(cliente_id, []).append(websocket)

    def disconnect(self, cliente_id: int, websocket: WebSocket):
        self.connections[cliente_id].remove(websocket)

    async def send_to_cliente(self, cliente_id: int, data: dict):
        for ws in self.connections.get(cliente_id, []):
            await ws.send_json(data)

manager = ConnectionManager()

# ========================
# LOGIN
# ========================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    cliente = autenticar_cliente(db, email, senha)
    if not cliente:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "erro": "Email ou senha inválidos"}
        )

    request.session["cliente_id"] = cliente.id
    return RedirectResponse("/", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ========================
# DASHBOARD
# ========================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return RedirectResponse("/login", status_code=302)

    # 🔽 AQUI ENTRA O CÓDIGO QUE VOCÊ PERGUNTOU
    mesas_db = db.query(Mesa).filter(Mesa.cliente_id == cliente_id).all()

    mesas_view = {
        mesa.numero: {
            "status": mesa.status,
            "tipo": mesa.tipo,
            "timestamp": mesa.timestamp,
            "id": mesa.id
        }
        for mesa in mesas_db
    }

    return templates.TemplateResponse(
        "painel.html",
        {
            "request": request,
            "mesas": mesas_view
        }
    )

# ========================
# WEBSOCKET
# ========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 🔐 sessão vem no cookie automaticamente
    session = websocket.scope.get("session")
    cliente_id = session.get("cliente_id") if session else None

    if not cliente_id:
        await websocket.close()
        return

    await manager.connect(cliente_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(cliente_id, websocket)

# ========================
# MESA (QR)
# ========================
@app.post("/c/{cliente_id}/mesa/{mesa_id}/chamar")
async def chamar_mesa(
    cliente_id: int,
    mesa_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    mesa = db.query(Mesa).filter(
        Mesa.id == mesa_id,
        Mesa.cliente_id == cliente_id
    ).first()

    if not mesa or mesa.status == "chamando":
        return {"ok": False}

    mesa.status = "chamando"
    mesa.tipo = payload.get("tipo")
    mesa.timestamp = time.time()

    db.commit()

    # 🔔 AVISA O PAINEL CORRETO
    await manager.send_to_cliente(cliente_id, {
        "id": mesa.id,
        "status": mesa.status,
        "tipo": mesa.tipo,
        "timestamp": mesa.timestamp
    })

    return {"ok": True}


@app.get("/c/{cliente_id}/mesa/{mesa_id}", response_class=HTMLResponse)
async def mesa_page(
    request: Request,
    cliente_id: int,
    mesa_id: int,
    db: Session = Depends(get_db)
):
    mesa = db.query(Mesa).filter(
        Mesa.id == mesa_id,
        Mesa.cliente_id == cliente_id
    ).first()

    if not mesa:
        return HTMLResponse("Mesa não encontrada", status_code=404)

    return templates.TemplateResponse(
        "mesa.html",
        {
            "request": request,
            "mesa": mesa.numero,
            "cliente_id": cliente_id,
            "mesa_id": mesa_id
        }
    )


# ========================
# CHAMADAS
# ========================
@app.post("/chamar/{mesa_id}")
async def chamar_mesa(mesa_id: int, request: Request, payload: dict):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return {"ok": False}

    mesas_cliente = get_mesas_cliente(cliente_id)

    if mesas_cliente[mesa_id]["status"] == "chamando":
        return {"ok": False}

    mesas_cliente[mesa_id] = {
        "status": "chamando",
        "tipo": payload.get("tipo"),
        "timestamp": time.time()
    }

    await manager.send_to_cliente(cliente_id, {
        "mesa": mesa_id,
        "status": "chamando",
        "tipo": payload.get("tipo"),
        "timestamp": mesas_cliente[mesa_id]["timestamp"]
    })

    return {"ok": True}

@app.post("/c/{cliente_id}/mesa/{mesa_id}/atendido")
async def atender_mesa(
    cliente_id: int,
    mesa_id: int,
    db: Session = Depends(get_db)
):
    mesa = db.query(Mesa).filter(
        Mesa.id == mesa_id,
        Mesa.cliente_id == cliente_id
    ).first()

    if not mesa:
        return {"ok": False}

    mesa.status = "livre"
    mesa.tipo = None
    mesa.timestamp = None

    db.commit()

    await manager.send_to_cliente(cliente_id, {
        "mesa": mesa.numero,
        "status": "livre",
        "tipo": None,
        "timestamp": None
    })

    return {"ok": True}

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )

@app.post("/register")
async def register(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    existe = db.query(Cliente).filter(Cliente.email == email).first()
    if existe:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "erro": "Email já cadastrado"}
        )

    novo_cliente = Cliente(
        nome=nome,
        email=email,
        senha=hash_senha(senha)
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    # 🔥 cria mesas padrão (ex: 3 mesas)
    for numero in range(1, 4):
        mesa = Mesa(
            numero=numero,
            cliente_id=novo_cliente.id
        )
        db.add(mesa)

    db.commit()

    return RedirectResponse("/login", status_code=302)

@app.post("/mesas/criar")
async def criar_mesa(
    request: Request,
    numero: int = Form(...),
    db: Session = Depends(get_db)
):
    cliente_id = request.session.get("cliente_id")

    mesa = Mesa(numero=numero, cliente_id=cliente_id)
    db.add(mesa)
    db.commit()

    return RedirectResponse("/", status_code=302)

@app.post("/mesas/{mesa_id}/remover")
async def remover_mesa(
    mesa_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    cliente_id = request.session.get("cliente_id")

    mesa = db.query(Mesa).filter(
        Mesa.id == mesa_id,
        Mesa.cliente_id == cliente_id
    ).first()

    if mesa:
        db.delete(mesa)
        db.commit()

    return RedirectResponse("/", status_code=302)

from fastapi.responses import StreamingResponse
import io
import zipfile
import qrcode

@app.post("/qrcodes/baixar")
async def baixar_qrcodes(
    request: Request,
    db: Session = Depends(get_db)
):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return RedirectResponse("/login", status_code=302)

    mesas = db.query(Mesa).filter(Mesa.cliente_id == cliente_id).all()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for mesa in mesas:
            url = f"https://atendimento-pf79.onrender.com/c/{cliente_id}/mesa/{mesa.id}"

            img = qrcode.make(url)
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            nome_arquivo = f"mesa_{mesa.numero}.png"
            zip_file.writestr(nome_arquivo, img_buffer.read())

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=qrcodes_mesas.zip"
        }
    )
