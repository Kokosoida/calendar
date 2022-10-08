from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func

from app.db import Base


class EventInvite(Base):
    __tablename__ = "event_invite"
    event_id = Column(ForeignKey("event.id"), primary_key=True)
    user_id = Column(GUID, ForeignKey("users.id"), primary_key=True)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    is_accepted = Column(Boolean, nullable=True, default=None)

    event = relationship("Event", back_populates="invites")
    user = relationship("User", back_populates="invites")
