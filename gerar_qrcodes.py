import qrcode
import os
from database import SessionLocal
from models import Mesa

# 🔧 CONFIGURAÇÃO
BASE_URL = f"https://atendimento-pf79.onrender.com/c/{cliente_id}/mesa/{mesa.id}"  
PASTA_QR = "qrcodes"

os.makedirs(PASTA_QR, exist_ok=True)

db = SessionLocal()

mesas = db.query(Mesa).all()

for mesa in mesas:
    url = f"{BASE_URL}/c/{mesa.cliente_id}/mesa/{mesa.id}"

    img = qrcode.make(url)

    nome_arquivo = f"cliente_{mesa.cliente_id}_mesa_{mesa.numero}.png"
    caminho = os.path.join(PASTA_QR, nome_arquivo)

    img.save(caminho)

    print(f"QR gerado: {caminho} → {url}")

db.close()
