# Rilla-like Conversation Intelligence Implementation Plan

## Overview
Build a complete conversation intelligence platform similar to Rilla Voice, with real-time transcription, AI insights, coaching platform, and live AI nudging during technician-customer calls.

---

## Phase 1: Authentication & User Management (Week 1-2)

### 1.1 User Authentication System

#### Database Schema (PostgreSQL)
```sql
-- Users table
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'technician', 'supervisor', 'admin'
    google_id VARCHAR(255) UNIQUE,
    profile_picture_url TEXT,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Teams/Organizations
CREATE TABLE teams (
    team_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- User-Team relationship
CREATE TABLE team_members (
    team_id VARCHAR(50) REFERENCES teams(team_id),
    user_id VARCHAR(50) REFERENCES users(user_id),
    role VARCHAR(50) NOT NULL, -- 'member', 'supervisor', 'admin'
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id)
);

-- Supervisor-Technician relationships
CREATE TABLE supervisor_assignments (
    supervisor_id VARCHAR(50) REFERENCES users(user_id),
    technician_id VARCHAR(50) REFERENCES users(user_id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (supervisor_id, technician_id)
);

-- Session tokens
CREATE TABLE auth_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    device_info JSONB
);
```

#### Backend API (clara-server)

**New Files:**
- `auth/google_sso.py` - Google OAuth2 integration
- `auth/jwt_handler.py` - JWT token generation/validation
- `auth/middleware.py` - Authentication middleware
- `users/service.py` - User management service
- `users/models.py` - User data models

**Endpoints:**
```python
# Authentication
POST   /auth/google/login          # Google SSO login
POST   /auth/google/callback       # OAuth callback
POST   /auth/refresh               # Refresh JWT token
POST   /auth/logout                # Logout user
GET    /auth/me                    # Get current user info

# User Management
GET    /users/{user_id}            # Get user profile
PUT    /users/{user_id}            # Update user profile
GET    /users/team/{team_id}       # Get team members
GET    /users/technicians          # Get all technicians (supervisor only)
POST   /users/assign-supervisor    # Assign supervisor to technician
```

#### Frontend (clara-react-native)

**New Screens:**
- `app/(auth)/login.tsx` - Login screen with Google SSO button
- `app/(auth)/role-selection.tsx` - Select role after first login
- `app/(auth)/profile-setup.tsx` - Complete profile setup
- `app/(authenticated)/profile.tsx` - User profile management

**New Context:**
- `contexts/AuthProvider.tsx` - Authentication state management
- Storage: Use `@react-native-async-storage/async-storage` for token persistence

**Libraries to Add:**
```json
{
  "@react-native-google-signin/google-signin": "^11.0.0",
  "@react-native-async-storage/async-storage": "^1.21.0",
  "jwt-decode": "^4.0.0"
}
```

---

## Phase 2: Conversation Recording & Storage (Week 2-3)

### 2.1 Call Recording Infrastructure

#### Database Schema
```sql
-- Conversations/Calls
CREATE TABLE conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    technician_id VARCHAR(50) REFERENCES users(user_id),
    job_id VARCHAR(50) REFERENCES jobs(job_id),
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50),

    -- Recording metadata
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    recording_url TEXT,
    recording_file_size BIGINT,

    -- Context
    location_address TEXT,
    equipment_discussed JSONB DEFAULT '[]'::jsonb,
    job_context JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'processing', 'analyzed'

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Real-time transcription segments
CREATE TABLE transcription_segments (
    segment_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id),

    -- Speaker info
    speaker_type VARCHAR(50) NOT NULL, -- 'technician', 'customer', 'unknown'
    speaker_id VARCHAR(50), -- References users.user_id if technician

    -- Transcription
    text TEXT NOT NULL,
    start_time FLOAT NOT NULL, -- Seconds from conversation start
    end_time FLOAT NOT NULL,
    confidence FLOAT,

    -- Metadata
    is_final BOOLEAN DEFAULT false,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast lookup
CREATE INDEX idx_transcription_conversation ON transcription_segments(conversation_id);
CREATE INDEX idx_transcription_time ON transcription_segments(conversation_id, start_time);
```

#### Backend API

**New Files:**
- `conversations/service.py` - Conversation management
- `conversations/recording.py` - Audio recording handler
- `conversations/storage.py` - S3/cloud storage integration
- `transcription/service.py` - Real-time transcription service

