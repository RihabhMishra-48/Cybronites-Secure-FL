from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Node(Base):
    __tablename__ = "nodes"
    id = Column(String, primary_key=True, index=True) # UUID or specific ID
    name = Column(String)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    trust_score = Column(Float, default=100.0)

class Round(Base):
    __tablename__ = "rounds"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="IDLE") # IDLE, WAITING, AGGREGATING, COMPLETED
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    model_hash = Column(String, nullable=True)

class Update(Base):
    __tablename__ = "updates"
    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    node_id = Column(String, ForeignKey("nodes.id"))
    hash = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # ACCEPTED, REJECTED

class BlockDB(Base):
    __tablename__ = "blockchain"
    index = Column(Integer, primary_key=True)
    transactions = Column(JSON)
    timestamp = Column(Float)
    previous_hash = Column(String)
    hash = Column(String)
