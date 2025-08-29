# 911 Call Simulation Training System - Technical Documentation

## Overview

The 911 Call Simulation Training System is a comprehensive AI-powered platform designed to train emergency service operators through realistic simulated emergency calls. The system uses a local Llama-3.1-8B language model to generate dynamic, contextually appropriate caller responses across various emergency scenarios.

### Key Features

- **AI-Powered Caller Simulation**: Uses HuggingFace Transformers with Llama-3.1-8B for natural language generation
- **Dynamic Emotional States**: Tracks and adjusts caller emotional state throughout conversations
- **Scenario-Based Training**: Supports 80+ different emergency scenario types
- **Real-time Conversation Management**: Maintains conversation history and context
- **Progress Tracking**: Monitors training progress and key details revealed
- **RESTful API**: Clean API interface for frontend integration

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React         │    │   Flask API     │    │   Llama Model   │
│   Frontend      │◄──►│   Server        │◄──►│   (Local)       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis         │
                       │   (Optional)    │
                       └─────────────────┘
```

### Core Components

1. **AI Generator** (`ai_generator.py`): Manages the Llama model and response generation
2. **API Server** (`app.py`): Flask-based REST API server
3. **Session Manager** (`session_manager.py`): Handles training session lifecycle
4. **Scenario Contexts** (`scenario_contexts.py`): Manages emergency scenarios and contexts
5. **Data Models** (`models.py`): Defines core data structures

## Installation & Setup

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended for Llama model)
- 16GB+ RAM
- 50GB+ storage for model files

### Dependencies

```bash
pip install r /home/ubuntu/911-simulation-system/backend/requirements.txt
python -m spacy download en_core_web_sm
```

### Model Setup

The development system expects the Llama-3.1-8B model to be located at:
```
/home/ubuntu/.llama/checkpoints/Llama3.1-8B-Instruct-hf
```

Update the `model_path` in `HuggingFaceCallerGenerator.__init__()` if using a different location.

### Configuration

#### Environment Variables

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Server Configuration
HOST=0.0.0.0
PORT=5001
```

## API Documentation

### Base URL
```
http://localhost:5001/api
```

### Endpoints

#### 1. Create Session
**POST** `/sessions`

Creates a new training session for a specific scenario.

**Request Body:**
```json
{
  "trainee_id": "trainer_001",
  "scenario_type": "10-01"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "scenario_type": "10-01",
  "status": "created"
}
```

#### 2. Get Session Info
**GET** `/sessions/{session_id}`

Retrieves current session state and metadata.

**Response:**
```json
{
  "session_id": "uuid-string",
  "scenario_type": "10-01",
  "emotional_state": "panicked",
  "intensity": 8,
  "scenario_progress": 0.45,
  "is_active": true,
  "key_details_revealed": ["location", "situation", "people"]
}
```

#### 3. Send Message
**POST** `/sessions/{session_id}/message`

Sends a message from the operator to the simulated caller and receives a response.

**Request Body:**
```json
{
  "message": "911, what is your emergency?"
}
```

**Response:**
```json
{
  "caller_response": "I've been in an accident!",
  "emotional_state": "panicked",
  "intensity": 7,
  "scenario_progress": 0.15,
  "key_details_revealed": ["situation"],
  "conversation_history": [
    {
      "role": "call_taker",
      "content": "911, what is your emergency?",
      "timestamp": "2025-01-15T10:30:00"
    },
    {
      "role": "caller",
      "content": "I've been in an accident!",
      "timestamp": "2025-01-15T10:30:05"
    }
  ]
}
```

#### 4. End Session
**POST** `/sessions/{session_id}/end`

Terminates the training session.

**Response:**
```json
{
  "status": "terminated"
}
```

#### 5. Health Check
**GET** `/health`

System health and status information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "model_loaded": true,
  "model_path": "/home/ubuntu/.llama/checkpoints/Llama3.1-8B-Instruct-hf",
  "active_sessions": 3
}
```

## Data Models

### Emotional States
```python
class EmotionalState(Enum):
    CALM = "calm"
    WORRIED = "worried" 
    PANICKED = "panicked"
    HYSTERICAL = "hysterical"
    RELIEVED = "relieved"
```

### Scenario Types
The system supports 80+ scenario types including:
- **Traffic Accidents**: `10-01`, `10-02`
- **Criminal Activity**: `10-30` (Robbery), `10-34` (Theft)
- **Emergencies**: `10-08H` (Home Invasion), `10-21` (Mental Health)
- **Traffic Issues**: `10-83` (Impaired Driver), `10-88` (Traffic Hazard)

### CallerState
```python
@dataclass
class CallerState:
    emotional_state: EmotionalState
    intensity: int                    # 1-10 scale
    scenario_type: ScenarioType
    key_details_revealed: List[str]
    conversation_history: List[Dict]
    caller_profile: Dict[str, Any]
    scenario_progress: float          # 0.0-1.0
```

### SessionData
```python
@dataclass
class SessionData:
    session_id: str
    trainee_id: str
    scenario_type: ScenarioType
    caller_state: CallerState
    created_at: datetime
    last_activity: datetime
    is_active: bool
