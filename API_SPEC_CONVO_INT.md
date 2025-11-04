# Conversation Intelligence API Specification

## Base URL
```
Production: https://api.clarahvac.com/v1
Development: http://localhost:3000
```

---

## Authentication

All endpoints (except `/auth/*`) require JWT authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## 1. Authentication Endpoints

### `POST /auth/google/login`
Initiate Google SSO login

**Request:**
```json
{
  "id_token": "google_id_token_from_client"
}
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "expires_in": 3600,
  "user": {
    "user_id": "USER-12345",
    "email": "tech@example.com",
    "full_name": "John Technician",
    "role": "technician",
    "profile_picture_url": "https://..."
  }
}
```

### `POST /auth/refresh`
Refresh access token

**Request:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_access_token",
  "expires_in": 3600
}
```

### `GET /auth/me`
Get current user profile

**Response:**
```json
{
  "user_id": "USER-12345",
  "email": "tech@example.com",
  "full_name": "John Technician",
  "role": "technician",
  "phone": "+1234567890",
  "team": {
    "team_id": "TEAM-001",
    "name": "Main Team"
  },
  "supervisor": {
    "user_id": "USER-67890",
    "full_name": "Sarah Supervisor"
  }
}
```

---

## 2. User Management

### `GET /users/{user_id}`
Get user profile

**Response:**
```json
{
  "user_id": "USER-12345",
  "email": "tech@example.com",
  "full_name": "John Technician",
  "role": "technician",
  "stats": {
    "total_calls": 45,
    "avg_satisfaction": 4.5,
    "upsell_conversion": 0.32
  }
}
```

### `GET /users/technicians` (Supervisor only)
Get list of assigned technicians

**Response:**
```json
{
  "technicians": [
    {
      "user_id": "USER-12345",
      "full_name": "John Technician",
      "stats": {
        "calls_today": 3,
        "avg_call_duration": 840,
        "customer_satisfaction": 4.8
      }
    }
  ]
}
```

---

## 3. Conversation Management

### `POST /conversations/start`
Start a new conversation recording

**Request:**
```json
{
  "job_id": "JOB-2024-1022-001",
  "customer_name": "Phoenix Mills Ltd",
  "customer_phone": "+91 20 2553 4567",
  "location_address": "FC Road, Pune"
}
```

**Response:**
```json
{
  "conversation_id": "CONV-20241104-001",
  "started_at": "2024-11-04T10:30:00Z",
  "status": "in_progress",
  "websocket_url": "wss://api.clarahvac.com/conversations/CONV-20241104-001/transcribe"
}
```

### `POST /conversations/{conversation_id}/stop`
End conversation recording

**Response:**
```json
{
  "conversation_id": "CONV-20241104-001",
  "ended_at": "2024-11-04T10:45:30Z",
  "duration_seconds": 930,
  "status": "processing",
  "recording_url": "https://storage.clarahvac.com/recordings/CONV-20241104-001.m4a"
}
```

### `POST /conversations/{conversation_id}/upload-audio`
Upload audio chunk (for streaming)

**Request:** `multipart/form-data`
- `chunk`: Audio file (m4a, wav, mp3)
- `sequence`: Integer (chunk order)

**Response:**
```json
{
  "chunk_id": "CHUNK-123",
  "received": true
}
```

### `GET /conversations/{conversation_id}`
Get conversation details

**Response:**
```json
{
  "conversation_id": "CONV-20241104-001",
  "technician": {
    "user_id": "USER-12345",
    "full_name": "John Technician"
  },
  "job": {
    "job_id": "JOB-2024-1022-001",
    "title": "Fire Pump Inspection"
  },
  "customer_name": "Phoenix Mills Ltd",
  "started_at": "2024-11-04T10:30:00Z",
  "ended_at": "2024-11-04T10:45:30Z",
  "duration_seconds": 930,
  "status": "analyzed",
  "recording_url": "https://...",
  "has_insights": true
}
```

### `GET /conversations/technician/{technician_id}`
Get technician's conversation history

**Query Parameters:**
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset
- `status`: Filter by status

**Response:**
```json
{
  "conversations": [...],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

## 4. Transcription

### `WS /conversations/{conversation_id}/transcribe`
WebSocket for real-time transcription

**Server Messages:**
```json
{
  "type": "transcription_segment",
  "segment_id": 123,
  "speaker_type": "technician",
  "text": "Let me check the pressure gauge",
  "start_time": 45.2,
  "end_time": 47.8,
  "is_final": false,
  "confidence": 0.92
}
```

### `GET /conversations/{conversation_id}/transcript`
Get full conversation transcript

**Response:**
```json
{
  "conversation_id": "CONV-20241104-001",
  "segments": [
    {
      "segment_id": 1,
      "speaker_type": "technician",
      "text": "Hi, I'm John from ClaraHVAC",
      "start_time": 0.0,
      "end_time": 2.5
    },
    {
      "segment_id": 2,
      "speaker_type": "customer",
      "text": "Hello, thanks for coming",
      "start_time": 2.8,
      "end_time": 4.2
    }
  ],
  "total_segments": 234
}
```

---

## 5. AI Insights

### `GET /conversations/{conversation_id}/insights`
Get AI-generated insights

**Response:**
```json
{
  "insight_id": 456,
  "conversation_id": "CONV-20241104-001",
  "summary": "Technician completed fire pump inspection. Customer expressed concern about pump age (15 years) and frequent repairs. Technician explained options but did not provide quote for replacement.",
  "key_topics": [
    "Equipment Age",
    "Frequent Repairs",
    "Replacement Options"
  ],
  "overall_sentiment": "positive",
  "customer_satisfaction_score": 85,
  "positive_keywords": [
    "professional",
    "thorough",
    "explained well"
  ],
  "improvement_keywords": [
    "pricing unclear",
    "no written quote"
  ],
  "action_items": [
    "Send replacement quote within 24 hours",
    "Schedule follow-up call next week"
  ]
}
```

### `GET /conversations/{conversation_id}/upsells`
Get detected upsell opportunities

**Response:**
```json
{
  "opportunities": [
    {
      "opportunity_id": 789,
      "opportunity_type": "equipment_replacement",
      "title": "Fire Pump Replacement",
      "description": "Customer mentioned pump is 15 years old with frequent repairs. Strong candidate for replacement.",
      "trigger_phrase": "We've had to fix this pump three times this year",
      "timestamp_in_call": 180.5,
      "confidence": 0.88,
      "estimated_value": 35000.00,
      "priority": "high",
      "status": "identified"
    }
  ]
}
```

### `GET /conversations/{conversation_id}/coaching`
Get coaching moments

**Response:**
```json
{
  "coaching_moments": [
    {
      "moment_id": 234,
      "category": "upsell_missed",
      "title": "Missed Quote Follow-up",
      "timestamp_in_call": 820.0,
      "what_happened": "Customer asked about replacement cost. Technician said 'I'll have to get back to you' but didn't commit to a timeline.",
      "what_should_happen": "Set clear expectation for when quote will be provided",
      "example_better_response": "I'll have a detailed quote to you by tomorrow afternoon. Would email or phone call work better for you?",
      "severity": "important"
    }
  ]
}
```

### `POST /conversations/{conversation_id}/analyze`
Trigger AI analysis manually

**Response:**
```json
{
  "conversation_id": "CONV-20241104-001",
  "status": "processing",
  "estimated_completion": "2024-11-04T11:00:00Z"
}
```

---

## 6. Live Nudging

### `WS /conversations/{conversation_id}/nudges`
WebSocket for live AI nudges

**Server Messages:**
```json
{
  "type": "nudge",
  "nudge_id": 567,
  "nudge_type": "upsell_prompt",
  "title": "💡 Upsell Opportunity",
  "message": "Customer mentioned frequent repairs - suggest maintenance plan",
  "suggested_response": "We offer a preventive maintenance plan that could save you money on these recurring repairs. Would you like to hear about it?",
  "confidence": 0.85,
  "triggered_at": 245.8
}
```

**Client Messages (for nudge actions):**
```json
{
  "action": "dismissed",
  "nudge_id": 567
}
```

---

## 7. Coach Platform (Supervisor)

### `GET /coach/technicians`
Get assigned technicians with stats

**Response:**
```json
{
  "technicians": [
    {
      "user_id": "USER-12345",
      "full_name": "John Technician",
      "stats": {
        "calls_this_week": 12,
        "avg_satisfaction": 4.5,
        "upsell_conversion": 0.35,
        "coaching_moments_count": 8
      }
    }
  ]
}
```

### `GET /coach/calls/recent`
Get recent calls across team

**Query Parameters:**
- `limit`: Default 20
- `days`: Last N days (default: 7)
- `min_rating`: Filter by rating

**Response:**
```json
{
  "calls": [
    {
      "conversation_id": "CONV-20241104-001",
      "technician": {...},
      "customer_name": "Phoenix Mills",
      "duration_seconds": 930,
      "satisfaction_score": 85,
      "upsells_count": 2,
      "coaching_moments_count": 1,
      "started_at": "2024-11-04T10:30:00Z"
    }
  ]
}
```

### `POST /coach/calls/{conversation_id}/feedback`
Leave supervisor feedback

**Request:**
```json
{
  "overall_rating": 4,
  "rapport_rating": 5,
  "technical_rating": 4,
  "upsell_rating": 3,
  "strengths": "Great rapport building. Customer felt comfortable.",
  "areas_for_improvement": "Could have been more proactive with pricing discussion.",
  "is_training_example": true
}
```

**Response:**
```json
{
  "feedback_id": 890,
  "created_at": "2024-11-04T12:00:00Z"
}
```

### `PUT /coach/upsells/{opportunity_id}/status`
Update upsell opportunity status

**Request:**
```json
{
  "status": "closed_won",
  "actual_value": 35000.00,
  "notes": "Customer signed contract. Installation scheduled for next month."
}
```

---

## 8. Analytics

### `GET /analytics/technician/{technician_id}/daily`
Get daily performance metrics

**Query Parameters:**
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response:**
```json
{
  "metrics": [
    {
      "date": "2024-11-04",
      "total_calls": 5,
      "avg_call_duration": 840,
      "upsells_closed": 2,
      "upsell_revenue": 45000.00,
      "avg_customer_satisfaction": 4.6,
      "coaching_moments_count": 3
    }
  ]
}
```

### `GET /analytics/technician/{technician_id}/trends`
Get performance trends

**Response:**
```json
{
  "trends": {
    "calls_trend": "up", // up, down, stable
    "satisfaction_trend": "up",
    "upsell_trend": "stable",
    "weekly_stats": [...]
  }
}
```

### `GET /analytics/team/overview`
Get team-wide analytics (Supervisor only)

**Response:**
```json
{
  "team_stats": {
    "total_calls_this_week": 45,
    "avg_satisfaction": 4.5,
    "total_upsell_revenue": 180000.00,
    "top_performer": {
      "user_id": "USER-12345",
      "full_name": "John Technician",
      "stats": {...}
    }
  }
}
```

### `GET /analytics/leaderboard/{period}`
Get leaderboard

**Path Parameters:**
- `period`: daily, weekly, monthly

**Response:**
```json
{
  "period_type": "weekly",
  "period_start": "2024-10-28",
  "period_end": "2024-11-03",
  "rankings": [
    {
      "rank": 1,
      "user_id": "USER-12345",
      "full_name": "John Technician",
      "score": 95.5,
      "metrics": {
        "calls": 20,
        "satisfaction": 4.8,
        "upsell_conversion": 0.45,
        "revenue": 90000.00
      }
    }
  ]
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token",
    "details": {}
  }
}
```

### Common Error Codes
- `UNAUTHORIZED` (401): Invalid authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (422): Invalid request data
- `SERVER_ERROR` (500): Internal server error

---

## Rate Limiting

- **Standard endpoints**: 100 requests/minute per user
- **WebSocket connections**: 5 concurrent connections per user
- **Upload endpoints**: 10 MB/minute per user

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699104000
```

---

## Webhooks (Future)

For integrations, we'll support webhooks for:
- `conversation.completed` - When call ends
- `insights.generated` - When AI analysis completes
- `upsell.identified` - When new opportunity detected
- `feedback.submitted` - When supervisor leaves feedback