**Endpoints:**
```python
# Conversation Management
POST   /conversations/start         # Start new conversation
POST   /conversations/{id}/stop     # End conversation
GET    /conversations/{id}          # Get conversation details
GET    /conversations/technician/{tech_id}  # Get tech's conversations
POST   /conversations/{id}/upload-audio     # Upload audio chunk

# Transcription
WS     /conversations/{id}/transcribe       # WebSocket for live transcription
GET    /conversations/{id}/transcript       # Get full transcript
```

#### Frontend Implementation

**New Components:**
- `components/conversation/RecordingButton.tsx` - Start/stop recording
- `components/conversation/LiveTranscript.tsx` - Show live transcription
- `components/conversation/ConversationTimer.tsx` - Call duration timer
- `components/conversation/SpeakerIdentifier.tsx` - Show who's speaking

**Recording Flow:**
```typescript
// Use expo-av for audio recording
import { Audio } from 'expo-av';

// Start recording when technician begins customer call
// Stream audio to backend in chunks (every 2-3 seconds)
// Display live transcription
// Save full recording when call ends
```

---

## Phase 3: Real-Time Transcription (Week 3-4)

### 3.1 Transcription Engine

#### Agent Integration (clara-agent)

**New Files:**
- `src/transcription/live_transcriber.py` - LiveKit transcription wrapper
- `src/transcription/speaker_diarization.py` - Identify technician vs customer
- `src/transcription/transcript_processor.py` - Process and clean transcripts

**Technology Stack:**
- Use **Google Speech-to-Text v2** (already integrated via Gemini)
- Add **speaker diarization** to distinguish technician from customer
- Use **streaming recognition** for real-time results

**Implementation:**
```python
class ConversationTranscriber:
    """Real-time conversation transcription with speaker diarization"""

    async def start_transcription(self, conversation_id: str):
        """Start transcribing conversation"""
        # Subscribe to audio stream from both participants
        # Apply speaker diarization
        # Send segments to backend via WebSocket

    async def process_segment(self, audio_chunk: bytes, speaker: str):
        """Process audio chunk and generate transcription"""
        # Use Google STT streaming API
        # Identify speaker (technician vs customer)
        # Save to database with timestamp
```

#### Backend WebSocket Handler

```python
# conversations/websocket.py
@app.websocket("/conversations/{conversation_id}/transcribe")
async def transcription_websocket(websocket: WebSocket, conversation_id: str):
    await websocket.accept()

    try:
        while True:
            # Receive transcription segments from agent
            data = await websocket.receive_json()

            # Save to database
            await save_transcription_segment(conversation_id, data)

            # Broadcast to all connected clients (for supervisor monitoring)
            await broadcast_to_supervisors(conversation_id, data)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from conversation {conversation_id}")
```

---

## Phase 4: AI Insights & Analysis (Week 4-5)

### 4.1 Post-Call AI Analysis

