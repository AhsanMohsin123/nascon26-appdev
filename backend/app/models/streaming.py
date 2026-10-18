from sqlalchemy import Column, String, Integer, Text, Boolean
from app.database import Base


class StreamKey(Base):
    __tablename__ = "stream_keys"
    player_id = Column(String(64), primary_key=True)
    label = Column(String(64))
    stream_key = Column(String(64))
    status = Column(String(16))  # active | revoked


class CostreamSession(Base):
    __tablename__ = "costream_sessions"
    session_id = Column(String(64), primary_key=True)
    host_player_id = Column(String(64))
    active_host = Column(String(64))
    participants = Column(Text)  # json list — original requested participants
    active_participants = Column(Text)  # json list — current active roster
    layout = Column(String(16))
    status = Column(String(16))
    handoff_occurred = Column(Boolean, default=False)
    chat_room_id = Column(String(64))


class QRMapping(Base):
    __tablename__ = "qr_mappings"
    entity_id = Column(String(64), primary_key=True)
    entity_type = Column(String(16))
    short_code = Column(String(64), unique=True)
    scan_count = Column(Integer, default=0)


class QRScanTelemetry(Base):
    """Privacy-safe aggregate scan counters — no IP, User-Agent string, or fingerprint stored (NFR-9)."""
    __tablename__ = "qr_scan_telemetry"
    entity_id = Column(String(64), primary_key=True)
    device_family = Column(String(16), primary_key=True)  # "mobile" | "desktop"
    hour_bucket = Column(String(16), primary_key=True)  # UTC "YYYY-MM-DDTHH"
    count = Column(Integer, default=0)


class GuestToken(Base):
    __tablename__ = "guest_tokens"
    token = Column(String(64), primary_key=True)
    status = Column(String(16), default="valid")  # valid | merged
    merged_user_id = Column(String(64), nullable=True)
    merged_cart_signature = Column(Text, nullable=True)  # canonical(guest_cart) at merge time, for replay detection


class Cart(Base):
    __tablename__ = "carts"
    user_id = Column(String(64), primary_key=True)
    currency = Column(String(8), default="PKR")


class CartItem(Base):
    __tablename__ = "cart_items"
    user_id = Column(String(64), primary_key=True)
    variant_id = Column(String(64), primary_key=True)
    quantity = Column(Integer, default=0)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String(64), primary_key=True)
    chat_room_id = Column(String(64), index=True)
    sender = Column(String(64))
    text = Column(Text)
    flagged = Column(Boolean, default=False)
    reason = Column(String(32), nullable=True)


class ModerationAction(Base):
    __tablename__ = "moderation_actions"
    chat_room_id = Column(String(64), primary_key=True)
    kicked_users = Column(Text, default="[]")  # json list
    muted_users = Column(Text, default="[]")  # json list


class DLQEvent(Base):
    __tablename__ = "dlq_events"
    id = Column(String(64), primary_key=True)
    event_type = Column(String(32))
    payload = Column(Text)
