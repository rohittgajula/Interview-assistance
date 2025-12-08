"""
Event schemas for Kafka messages.
Defines standardized event structures for cross-service communication.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass(kw_only=True)
class BaseEvent:
    """Base event class with common fields"""
    event_type: str
    timestamp: str
    service: str
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create event from dictionary"""
        return cls(**data)


# User Events

@dataclass(kw_only=True)
class UserCreatedEvent(BaseEvent):
    """Event published when a new user is created"""
    user_id: str
    username: str
    email: str
    role: str
    date_of_birth: Optional[str] = None  # ISO format date string
    age: Optional[int] = None
    is_active: bool = True
    event_type: str = "user.created"
    service: str = "auth_service"

    def __init__(self, user_id: str, username: str, email: str, role: str,
                 date_of_birth: Optional[str] = None, age: Optional[int] = None,
                 is_active: bool = True, timestamp: Optional[str] = None, **kwargs):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.date_of_birth = date_of_birth
        self.age = age
        self.is_active = is_active
        self.event_type = "user.created"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


@dataclass(kw_only=True)
class UserUpdatedEvent(BaseEvent):
    """Event published when a user is updated"""
    user_id: str
    date_of_birth: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    updated_fields: Optional[list] = None
    event_type: str = "user.updated"
    service: str = "auth_service"

    def __init__(self, user_id: str, username: Optional[str] = None,
                 email: Optional[str] = None, role: Optional[str] = None,
                 date_of_birth: Optional[str] = None,
                 updated_fields: Optional[list] = None,
                 timestamp: Optional[str] = None, **kwargs):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.date_of_birth = date_of_birth
        self.updated_fields = updated_fields or []
        self.event_type = "user.updated"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


@dataclass(kw_only=True)
class UserDeletedEvent(BaseEvent):
    """Event published when a user is deleted"""
    user_id: str
    username: str
    email: str
    event_type: str = "user.deleted"
    service: str = "auth_service"

    def __init__(self, user_id: str, username: str, email: str,
                 timestamp: Optional[str] = None, **kwargs):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.event_type = "user.deleted"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


@dataclass(kw_only=True)
class UserLoginEvent(BaseEvent):
    """Event published when a user logs in"""
    user_id: str
    username: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    event_type: str = "user.login"
    service: str = "auth_service"

    def __init__(self, user_id: str, username: str,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 timestamp: Optional[str] = None, **kwargs):
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.event_type = "user.login"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


# Organization Events

@dataclass(kw_only=True)
class OrganizationCreatedEvent(BaseEvent):
    """Event published when an organization is created"""
    organization_id: str
    name: str
    created_by: str
    event_type: str = "organization.created"
    service: str = "auth_service"

    def __init__(self, organization_id: str, name: str, created_by: str,
                 timestamp: Optional[str] = None, **kwargs):
        self.organization_id = organization_id
        self.name = name
        self.created_by = created_by
        self.event_type = "organization.created"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


@dataclass(kw_only=True)
class MemberAddedEvent(BaseEvent):
    """Event published when a member is added to an organization"""
    organization_id: str
    user_id: str
    role: str
    added_by: str
    event_type: str = "member.added"
    service: str = "auth_service"

    def __init__(self, organization_id: str, user_id: str, role: str,
                 added_by: str, timestamp: Optional[str] = None, **kwargs):
        self.organization_id = organization_id
        self.user_id = user_id
        self.role = role
        self.added_by = added_by
        self.event_type = "member.added"
        self.service = "auth_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


# Bloom Filter Events

@dataclass(kw_only=True)
class FilterRebuildStartedEvent(BaseEvent):
    """Event published when bloom filter rebuild starts"""
    rebuild_id: str
    filter_type: str  # 'username' or 'email'
    event_type: str = "filter.rebuild.started"
    service: str = "bloom_filter_service"

    def __init__(self, rebuild_id: str, filter_type: str,
                 timestamp: Optional[str] = None, **kwargs):
        self.rebuild_id = rebuild_id
        self.filter_type = filter_type
        self.event_type = "filter.rebuild.started"
        self.service = "bloom_filter_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


@dataclass(kw_only=True)
class FilterRebuildCompletedEvent(BaseEvent):
    """Event published when bloom filter rebuild completes"""
    rebuild_id: str
    filter_type: str
    items_added: int
    duration_seconds: float
    event_type: str = "filter.rebuild.completed"
    service: str = "bloom_filter_service"

    def __init__(self, rebuild_id: str, filter_type: str, items_added: int,
                 duration_seconds: float, timestamp: Optional[str] = None, **kwargs):
        self.rebuild_id = rebuild_id
        self.filter_type = filter_type
        self.items_added = items_added
        self.duration_seconds = duration_seconds
        self.event_type = "filter.rebuild.completed"
        self.service = "bloom_filter_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


# Interview Events (for future use)

@dataclass(kw_only=True)
class InterviewScheduledEvent(BaseEvent):
    """Event published when an interview is scheduled"""
    interview_id: str
    candidate_id: str
    interviewer_id: str
    scheduled_time: str
    event_type: str = "interview.scheduled"
    service: str = "interview_service"

    def __init__(self, interview_id: str, candidate_id: str, interviewer_id: str,
                 scheduled_time: str, timestamp: Optional[str] = None, **kwargs):
        self.interview_id = interview_id
        self.candidate_id = candidate_id
        self.interviewer_id = interviewer_id
        self.scheduled_time = scheduled_time
        self.event_type = "interview.scheduled"
        self.service = "interview_service"
        self.version = kwargs.get('version', "1.0")
        self.timestamp = timestamp or datetime.utcnow().isoformat()


# Event Serialization Utilities

def serialize_event(event: BaseEvent) -> bytes:
    """
    Serialize an event to bytes for Kafka.

    Args:
        event: Event instance to serialize

    Returns:
        bytes: JSON-encoded event
    """
    return event.to_json().encode('utf-8')


def deserialize_event(data: bytes, event_class: type = BaseEvent) -> BaseEvent:
    """
    Deserialize bytes from Kafka to an event.

    Args:
        data: JSON-encoded bytes
        event_class: Event class to instantiate

    Returns:
        BaseEvent: Deserialized event instance
    """
    json_data = json.loads(data.decode('utf-8'))
    return event_class.from_dict(json_data)


# Event type to class mapping
EVENT_TYPE_MAPPING = {
    "user.created": UserCreatedEvent,
    "user.updated": UserUpdatedEvent,
    "user.deleted": UserDeletedEvent,
    "user.login": UserLoginEvent,
    "organization.created": OrganizationCreatedEvent,
    "member.added": MemberAddedEvent,
    "filter.rebuild.started": FilterRebuildStartedEvent,
    "filter.rebuild.completed": FilterRebuildCompletedEvent,
    "interview.scheduled": InterviewScheduledEvent,
}


def deserialize_event_auto(data: bytes) -> BaseEvent:
    """
    Automatically deserialize event based on event_type field.

    Args:
        data: JSON-encoded bytes

    Returns:
        BaseEvent: Deserialized event instance of the correct type
    """
    json_data = json.loads(data.decode('utf-8'))
    event_type = json_data.get('event_type')
    event_class = EVENT_TYPE_MAPPING.get(event_type, BaseEvent)
    return event_class.from_dict(json_data)