#### Database Schema
```sql
-- AI Insights per conversation
CREATE TABLE conversation_insights (
    insight_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id),

    -- Summary
    summary TEXT,
    key_topics JSONB DEFAULT '[]'::jsonb,

    -- Sentiment Analysis
    overall_sentiment VARCHAR(50), -- 'positive', 'neutral', 'negative'
    sentiment_scores JSONB,
    customer_satisfaction_score FLOAT, -- 0-100

    -- Keywords & Phrases
    positive_keywords JSONB DEFAULT '[]'::jsonb,
    improvement_keywords JSONB DEFAULT '[]'::jsonb,
    technical_terms JSONB DEFAULT '[]'::jsonb,

    -- Action Items
    action_items JSONB DEFAULT '[]'::jsonb,
    follow_ups JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    analyzed_at TIMESTAMP DEFAULT NOW(),
    analysis_model VARCHAR(100)
);

-- Upsell Opportunities
CREATE TABLE upsell_opportunities (
    opportunity_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id),

    -- Opportunity details
    opportunity_type VARCHAR(100), -- 'equipment_upgrade', 'maintenance_plan', 'additional_service'
    title VARCHAR(255),
    description TEXT,

    -- Detected from conversation
    trigger_phrase TEXT,
    timestamp_in_call FLOAT, -- When it was mentioned
    confidence FLOAT, -- 0-1

    -- Business value
    estimated_value DECIMAL(10, 2),
    priority VARCHAR(50), -- 'high', 'medium', 'low'

    -- Status
    status VARCHAR(50) DEFAULT 'identified', -- 'identified', 'pitched', 'closed_won', 'closed_lost'

    created_at TIMESTAMP DEFAULT NOW()
);

-- Coaching Moments (areas for improvement)
CREATE TABLE coaching_moments (
    moment_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id),

    -- Moment details
    category VARCHAR(100), -- 'rapport_building', 'objection_handling', 'upsell_missed', 'technical_explanation'
    title VARCHAR(255),
    description TEXT,

    -- Location in conversation
    timestamp_in_call FLOAT,
    transcript_excerpt TEXT,

    -- Feedback
    what_happened TEXT,
    what_should_happen TEXT,
    example_better_response TEXT,

    -- Severity
    severity VARCHAR(50), -- 'critical', 'important', 'minor'

    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Agent Implementation

**New Files:**
- `src/insights/analyzer.py` - Main conversation analyzer
- `src/insights/upsell_detector.py` - Detect upsell opportunities
- `src/insights/coaching_detector.py` - Identify coaching moments
- `src/insights/sentiment_analyzer.py` - Sentiment analysis

```python
class ConversationAnalyzer:
    """Analyze completed conversations for insights"""

    async def analyze_conversation(self, conversation_id: str):
        """Full conversation analysis"""

        # 1. Get full transcript
        transcript = await self.get_transcript(conversation_id)

        # 2. Generate summary
        summary = await self.generate_summary(transcript)

        # 3. Sentiment analysis
        sentiment = await self.analyze_sentiment(transcript)

        # 4. Detect upsell opportunities
        upsells = await self.detect_upsell_opportunities(transcript)

        # 5. Identify coaching moments
        coaching = await self.identify_coaching_moments(transcript)

        # 6. Extract positive keywords
        keywords = await self.extract_keywords(transcript)

        # 7. Save all insights
        await self.save_insights({
            'summary': summary,
            'sentiment': sentiment,
            'upsells': upsells,
            'coaching': coaching,
            'keywords': keywords
        })
```

**Gemini Prompt for Analysis:**
```python
ANALYSIS_PROMPT = """
Analyze this HVAC technician-customer conversation and provide:

1. SUMMARY (2-3 sentences)
   - What was the service call about?
   - What was resolved?

2. UPSELL OPPORTUNITIES
   For each opportunity:
   - Type (equipment upgrade, maintenance plan, additional service)
   - Specific recommendation
   - Quote from conversation that triggered this
   - Estimated value
   - Priority (high/medium/low)

3. POSITIVE MOMENTS
   - What did the technician do well?
   - Specific phrases or behaviors that built rapport
   - Examples of great customer service

4. COACHING OPPORTUNITIES
   For each opportunity:
   - What happened (missed opportunity or mistake)
   - What should have happened
   - Example of a better response
   - Category (rapport, objection handling, technical explanation, upsell)

5. CUSTOMER SENTIMENT
   - Overall sentiment (positive/neutral/negative)
   - Customer satisfaction score (0-100)
   - Key emotions detected

6. ACTION ITEMS
   - Follow-up tasks for technician
   - Items to log in CRM

Context:
- Job: {job_type} at {location}
- Equipment: {equipment_list}
- Previous history: {equipment_history}

Transcript:
{full_transcript}
"""
```

#### Backend API

```python
# Insights endpoints
GET    /conversations/{id}/insights       # Get AI insights
GET    /conversations/{id}/upsells        # Get upsell opportunities
GET    /conversations/{id}/coaching       # Get coaching moments
POST   /conversations/{id}/analyze        # Trigger analysis manually
```

---

## Phase 5: Coach Platform (Supervisor View) (Week 5-6)

### 5.1 Supervisor Dashboard

#### Frontend Screens

**New Screens:**
- `app/(authenticated)/coach/dashboard.tsx` - Supervisor home
- `app/(authenticated)/coach/technicians.tsx` - List of technicians
- `app/(authenticated)/coach/calls/[id].tsx` - Individual call review
- `app/(authenticated)/coach/analytics.tsx` - Team analytics
- `app/(authenticated)/coach/live.tsx` - Live call monitoring

**Coach Dashboard Components:**
```typescript
// components/coach/TechnicianCard.tsx
interface TechnicianCardProps {
  technician: User;
  stats: {
    calls_today: number;
    avg_call_duration: number;
    upsell_conversion: number;
    customer_satisfaction: number;
  };
}

