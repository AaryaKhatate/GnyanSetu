#  Visualization Orchestrator Service

## Overview

The **Visualization Orchestrator Service** is a microservice that validates, optimizes, and coordinates dynamic visualization instructions for GnyanSetu's AI learning platform.

### Key Features

 **Smart Coordinate Management**
- 9-zone layout system (1920x1080 canvas)
- Automatic space allocation
- Overlap prevention
- Perfect positioning

 **Validation & Optimization**
- JSON structure validation
- Animation sequencing
- Scene timing optimization
- Error handling & warnings

 **Multi-Format Support**
- Shapes: circle, rectangle, line, arrow, text, image, polygon
- Animations: fadeIn, fadeOut, scale, move, rotate, pulse, glow, draw, write, orbit
- Effects: background, particles, glow, filters

 **Real-Time Streaming**
- WebSocket support
- Scene-by-scene delivery
- Audio-visual synchronization

---

## Installation

```bash
# Clone repository
cd microservices/visualization-service

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URL
```

---

## Configuration

Create `.env` file:

```env
MONGODB_URL=mongodb://localhost:27017
PORT=8006
```

---

## Running the Service

### Windows

```bash
start_service.bat
```

### Linux/Mac

```bash
python app.py
```

The service will start on **http://localhost:8006**

---

## API Endpoints

### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-11T12:00:00"
}
```

---

### 2. Process Visualization

```http
POST /api/visualizations/process
Content-Type: application/json
```

**Request Body:**
```json
{
  "lesson_id": "12345",
  "topic": "Photosynthesis",
  "explanation": "Visual breakdown of photosynthesis process",
  "scenes": [
    {
      "scene_id": "intro",
      "title": "Introduction",
      "duration": 10.0,
      "shapes": [
        {
          "type": "circle",
          "zone": "center",
          "radius": 50,
          "fill": "#4A90E2",
          "label": "Chloroplast"
        }
      ],
      "animations": [
        {
          "shape_index": 0,
          "type": "fadeIn",
          "duration": 2.0,
          "delay": 0.0
        }
      ],
      "effects": {
        "background": "white"
      },
      "audio": {
        "text": "Let's explore photosynthesis",
        "start_time": 0.0,
        "duration": 10.0
      }
    }
  ]
}
```

**Response:**
```json
{
  "visualization_id": "viz_12345_20251011120000",
  "lesson_id": "12345",
  "status": "processed",
  "scenes": [...],
  "total_duration": 10.0,
  "created_at": "2025-10-11T12:00:00",
  "errors": [],
  "warnings": []
}
```

---

### 3. Get Visualization by ID

```http
GET /api/visualizations/{visualization_id}
```

**Response:**
```json
{
  "visualization_id": "viz_12345_20251011120000",
  "lesson_id": "12345",
  "topic": "Photosynthesis",
  "scenes": [...],
  "canvas": {
    "width": 1920,
    "height": 1080,
    "padding": 50
  }
}
```

---

### 4. Get Visualizations by Lesson

```http
GET /api/visualizations/lesson/{lesson_id}
```

**Response:**
```json
{
  "lesson_id": "12345",
  "visualizations": [...]
}
```

---

### 5. WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:8006/ws/visualization/session_123');

// Send request
ws.send(JSON.stringify({
  type: 'request_visualization',
  lesson_id: '12345'
}));

// Receive visualization
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

## Coordinate System

### Canvas Layout

```
Canvas: 1920x1080 pixels
Padding: 50px
Zone Spacing: 20px

