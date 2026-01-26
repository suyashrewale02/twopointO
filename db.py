import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Text, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Connection(Base):
    __tablename__ = "connections"

    connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_text = Column(Text, unique=True, nullable=False)
    definition = Column(Text, nullable=True)
    type = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Path(Base):
    __tablename__ = "paths"

    path_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_connection = Column(UUID(as_uuid=True), ForeignKey("connections.connection_id"), nullable=False)
    to_connection = Column(UUID(as_uuid=True), ForeignKey("connections.connection_id"), nullable=False)
    relation_type = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    from_node = relationship("Connection", foreign_keys=[from_connection])
    to_node = relationship("Connection", foreign_keys=[to_connection])


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