// components/coach/CallReviewCard.tsx
interface CallReviewCardProps {
  conversation: Conversation;
  insights: ConversationInsights;
  onPlayAudio: () => void;
  onViewTranscript: () => void;
}

// components/coach/InsightCard.tsx
// Display upsells, coaching moments, positive highlights
```

### 5.2 Call Review Interface

**Features:**
- Audio playback with transcript sync
- Highlight coaching moments in timeline
- Annotate specific moments
- Leave feedback for technician
- Mark upsells as "closed won" or "closed lost"

```typescript
// components/coach/CallPlayer.tsx
const CallPlayer: React.FC<{ conversation: Conversation }> = ({ conversation }) => {
  return (
    <View>
      {/* Audio player with waveform */}
      <AudioWaveform audioUrl={conversation.recording_url} />

      {/* Synchronized transcript */}
      <TranscriptView
        segments={transcriptSegments}
        currentTime={currentPlaybackTime}
        highlights={coachingMoments}
      />

      {/* Timeline markers */}
      <Timeline markers={[
        ...upsellOpportunities,
        ...coachingMoments,
        ...positiveMoments
      ]} />

      {/* Insights panel */}
      <InsightsPanel insights={insights} />
    </View>
  );
};
```

#### Backend API

```python
# Supervisor endpoints
GET    /coach/technicians                 # Get assigned technicians
GET    /coach/technicians/{id}/calls      # Get technician's calls
GET    /coach/calls/recent                # Recent calls across team
GET    /coach/analytics/team              # Team performance metrics
POST   /coach/calls/{id}/feedback         # Leave feedback on call
PUT    /coach/upsells/{id}/status         # Update upsell status
```

---

## Phase 6: Rilla Live Mode (Real-time AI Nudging) (Week 6-7)

### 6.1 Live AI Assistant

#### Database Schema
```sql
-- Live AI nudges during calls
CREATE TABLE live_nudges (
    nudge_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id),

    -- Nudge content
    type VARCHAR(50), -- 'upsell_prompt', 'objection_handler', 'next_question', 'warning'
    title VARCHAR(255),
    message TEXT,
    suggested_response TEXT,

    -- Trigger
    triggered_by_phrase TEXT,
    triggered_at FLOAT, -- Timestamp in conversation
    confidence FLOAT,

    -- Action
    was_displayed BOOLEAN DEFAULT true,
    was_dismissed BOOLEAN DEFAULT false,
    was_acted_upon BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Agent Implementation

**New File:** `src/live_coaching/nudge_engine.py`

```python
class LiveNudgeEngine:
    """Real-time AI coaching during calls"""

    def __init__(self):
        self.context_window = []  # Last 30 seconds of conversation
        self.job_context = None
        self.equipment_history = None

    async def process_transcription_segment(self, segment: dict):
        """Process each transcription segment in real-time"""

        # Add to context window
        self.context_window.append(segment)

        # Analyze for nudge opportunities
        nudges = []

        # 1. Upsell opportunities
        if self.detect_upsell_opening(segment):
            nudges.append(await self.generate_upsell_nudge(segment))

        # 2. Objection handling
        if self.detect_customer_objection(segment):
            nudges.append(await self.generate_objection_handler(segment))

        # 3. Missing information
        if self.detect_missing_info(segment):
            nudges.append(await self.generate_info_reminder(segment))

        # 4. Technical assistance
        if self.detect_technical_question(segment):
            nudges.append(await self.generate_technical_help(segment))

        return nudges

    def detect_upsell_opening(self, segment: dict) -> bool:
        """Detect when customer mentions something that could lead to upsell"""

        upsell_triggers = [
            "old", "not working well", "frequent issues",
            "replace", "upgrade", "inefficient",
            "high bills", "maintenance", "warranty"
        ]

        text_lower = segment['text'].lower()
        return any(trigger in text_lower for trigger in upsell_triggers)

    async def generate_upsell_nudge(self, segment: dict) -> dict:
        """Generate upsell nudge based on context"""

        # Use Gemini to generate contextual nudge
        prompt = f"""
        Customer just said: "{segment['text']}"

        Job context: {self.job_context}
        Equipment: {self.equipment_history}

        Generate a brief, specific nudge for the technician to upsell.
        Include:
        1. What to mention (1 sentence)
        2. Suggested question to ask (1 sentence)

        Keep it under 30 words total.
        """

        response = await self.gemini.generate(prompt)

        return {
            'type': 'upsell_prompt',
            'title': '💡 Upsell Opportunity',
            'message': response,
            'confidence': 0.85
        }
```

