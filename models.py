from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)

    mesas = relationship("Mesa", back_populates="cliente")


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))

    status = Column(String, default="livre")      # livre | chamando
    tipo = Column(String, nullable=True)           # garcom | conta
    timestamp = Column(Float, nullable=True)       # time.time()

    cliente = relationship("Cliente", back_populates="mesas")