```

## Scenario System

### Scenario Structure
Each scenario includes:
- **Location**: Specific address or area
- **Situation**: What happened
- **Current Status**: Current state of the emergency
- **Caller Background**: Caller's relationship to the incident
- **Caller Name & Phone**: Randomly assigned

### Example Scenario
```python
{
    "location": "Cranston Ave SE / Deerfoot Tr SE",
    "situation": "Witnessed a rollover accident. White SUV is currently in the ditch off southbound Deerfoot Trail.",
    "current_status": "Drive-by caller who has already left the scene. Driver appears to be injured and trapped.",
    "caller_background": "Excited drive-by witness who saw the accident while driving.",
    "caller_name": "John Smith",
    "phone": "403-555-0123"
}
```

## AI Response Generation

### Process Flow
1. **Context Building**: Combines scenario context, conversation history, and current message
2. **System Prompt Creation**: Generates appropriate system prompt based on emotional state
3. **Model Inference**: Uses Llama-3.1-8B to generate response
4. **Response Cleaning**: Removes artifacts, fixes grammar, naturalizes language
5. **State Update**: Updates emotional state and scenario progress

### Response Quality Controls
- **Stage Direction Removal**: Eliminates theatrical elements like "(pauses)" or "(sighs)"
- **Grammar Correction**: Fixes basic grammar and punctuation errors
- **Naturalization**: Converts formal language to conversational tone
- **Coherence Validation**: Ensures responses address the operator's questions
- **Fallback Responses**: Provides sensible defaults for poor generations

### Emotional State Management
The system dynamically adjusts caller emotional state based on:
- **Operator Behavior**: Calming words reduce intensity
- **Question Quality**: Poor responses increase agitation
- **Scenario Progress**: Revealing key details can affect emotional state
- **Time Progression**: Generally trends toward calmer states

## Frontend Integration

### React Integration Points

#### Session Management
```javascript
// Create new session
const createSession = async (traineeId, scenarioType) => {
  const response = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trainee_id: traineeId, scenario_type: scenarioType })
  });
  return response.json();
};
```

#### Message Exchange
```javascript
// Send message and get caller response
const sendMessage = async (sessionId, message) => {
  const response = await fetch(`/api/sessions/${sessionId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  return response.json();
};
```

#### Real-time Updates
```javascript
// Recommended polling interval for session updates
const pollSessionStatus = (sessionId) => {
  setInterval(async () => {
    const status = await fetch(`/api/sessions/${sessionId}`);
    const data = await status.json();
    updateUI(data);
  }, 5000); // Poll every 5 seconds
};
```

### UI Components Suggestions

1. **Scenario Selection**: Dropdown/grid for choosing emergency types
2. **Conversation Interface**: Chat-like interface with operator/caller distinction
3. **Emotional Indicator**: Visual representation of caller's emotional state
4. **Progress Tracker**: Shows scenario completion and key details revealed
5. **Session Controls**: Start, terminate, end session functionality

## Performance Optimization

### Model Performance
- **GPU Utilization**: Ensure CUDA is properly configured
- **Batch Size**: Adjust based on available memory
- **Model Quantization**: Consider using quantized models for faster inference
- **Threading**: Uses thread locking to prevent concurrent model access

### API Performance
- **Connection Pooling**: Use connection pooling for database operations
- **Caching**: Implement Redis caching for session data
- **Async Processing**: Consider async endpoints for long-running operations

### Memory Management
- **Session Cleanup**: Implement automatic cleanup of inactive sessions
- **History Limiting**: Truncate conversation history for long sessions
- **Model Loading**: Load model once at startup, not per request

## Error Handling

### Common Error Scenarios
1. **Model Loading Failures**: Verify model path and GPU availability
2. **Session Not Found**: Handle invalid session IDs gracefully
3. **Generation Failures**: Implement fallback responses
4. **Memory Issues**: Monitor GPU/CPU memory usage

### Error Response Format
```json
{
  "error": "Session not found",
  "error_code": "SESSION_NOT_FOUND",
  "timestamp": "2025-01-15T10:30:00"
}
```

## Security Considerations

### Data Protection
- **Session Isolation**: Ensure sessions cannot access each other's data
- **Input Validation**: Validate all API inputs
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Authentication**: Consider adding authentication for production use

### Model Security
- **Local Deployment**: Model runs locally, preventing data leakage
- **Access Control**: Restrict access to model files and configuration
- **Input Sanitization**: Clean user inputs before model processing

## Deployment

### Development Deployment
```bash
# Start the server
python app.py

# Server will run on http://localhost:5001
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:5001 app:app
```

#### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5001", "app:app"]
```

### Environment-Specific Configuration
- **Development**: Single worker, debug mode enabled
- **Staging**: Multiple workers, logging enabled
- **Production**: Load balancing, monitoring, SSL termination

## Monitoring & Logging

### Key Metrics
- **Response Time**: Track API response times
- **Model Performance**: Monitor generation speed and quality
- **Session Activity**: Track active sessions and usage patterns
- **Error Rates**: Monitor API error rates and types

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```