#### Frontend Live Mode UI

**New Component:** `components/conversation/LiveNudges.tsx`

```typescript
const LiveNudges: React.FC = () => {
  const [activeNudges, setActiveNudges] = useState<Nudge[]>([]);

  // Subscribe to live nudges from agent via WebSocket
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/conversations/${conversationId}/nudges`);

    ws.onmessage = (event) => {
      const nudge = JSON.parse(event.data);
      setActiveNudges(prev => [...prev, nudge]);

      // Auto-dismiss after 15 seconds
      setTimeout(() => {
        setActiveNudges(prev => prev.filter(n => n.id !== nudge.id));
      }, 15000);
    };

    return () => ws.close();
  }, [conversationId]);

  return (
    <View style={styles.nudgeContainer}>
      {activeNudges.map(nudge => (
        <NudgeCard
          key={nudge.id}
          nudge={nudge}
          onDismiss={() => dismissNudge(nudge.id)}
          onAct={() => markAsActedUpon(nudge.id)}
        />
      ))}
    </View>
  );
};
```

**Nudge Types:**

1. **Upsell Prompts**
   - "💡 Customer mentioned high bills - suggest maintenance plan"
   - "🔧 Old equipment (12 years) - consider replacement quote"

2. **Objection Handlers**
   - "💬 Customer concerned about cost - mention financing options"
   - "⚡ Customer hesitant - share warranty benefits"

3. **Next Best Questions**
   - "❓ Ask about other rooms/units that might need service"
   - "📋 Verify maintenance history - check for service contract"

4. **Technical Assistance**
   - "📖 Manual reference: Page 42 has wiring diagram"
   - "⚠️ Reminder: Check manufacturer's recall notice"

5. **Compliance Reminders**
   - "✅ Don't forget to show customer air filter"
   - "📸 Take photo of model/serial number"

---

## Phase 7: Analytics & Performance Metrics (Week 7-8)

### 7.1 Analytics Schema

```sql
-- Daily technician performance metrics
CREATE TABLE daily_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    technician_id VARCHAR(50) REFERENCES users(user_id),
    date DATE NOT NULL,

    -- Call volume
    total_calls INTEGER DEFAULT 0,
    avg_call_duration INTEGER, -- seconds

    -- Conversion metrics
    upsells_identified INTEGER DEFAULT 0,
    upsells_pitched INTEGER DEFAULT 0,
    upsells_closed INTEGER DEFAULT 0,
    upsell_conversion_rate FLOAT,
    upsell_revenue DECIMAL(10, 2) DEFAULT 0,

    -- Quality metrics
    avg_customer_satisfaction FLOAT,
    positive_keyword_count INTEGER DEFAULT 0,
    coaching_moments_count INTEGER DEFAULT 0,

    -- Behavioral metrics
    avg_rapport_score FLOAT, -- 0-100
    avg_technical_explanation_score FLOAT,
    avg_objection_handling_score FLOAT,

    -- Live coaching
    nudges_received INTEGER DEFAULT 0,
    nudges_acted_upon INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(technician_id, date)
);