┌──────────────────┬──────────────────┬──────────────────┐
│  TOP_LEFT        │  TOP_CENTER      │  TOP_RIGHT       │
│  580x310         │  580x310         │  580x310         │
├──────────────────┼──────────────────┼──────────────────┤
│  CENTER_LEFT     │  CENTER          │  CENTER_RIGHT    │
│  580x310         │  580x310         │  580x310         │
├──────────────────┼──────────────────┼──────────────────┤
│  BOTTOM_LEFT     │  BOTTOM_CENTER   │  BOTTOM_RIGHT    │
│  580x310         │  580x310         │  580x310         │
└──────────────────┴──────────────────┴──────────────────┘
```

### Zone-Based Positioning

```json
{
  "type": "circle",
  "zone": "center",  //  Smart positioning
  "radius": 50
}
```

The orchestrator automatically calculates perfect coordinates within the specified zone.

---

## Shape Types

| Type | Required Props | Optional Props |
|------|---------------|----------------|
| `circle` | `zone` or `x,y`, `radius` | `fill`, `stroke`, `strokeWidth`, `label` |
| `rectangle` | `zone` or `x,y`, `width`, `height` | `fill`, `stroke`, `cornerRadius` |
| `line` | `points` | `stroke`, `strokeWidth` |
| `arrow` | `points` | `stroke`, `strokeWidth`, `pointerLength` |
| `text` | `text`, `zone` or `x,y` | `fontSize`, `fontFamily`, `fill` |
| `image` | `src`, `zone` or `x,y` | `width`, `height` |
| `polygon` | `points` | `fill`, `stroke`, `strokeWidth` |

---

## Animation Types

| Type | Description | Properties |
|------|-------------|-----------|
| `fadeIn` | Fade in from transparent | `duration`, `delay` |
| `fadeOut` | Fade out to transparent | `duration`, `delay` |
| `scale` | Grow/shrink | `from_props`, `to_props`, `duration` |
| `move` | Translate position | `to_props: {x, y}` |
| `rotate` | Rotate | `to_props: {rotation}` |
| `pulse` | Pulsate effect | `duration`, `repeat`, `yoyo` |
| `glow` | Glow/shadow effect | `duration`, `glow_color` |
| `draw` | Draw line/arrow | `duration` |
| `write` | Type text | `duration` |
| `orbit` | Circular motion | `orbit_center`, `orbit_radius` |

---

## Error Handling

The service provides comprehensive error handling:

```json
{
  "visualization_id": "viz_123",
  "status": "processed",
  "errors": [
    "Scene 2: Animation references invalid shape index 10"
  ],
  "warnings": [
    "Scene 1: Shape 3 has no zone or coordinates, using canvas center"
  ]
}
```

---

## MongoDB Schema

```javascript
{
  visualization_id: String,        // Unique ID
  lesson_id: String,               // Reference to lesson
  topic: String,                   // Lesson topic
  explanation: String,             // Visual explanation
  session_id: String,              // Optional session reference
  status: String,                  // "processed"
  scenes: [Scene],                 // Optimized scene data
  total_duration: Number,          // Total playback time
  canvas: {                        // Canvas configuration
    width: Number,
    height: Number,
    padding: Number
  },
  errors: [String],                // Processing errors
  warnings: [String],              // Processing warnings
  created_at: ISODate,
  updated_at: ISODate
}
```

---

## Development

### Run in Development Mode

```bash
# With auto-reload
uvicorn app:app --host 0.0.0.0 --port 8006 --reload
```

### Run Tests

```bash
pytest tests/
```

### View API Documentation

Open browser: **http://localhost:8006/docs**

FastAPI automatically generates interactive API documentation.

---

## Logging

The service logs all operations:

```
INFO:      Connected to MongoDB: visualization_db
INFO:     Received visualization request for lesson: 12345
INFO:     Initialized CoordinateManager: Canvas 1920x1080, Zones 580x310
WARNING:  Could not find non-overlapping space in center, using fallback position
INFO:      Stored visualization: viz_12345_20251011120000
ERROR:     Error processing visualization: Invalid scene structure
```

---

## Performance

- **MongoDB Indexing**: Automatic indexing on `lesson_id` and `visualization_id`
- **Connection Pooling**: Motor async driver for efficient database operations
- **WebSocket**: Persistent connections for real-time streaming
- **Validation**: Pydantic models for fast validation

---

## Security

1. **Input Validation**: All inputs validated with Pydantic
2. **CORS**: Configured for allowed origins
3. **Rate Limiting**: (TODO) Add rate limiting middleware
4. **MongoDB Auth**: Use authenticated connections in production

---

## Troubleshooting

### MongoDB Connection Error

```bash
# Check MongoDB is running
# Windows:
net start MongoDB

# Linux:
sudo systemctl status mongod
```

### Port Already in Use

```bash
# Change port in .env
PORT=8007
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

## License

MIT License - Part of GnyanSetu Project

---

## Contact

For issues or questions, please refer to the main GnyanSetu documentation.

---

**Version:** 1.0.0  
**Last Updated:** October 11, 2025
