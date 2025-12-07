"""
WebSocket URL routing for interview_service.
Maps WebSocket URLs to consumer classes.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Practice sessions WebSocket (solo AI practice)
    path('ws/practice-sessions/<uuid:session_id>/', consumers.PracticeSessionConsumer.as_asgi()),

    # Live interviews WebSocket (two-person interviews)
    path('ws/interviews/<uuid:session_id>/', consumers.InterviewConsumer.as_asgi()),
]
