from sqlalchemy import Column, Integer, String, Text
from app.db import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)

    hcp_name = Column(String(100))
    date = Column(String(20))
    time = Column(String(20))
    interaction_type = Column(String(50))
    topics = Column(Text)
    sentiment = Column(String(20))
    materials_shared = Column(Text)

    summary = Column(Text)
    follow_up = Column(Text)
    insight = Column(Text)
    priority = Column(String(20))