from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import Cliente

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_senha(senha: str):
    return pwd_context.hash(senha)

def verificar_senha(senha: str, senha_hash: str):
    return pwd_context.verify(senha, senha_hash)

def autenticar_cliente(db: Session, email: str, senha: str):
    cliente = db.query(Cliente).filter(Cliente.email == email).first()
    if not cliente:
        return None
    if not verificar_senha(senha, cliente.senha):
        return None
    return cliente
