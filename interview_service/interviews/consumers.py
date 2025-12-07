"""
WebSocket consumers for real-time interview functionality.
This is a basic placeholder for Phase 1. Full implementation in Phase 4.
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .authentication import WebSocketJWTAuthentication
from .models import LiveInterviewSession
import logging

logger = logging.getLogger(__name__)


class InterviewConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time live interview sessions.

    Handles:
    - Real-time audio streaming
    - Live transcription
    - AI feedback delivery (to interviewer)
    - Question updates
    - Session lifecycle events

    Full implementation will be added in Phase 4.
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        Authenticate user and join interview room.
        """
        # Get session ID from URL
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'interview_{self.session_id}'

        # Authenticate user via JWT token in query params
        self.user = await WebSocketJWTAuthentication.authenticate_websocket(self.scope)

        if not self.user:
            logger.warning(f"WebSocket connection rejected: authentication failed for session {self.session_id}")
            await self.close(code=4001)
            return

        # Verify user has access to this interview session
        has_access = await self.verify_session_access()
        if not has_access:
            logger.warning(f"WebSocket connection rejected: user {self.user.id} has no access to session {self.session_id}")
            await self.close(code=4003)
            return

        # Accept connection
        await self.accept()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Send connection confirmation
        await self.send_json({
            'type': 'connection.established',
            'data': {
                'session_id': str(self.session_id),
                'user_id': str(self.user.id),
                'user_role': self.user.role,
            }
        })

        logger.info(f"WebSocket connected: user {self.user.id} joined interview {self.session_id}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Leave interview room.
        """
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        logger.info(f"WebSocket disconnected: close_code={close_code}, session={self.session_id if hasattr(self, 'session_id') else 'unknown'}")

    async def receive_json(self, content):
        """
        Receive message from WebSocket.
        Route to appropriate handler based on message type.

        Phase 4 will implement handlers for:
        - audio.chunk
        - question.ask
        - answer.submit
        - session.control (start, end, pause)
        """
        message_type = content.get('type')

        logger.debug(f"Received WebSocket message: type={message_type}, session={self.session_id}")

        # Placeholder: echo back for now
        await self.send_json({
            'type': 'message.received',
            'data': {
                'original_type': message_type,
                'message': 'Message received. Full handlers will be implemented in Phase 4.'
            }
        })

    @database_sync_to_async
    def verify_session_access(self):
        """
        Verify that the authenticated user has access to the interview session.

        Returns:
            bool: True if user is interviewer or candidate for this session
        """
        try:
            session = LiveInterviewSession.objects.get(id=self.session_id)
            return session.interviewer == self.user or session.candidate == self.user
        except LiveInterviewSession.DoesNotExist:
            return False

    # Channel layer event handlers (for broadcasting)
    async def interview_update(self, event):
        """
        Handler for interview.update events from channel layer.
        Broadcasts interview updates to all participants.
        """
        await self.send_json(event['data'])

    async def question_asked(self, event):
        """
        Handler for question.asked events from channel layer.
        """
        await self.send_json(event['data'])

    async def feedback_realtime(self, event):
        """
        Handler for feedback.realtime events from channel layer.
        Only send to interviewer if feedback_visibility is 'interviewer_only'.
        """
        # Phase 4: Implement visibility filtering
        await self.send_json(event['data'])

    async def transcription_interim(self, event):
        """
        Handler for transcription.interim events from channel layer.
        """
        await self.send_json(event['data'])
