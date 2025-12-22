import qrcode
import os

BASE_URL = "http://localhost:8000/mesa"
TOTAL_MESAS = 4

os.makedirs("qrcodes", exist_ok=True)

for mesa in range(1, TOTAL_MESAS + 1):
    url = f"{BASE_URL}/{mesa}"
    img = qrcode.make(url)
    img.save(f"qrcodes/mesa_{mesa}.png")

print("QR Codes gerados com sucesso!")
