import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Node(Base):
    __tablename__ = "node_table"
    
    id = Column(Integer, primary_key=True)
    label = Column(String)
    node_type = Column(String)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, default=func.now())
    use_count = Column(Integer, default=1)

class Connection(Base):
    __tablename__ = "connections_table"
    
    id = Column(Integer, primary_key=True)
    from_node_id = Column(Integer)
    to_node_id = Column(Integer)
    relation_strength = Column(Float, default=0.1)
    use_count = Column(Integer, default=1)
    last_used_at = Column(DateTime, default=func.now())

def get_session():
    """Create database session."""
    return SessionLocal()