-- Leaderboard rankings
CREATE TABLE leaderboard_rankings (
    ranking_id SERIAL PRIMARY KEY,
    period_type VARCHAR(50), -- 'daily', 'weekly', 'monthly'
    period_start DATE,
    period_end DATE,

    -- Rankings
    rankings JSONB, -- Array of {user_id, rank, score, metrics}

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 7.2 Analytics Dashboard

**Frontend Screens:**
- `app/(authenticated)/analytics/personal.tsx` - Technician's own stats
- `app/(authenticated)/analytics/team.tsx` - Supervisor team view
- `app/(authenticated)/analytics/leaderboard.tsx` - Competitive rankings

**Key Metrics to Display:**

For Technicians:
- Calls this week/month
- Average customer satisfaction
- Upsell conversion rate
- Personal best moments
- Improvement areas

For Supervisors:
- Team performance overview
- Top performers
- Trending up/down technicians
- Team-wide upsell revenue
- Common coaching needs

#### Backend API

```python
# Analytics endpoints
GET    /analytics/technician/{id}/daily     # Daily metrics
GET    /analytics/technician/{id}/trends    # Performance trends
GET    /analytics/team/overview              # Team metrics
GET    /analytics/leaderboard/{period}       # Leaderboard
POST   /analytics/calculate                  # Trigger metric calculation
```

---

## Implementation Phases Summary

### Phase 1: Foundation (Week 1-2)
- ✅ Google SSO authentication
- ✅ User roles & permissions
- ✅ Database schema setup
- **Deliverable:** Users can log in, roles assigned

### Phase 2: Recording (Week 2-3)
- ✅ In-app call recording
- ✅ Audio storage (S3/cloud)
- ✅ Conversation metadata
- **Deliverable:** Technicians can record customer calls

### Phase 3: Transcription (Week 3-4)
- ✅ Real-time transcription
- ✅ Speaker diarization
- ✅ Transcript storage & retrieval
- **Deliverable:** Live transcription during calls

### Phase 4: AI Insights (Week 4-5)
- ✅ Post-call analysis
- ✅ Upsell detection
- ✅ Coaching moment identification
- ✅ Sentiment analysis
- **Deliverable:** AI-generated insights for every call

### Phase 5: Coach Platform (Week 5-6)
- ✅ Supervisor dashboard
- ✅ Call review interface
- ✅ Feedback mechanism
- ✅ Team analytics
- **Deliverable:** Supervisors can review and coach

### Phase 6: Live Nudging (Week 6-7)
- ✅ Real-time AI nudges
- ✅ Contextual suggestions
- ✅ Live coaching UI
- **Deliverable:** AI assists during live calls

### Phase 7: Analytics (Week 7-8)
- ✅ Performance metrics
- ✅ Leaderboards
- ✅ Trend analysis
- **Deliverable:** Complete analytics platform

---

## Technology Stack

### Frontend (clara-react-native)
- React Native + Expo
- **Auth:** `@react-native-google-signin/google-signin`
- **Audio:** `expo-av` for recording
- **WebSocket:** Native WebSocket API
- **Storage:** `@react-native-async-storage/async-storage`
- **Charts:** `react-native-chart-kit` or `victory-native`

### Backend (clara-server)
- FastAPI (Python)
- **Auth:** `python-jose` for JWT, `google-auth` for OAuth
- **Database:** PostgreSQL with asyncpg
- **Storage:** AWS S3 or Google Cloud Storage
- **WebSocket:** FastAPI WebSocket support

### Agent (clara-agent)
- LiveKit Agents SDK
- **Transcription:** Google Speech-to-Text v2 (via Gemini)
- **AI:** Google Gemini 2.5 Flash
- **Analysis:** Custom NLP + Gemini prompts

### Infrastructure
- **Database:** PostgreSQL (existing)
- **File Storage:** S3 or GCS for audio files
- **WebSocket:** For live transcription & nudges
- **Caching:** Redis (optional, for performance)

---

## Key Features Comparison with Rilla

| Feature | Rilla Voice | Clara Implementation |
|---------|-------------|---------------------|
| Call Recording | ✅ Automatic | ✅ Manual start/stop |
| Live Transcription | ✅ | ✅ |
| Speaker Diarization | ✅ | ✅ |
| AI Insights | ✅ | ✅ |
| Upsell Detection | ✅ | ✅ |
| Coaching Platform | ✅ | ✅ |
| Live AI Nudging | ✅ Rilla Live | ✅ Live Mode |
| Analytics Dashboard | ✅ | ✅ |
| Leaderboards | ✅ | ✅ |
| Job Context Integration | ❌ | ✅ **Better!** |
| Equipment History | ❌ | ✅ **Better!** |
| Integration with CRM | Limited | ✅ **Native** |

---

## Next Steps

1. **Review & Approve Plan**
2. **Set up Google Cloud Console** for OAuth credentials
3. **Create database migrations** for new tables
4. **Begin Phase 1 implementation** (Authentication)

Ready to start implementation?
