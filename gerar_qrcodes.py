import qrcode
import os

BASE_URL = "https://atendimento-pf79.onrender.com/mesa"
TOTAL_MESAS = 4  # muda depois se quiser mais mesas

os.makedirs("qrcodes", exist_ok=True)

for mesa in range(1, TOTAL_MESAS + 1):
    url = f"{BASE_URL}/{mesa}"
    img = qrcode.make(url)
    img.save(f"qrcodes/mesa_{mesa}.png")

print("QR Code gerado com sucesso!")
