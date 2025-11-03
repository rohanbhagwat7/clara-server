"""
LiveKit service for token generation and room management
"""
import os
from typing import Optional, Dict, List
from datetime import timedelta
from livekit import api
import uuid


def parse_ttl(ttl_str: str) -> timedelta:
    """Parse TTL string like '10m', '1h', '24h' to timedelta"""
    ttl_str = ttl_str.strip()
    if ttl_str.endswith('m'):
        return timedelta(minutes=int(ttl_str[:-1]))
    elif ttl_str.endswith('h'):
        return timedelta(hours=int(ttl_str[:-1]))
    elif ttl_str.endswith('d'):
        return timedelta(days=int(ttl_str[:-1]))
    elif ttl_str.endswith('s'):
        return timedelta(seconds=int(ttl_str[:-1]))
    else:
        # Default to minutes if no unit specified
        return timedelta(minutes=int(ttl_str))


class LiveKitService:
    """Service for LiveKit operations"""

    def __init__(self, url: str, api_key: str, api_secret: str):
        """Initialize LiveKit service"""
        self.url = url
        self.api_key = api_key
        self.api_secret = api_secret

        print(f"LiveKit service initialized: {url}")

    def create_token(
        self,
        room_name: str,
        participant_name: str,
        participant_identity: Optional[str] = None,
        participant_metadata: Optional[str] = None,
        participant_attributes: Optional[Dict[str, str]] = None,
        permissions: Optional[Dict] = None,
        ttl: str = "10m",
    ) -> str:
        """Create LiveKit access token"""
        identity = participant_identity or participant_name

        # Parse TTL string to timedelta
        ttl_delta = parse_ttl(ttl)

        # Create token
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_identity(identity).with_name(participant_name).with_ttl(ttl_delta)

        # Set grants
        grants = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=permissions.get("canPublish", True) if permissions else True,
            can_publish_data=permissions.get("canPublishData", True) if permissions else True,
            can_subscribe=permissions.get("canSubscribe", True) if permissions else True,
            can_update_own_metadata=permissions.get("canUpdateOwnMetadata", True) if permissions else True,
        )

        if permissions:
            if permissions.get("hidden") is not None:
                grants.hidden = permissions["hidden"]
            if permissions.get("recorder") is not None:
                grants.recorder = permissions["recorder"]
            if permissions.get("roomAdmin") is not None:
                grants.room_admin = permissions["roomAdmin"]
            if permissions.get("roomCreate") is not None:
                grants.room_create = permissions["roomCreate"]
            if permissions.get("roomList") is not None:
                grants.room_list = permissions["roomList"]
            if permissions.get("roomRecord") is not None:
                grants.room_record = permissions["roomRecord"]

        token.with_grants(grants)

        if participant_metadata:
            token.with_metadata(participant_metadata)
        if participant_attributes:
            token.with_attributes(participant_attributes)

        return token.to_jwt()

    async def create_room(
        self,
        name: Optional[str] = None,
        empty_timeout: int = 300,
        max_participants: int = 100,
        metadata: str = "",
    ) -> Dict:
        """Create a LiveKit room"""
        room_name = name or f"room-{uuid.uuid4()}"

        room_service = api.RoomService(self.url, self.api_key, self.api_secret)

        room = await room_service.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=empty_timeout,
                max_participants=max_participants,
                metadata=metadata,
            )
        )

        return {
            "sid": room.sid,
            "name": room.name,
            "emptyTimeout": room.empty_timeout,
            "maxParticipants": room.max_participants,
            "creationTime": room.creation_time,
            "metadata": room.metadata,
            "numParticipants": room.num_participants,
        }

    async def list_rooms(self) -> List[Dict]:
        """List all active rooms"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        rooms = await room_service.list_rooms(api.ListRoomsRequest())

        return [
            {
                "sid": room.sid,
                "name": room.name,
                "emptyTimeout": room.empty_timeout,
                "maxParticipants": room.max_participants,
                "creationTime": room.creation_time,
                "numParticipants": room.num_participants,
                "metadata": room.metadata,
            }
            for room in rooms
        ]

    async def get_room(self, room_name: str) -> Dict:
        """Get room details with participants"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        participants = await room_service.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )

        return {
            "room": room_name,
            "numParticipants": len(participants),
            "participants": [
                {
                    "sid": p.sid,
                    "identity": p.identity,
                    "name": p.name,
                    "state": str(p.state),
                    "metadata": p.metadata,
                    "joinedAt": p.joined_at,
                }
                for p in participants
            ],
        }

    async def delete_room(self, room_name: str) -> Dict:
        """Delete a room"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        await room_service.delete_room(api.DeleteRoomRequest(room=room_name))
        return {"message": f"Room {room_name} deleted successfully"}

    async def update_room_metadata(self, room_name: str, metadata: str) -> Dict:
        """Update room metadata"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        await room_service.update_room_metadata(
            api.UpdateRoomMetadataRequest(room=room_name, metadata=metadata)
        )
        return {"message": "Room metadata updated successfully", "room": room_name}

    async def get_participant(self, room_name: str, identity: str) -> Dict:
        """Get participant info"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        participant = await room_service.get_participant(
            api.RoomParticipantIdentity(room=room_name, identity=identity)
        )

        return {
            "sid": participant.sid,
            "identity": participant.identity,
            "name": participant.name,
            "state": str(participant.state),
            "metadata": participant.metadata,
            "joinedAt": participant.joined_at,
            "tracks": [
                {
                    "sid": t.sid,
                    "type": str(t.type),
                    "name": t.name,
                }
                for t in participant.tracks
            ],
        }

    async def remove_participant(self, room_name: str, identity: str) -> Dict:
        """Remove participant from room"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        await room_service.remove_participant(
            api.RoomParticipantIdentity(room=room_name, identity=identity)
        )
        return {"message": f"Participant {identity} removed from room {room_name}"}

    async def mute_published_track(
        self, room_name: str, identity: str, track_sid: str, muted: bool
    ) -> Dict:
        """Mute/unmute participant track"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)
        await room_service.mute_published_track(
            api.MuteRoomTrackRequest(
                room=room_name, identity=identity, track_sid=track_sid, muted=muted
            )
        )
        return {
            "message": f"Track {track_sid} {'muted' if muted else 'unmuted'} for participant {identity}"
        }

    async def update_participant(
        self,
        room_name: str,
        identity: str,
        metadata: Optional[str] = None,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Update participant metadata"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)

        request = api.UpdateParticipantRequest(room=room_name, identity=identity)
        if metadata:
            request.metadata = metadata
        if name:
            request.name = name
        if attributes:
            request.attributes = attributes

        await room_service.update_participant(request)
        return {"message": "Participant updated successfully"}

    async def send_data(
        self,
        room_name: str,
        data: bytes,
        destination_identities: Optional[List[str]] = None,
        topic: Optional[str] = None,
    ) -> Dict:
        """Send data message to room"""
        room_service = api.RoomService(self.url, self.api_key, self.api_secret)

        await room_service.send_data(
            api.SendDataRequest(
                room=room_name,
                data=data,
                destination_identities=destination_identities or [],
                topic=topic,
            )
        )
        return {"message": "Data sent successfully"}


# Singleton instance
_livekit_service: Optional[LiveKitService] = None


def initialize_livekit_service(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
) -> Optional[LiveKitService]:
    """Initialize the LiveKit service singleton"""
    global _livekit_service

    if not url or not api_key or not api_secret:
        print("LiveKit credentials not provided - LiveKit endpoints will be disabled")
        return None

    if _livekit_service is None:
        _livekit_service = LiveKitService(url, api_key, api_secret)
    return _livekit_service


def get_livekit_service() -> Optional[LiveKitService]:
    """Get the LiveKit service singleton"""
    return _livekit_service
