"""
Visualization Orchestrator Service
====================================
TWO-STAGE ARCHITECTURE:
1. Lesson Service → Educational content (lessons, teaching_steps)
2. Visualization Service → Extraordinary visualizations (icons, images, subject-specific shapes)

Uses dedicated Gemini LLM call ONLY for visualization generation
Ensures perfect coordinate management, no overlaps, and audio-visual sync

Port: 8006
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Literal, TYPE_CHECKING
from enum import Enum
import json
import logging
import os
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from collections import defaultdict
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
VISUALIZATION_DB_NAME = "visualization_db"
PORT = 8006

# Gemini AI Configuration for Visualization Generation
# Use the SAME API key as lesson service
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    # Prefer environment variable over hardcoded
    pass
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use gemini-2.0-flash-exp for fast, efficient generation
    GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("✅ Gemini AI configured for visualization generation")
else:
    GEMINI_MODEL = None
    logger.warning("⚠️ Gemini API key not found - visualization generation will use fallback")

# Canvas Configuration
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
PADDING = 50
ZONE_SPACING = 20

# ==================== Enums ====================
class VisualElementType(str, Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    IMAGE = "image"
    PATH = "path"
    GROUP = "group"
    POLYGON = "polygon"

class AnimationType(str, Enum):
    FADE_IN = "fadeIn"
    FADE_OUT = "fadeOut"
    DRAW = "draw"
    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"
    PULSE = "pulse"
    GLOW = "glow"
    WRITE = "write"
    ORBIT = "orbit"
    MORPH = "morph"

class LayoutZone(str, Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

# ==================== Pydantic Models ====================
class ShapeModel(BaseModel):
    type: VisualElementType
    x: Optional[float] = None
    y: Optional[float] = None
    zone: Optional[LayoutZone] = None  # Smart zone-based positioning
    width: Optional[float] = None
    height: Optional[float] = None
    radius: Optional[float] = None
    fill: Optional[str] = "transparent"
    stroke: Optional[str] = "#000000"
    strokeWidth: Optional[float] = 2
    label: Optional[str] = None
    points: Optional[List[float]] = None  # For polygons, lines
    text: Optional[str] = None  # For text elements
    fontSize: Optional[int] = 16
    fontFamily: Optional[str] = "Arial"
    src: Optional[str] = None  # For images
    rotation: Optional[float] = 0
    opacity: Optional[float] = 1.0
    zIndex: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = {}

class AnimationModel(BaseModel):
    shape_index: int = Field(..., description="Index of shape to animate (0-based)")
    type: AnimationType
    duration: float = Field(2.0, ge=0.1, le=30.0)
    delay: float = Field(0.0, ge=0.0)
    ease: Optional[str] = "power2.inOut"
    from_props: Optional[Dict[str, Any]] = None
    to_props: Optional[Dict[str, Any]] = None
    path: Optional[List[List[float]]] = None  # For move animations
    orbit_center: Optional[List[float]] = None  # For orbit animations
    orbit_radius: Optional[float] = None
    repeat: Optional[int] = 0  # -1 for infinite
    yoyo: Optional[bool] = False

class EffectsModel(BaseModel):
    background: Optional[str] = "white"
    particles: Optional[bool] = False
    particle_config: Optional[Dict[str, Any]] = None
    glow: Optional[bool] = False
    glow_color: Optional[str] = "#FFD700"
    filter: Optional[str] = None  # blur, brightness, contrast, etc.

class AudioSyncModel(BaseModel):
    text: str = Field(..., description="Text to be narrated")
    start_time: float = Field(0.0, ge=0.0)
    duration: float = Field(..., ge=0.1)
    tts_config: Optional[Dict[str, Any]] = None

class VisualizationSceneModel(BaseModel):
    scene_id: str
    title: Optional[str] = None
    duration: float = Field(..., ge=1.0, le=60.0)
    shapes: List[ShapeModel] = []
    animations: List[AnimationModel] = []
    effects: Optional[EffectsModel] = EffectsModel()
    audio: Optional[AudioSyncModel] = None
    metadata: Optional[Dict[str, Any]] = {}

class VisualizationRequestModel(BaseModel):
    lesson_id: str
    topic: str
    explanation: str
    scenes: List[VisualizationSceneModel]
    session_id: Optional[str] = None

class VisualizationResponseModel(BaseModel):
    visualization_id: str
    lesson_id: str
    status: str
    scenes: List[Dict[str, Any]]
    total_duration: float
    created_at: str
    errors: Optional[List[str]] = []
    warnings: Optional[List[str]] = []

# ==================== NEW: Konva.js Whiteboard Models ====================
class WhiteboardCommand(BaseModel):
    """Whiteboard drawing commands for Konva.js rendering"""
    action: Literal[
        "clear_all", "write_text", "draw_text_box", "draw_circle", 
        "draw_rectangle", "draw_line", "draw_arrow", "draw_image",
        "highlight_object", "draw_equation", "draw_path"
    ]
    # Dynamic fields based on action
    text: Optional[str] = None
    x_percent: Optional[float] = Field(None, ge=0, le=100)
    y_percent: Optional[float] = Field(None, ge=0, le=100)
    font_size: Optional[int] = None
    color: Optional[str] = None
    align: Optional[Literal["left", "center", "right"]] = None
    width_percent: Optional[float] = Field(None, ge=0, le=100)
    height: Optional[int] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    radius: Optional[int] = None
    points_percent: Optional[List[List[float]]] = None
    from_percent: Optional[List[float]] = None
    to_percent: Optional[List[float]] = None
    image_id: Optional[str] = None
    scale: Optional[float] = None
    target_text: Optional[str] = None
    target_id: Optional[str] = None
    duration: Optional[int] = None
    latex: Optional[str] = None
    thickness: Optional[float] = None
    path_data: Optional[str] = None  # SVG path data

class TeachingStep(BaseModel):
    """Single step in teaching sequence"""
    type: Literal["explanation_start", "explanation_step", "notes_and_quiz_ready"]
    text_explanation: str
    tts_text: str
    whiteboard_commands: List[WhiteboardCommand]

class ImageInfo(BaseModel):
    """Extracted PDF image with explanation"""
    id: str
    base64_data: Optional[str] = None
    explanation: str
    description: Optional[str] = None
    teaching_points: Optional[List[str]] = []
    narration: Optional[str] = None

class VisualizationDataV2(BaseModel):
    """New visualization format for Konva.js"""
    teaching_sequence: List[TeachingStep]
    images: List[ImageInfo] = []
    notes_content: Optional[str] = None
    quiz: Optional[List[Dict[str, Any]]] = []

# ==================== Coordinate Manager ====================
class CoordinateManager:
    """
    Smart coordinate management system to prevent overlaps
    Divides canvas into 9 zones and manages space allocation
    """
    
    def __init__(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, padding=PADDING):
        self.width = width
        self.height = height
        self.padding = padding
        
        # Calculate zone dimensions
        self.zone_width = (width - 2 * padding - 2 * ZONE_SPACING) // 3
        self.zone_height = (height - 2 * padding - 2 * ZONE_SPACING) // 3
        
        # Zone allocation tracker
        self.zone_allocations = defaultdict(list)  # zone -> [(x, y, width, height), ...]
        
        logger.info(f"Initialized CoordinateManager: Canvas {width}x{height}, Zones {self.zone_width}x{self.zone_height}")
    
    def get_zone_bounds(self, zone: LayoutZone) -> Dict[str, float]:
        """Get the boundaries of a specific zone"""
        zone_map = {
            LayoutZone.TOP_LEFT: (0, 0),
            LayoutZone.TOP_CENTER: (1, 0),
            LayoutZone.TOP_RIGHT: (2, 0),
            LayoutZone.CENTER_LEFT: (0, 1),
            LayoutZone.CENTER: (1, 1),
            LayoutZone.CENTER_RIGHT: (2, 1),
            LayoutZone.BOTTOM_LEFT: (0, 2),
            LayoutZone.BOTTOM_CENTER: (1, 2),
            LayoutZone.BOTTOM_RIGHT: (2, 2),
        }
        
        col, row = zone_map[zone]
        x = self.padding + col * (self.zone_width + ZONE_SPACING)
        y = self.padding + row * (self.zone_height + ZONE_SPACING)
        
        return {
            "x": x,
            "y": y,
            "width": self.zone_width,
            "height": self.zone_height
        }
    
    def check_overlap(self, x: float, y: float, width: float, height: float, zone: LayoutZone) -> bool:
        """Check if proposed coordinates overlap with existing allocations"""
        for allocated in self.zone_allocations[zone]:
            ax, ay, aw, ah = allocated
            
            # Check rectangle overlap
            if not (x + width < ax or x > ax + aw or y + height < ay or y > ay + ah):
                return True  # Overlap detected
        
        return False  # No overlap
    
    def allocate_space(self, zone: LayoutZone, width: float, height: float, 
                       preferred_x: Optional[float] = None, 
                       preferred_y: Optional[float] = None) -> Dict[str, float]:
        """
        Allocate space within a zone, avoiding overlaps
        Returns final coordinates
        """
        zone_bounds = self.get_zone_bounds(zone)
        
        # Try preferred position first
        if preferred_x is not None and preferred_y is not None:
            if not self.check_overlap(preferred_x, preferred_y, width, height, zone):
                self.zone_allocations[zone].append((preferred_x, preferred_y, width, height))
                return {"x": preferred_x, "y": preferred_y}
        
        # Try to find available space in zone
        for attempt_y in range(int(zone_bounds["y"]), int(zone_bounds["y"] + zone_bounds["height"] - height), 10):
            for attempt_x in range(int(zone_bounds["x"]), int(zone_bounds["x"] + zone_bounds["width"] - width), 10):
                if not self.check_overlap(attempt_x, attempt_y, width, height, zone):
                    self.zone_allocations[zone].append((attempt_x, attempt_y, width, height))
                    return {"x": attempt_x, "y": attempt_y}
        
        # Fallback: center of zone (may overlap, but logged as warning)
        fallback_x = zone_bounds["x"] + (zone_bounds["width"] - width) / 2
        fallback_y = zone_bounds["y"] + (zone_bounds["height"] - height) / 2
        self.zone_allocations[zone].append((fallback_x, fallback_y, width, height))
        logger.warning(f"Could not find non-overlapping space in {zone}, using fallback position")
        return {"x": fallback_x, "y": fallback_y}
    
    def reset(self):
        """Reset all allocations (for new scene)"""
        self.zone_allocations.clear()

# ==================== Visualization Processor ====================
class VisualizationProcessor:
    """
    Core processing engine for visualization instructions
    Validates, optimizes, and enriches visualization data
    """
    
    def __init__(self):
        self.coord_manager = CoordinateManager()
    
    def process_visualization(self, viz_request: VisualizationRequestModel) -> Dict[str, Any]:
        """
        Main processing pipeline for visualization request
        Returns optimized and validated visualization data
        """
        errors = []
        warnings = []
        processed_scenes = []
        total_duration = 0.0
        
        logger.info(f"Processing visualization for lesson: {viz_request.lesson_id}, Topic: {viz_request.topic}")
        
        for scene_idx, scene in enumerate(viz_request.scenes):
            try:
                # Reset coordinate manager for each scene
                self.coord_manager.reset()
                
                # Process scene
                processed_scene = self._process_scene(scene, scene_idx, warnings)
                processed_scenes.append(processed_scene)
                total_duration += scene.duration
                
            except Exception as e:
                error_msg = f"Scene {scene_idx} ({scene.scene_id}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if not processed_scenes:
            raise ValueError("No valid scenes to process")
        
        return {
            "scenes": processed_scenes,
            "total_duration": total_duration,
            "errors": errors,
            "warnings": warnings,
            "canvas": {
                "width": CANVAS_WIDTH,
                "height": CANVAS_HEIGHT,
                "padding": PADDING
            }
        }
    
    def _process_scene(self, scene: VisualizationSceneModel, scene_idx: int, warnings: List[str]) -> Dict[str, Any]:
        """Process a single scene with coordinate management"""
        processed_shapes = []
        
        # Process shapes with coordinate allocation
        for shape_idx, shape in enumerate(scene.shapes):
            try:
                processed_shape = self._process_shape(shape, shape_idx, warnings)
                processed_shapes.append(processed_shape)
            except Exception as e:
                warnings.append(f"Scene {scene_idx}, Shape {shape_idx}: {str(e)}")
        
        # Validate animations reference valid shapes
        valid_animations = []
        for anim in scene.animations:
            if 0 <= anim.shape_index < len(processed_shapes):
                # Use model_dump with exclude_none
                anim_data = anim.model_dump(exclude_none=True) if hasattr(anim, 'model_dump') else anim.dict(exclude_none=True)
                valid_animations.append(anim_data)
            else:
                warnings.append(f"Scene {scene_idx}: Animation references invalid shape index {anim.shape_index}")
        
        # Build audio sync
        audio_data = None
        if scene.audio:
            audio_data = {
                "text": scene.audio.text,
                "start_time": scene.audio.start_time,
                "duration": scene.audio.duration,
                "tts_config": scene.audio.tts_config or {
                    "voice": "en-US-Neural2-J",
                    "speaking_rate": 1.0,
                    "pitch": 0.0
                }
            }
        
        return {
            "scene_id": scene.scene_id,
            "title": scene.title,
            "duration": scene.duration,
            "shapes": processed_shapes,
            "animations": valid_animations,
            "effects": (scene.effects.model_dump(exclude_none=True) if hasattr(scene.effects, 'model_dump') else scene.effects.dict(exclude_none=True)) if scene.effects else {},
            "audio": audio_data,
            "metadata": scene.metadata
        }
    
    def _process_shape(self, shape: ShapeModel, shape_idx: int, warnings: List[str]) -> Dict[str, Any]:
        """Process shape with smart coordinate allocation"""
        # Use model_dump with exclude_none to avoid sending undefined properties to frontend
        shape_data = shape.model_dump(exclude_none=True) if hasattr(shape, 'model_dump') else shape.dict(exclude_none=True)
        
        # Calculate dimensions
        width = shape.width or (shape.radius * 2 if shape.radius else 100)
        height = shape.height or (shape.radius * 2 if shape.radius else 100)
        
        # Allocate coordinates if zone is specified
        if shape.zone:
            coords = self.coord_manager.allocate_space(
                zone=shape.zone,
                width=width,
                height=height,
                preferred_x=shape.x,
                preferred_y=shape.y
            )
            shape_data["x"] = coords["x"]
            shape_data["y"] = coords["y"]
        elif shape.x is None or shape.y is None:
            # No zone and no coordinates - use center as fallback
            shape_data["x"] = CANVAS_WIDTH / 2 - width / 2
            shape_data["y"] = CANVAS_HEIGHT / 2 - height / 2
            warnings.append(f"Shape {shape_idx} has no zone or coordinates, using canvas center")
        
        # Ensure coordinates are within canvas bounds
        shape_data["x"] = max(PADDING, min(shape_data["x"], CANVAS_WIDTH - width - PADDING))
        shape_data["y"] = max(PADDING, min(shape_data["y"], CANVAS_HEIGHT - height - PADDING))
        
        return shape_data

# ==================== FastAPI App ====================
app = FastAPI(
    title="Visualization Orchestrator Service",
    description="Validates and orchestrates visualization instructions for AI teaching",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Client
mongo_client = None
visualization_db = None

# Processor
processor = VisualizationProcessor()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()

# ==================== Startup/Shutdown ====================
@app.on_event("startup")
async def startup_db_client():
    global mongo_client, visualization_db
    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        visualization_db = mongo_client[VISUALIZATION_DB_NAME]
        
        # Test connection
        await mongo_client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {VISUALIZATION_DB_NAME}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

# ==================== API Endpoints ====================
@app.get("/")
async def root():
    return {
        "service": "Visualization Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "canvas": {
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "zones": 9
        }
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if mongo_client else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== NEW: Konva.js Whiteboard Visualization Generation ====================
WHITEBOARD_VISUALIZATION_PROMPT = """You are an AI Virtual Teacher creating interactive whiteboard teaching sequences using Konva.js.

INPUT:
- Topic: {topic}
- Lesson content: {lesson_content}
- Images available: {images_info}

OUTPUT: Generate a JSON object with step-by-step teaching sequence using whiteboard commands.

WHITEBOARD COMMANDS AVAILABLE:
1. clear_all - Clear the canvas
   {{"action": "clear_all"}}

2. write_text - Display text at position (percentage-based)
   {{"action": "write_text", "text": "...", "x_percent": 50, "y_percent": 20, "font_size": 30, "color": "#1e40af", "align": "center"}}

3. draw_text_box - Text in colored box
   {{"action": "draw_text_box", "text": "...", "x_percent": 30, "y_percent": 40, "width_percent": 20, "height": 60, "color": "#bfdbfe", "stroke": "#60a5fa"}}

4. draw_circle - Circle shape
   {{"action": "draw_circle", "x_percent": 50, "y_percent": 50, "radius": 30, "fill": "#dcfce7", "stroke": "#10b981"}}

5. draw_rectangle - Rectangle
   {{"action": "draw_rectangle", "x_percent": 40, "y_percent": 40, "width_percent": 15, "height": 60, "fill": "#fee2e2", "stroke": "#ef4444"}}

6. draw_line - Connect points
   {{"action": "draw_line", "points_percent": [[10,10], [90,90]], "stroke": "#374151", "stroke_width": 3}}

7. draw_arrow - Arrow with direction
   {{"action": "draw_arrow", "from_percent": [20,50], "to_percent": [80,50], "color": "#065f46", "thickness": 2}}

8. draw_image - Display extracted PDF image
   {{"action": "draw_image", "image_id": "pdf_img_1", "x_percent": 50, "y_percent": 50, "scale": 1.0}}

9. highlight_object - Emphasize element temporarily
   {{"action": "highlight_object", "target_text": "Voltage (V)", "duration": 2000, "color": "#f59e0b"}}

10. draw_equation - Math equation (LaTeX)
    {{"action": "draw_equation", "latex": "E = mc^2", "x_percent": 50, "y_percent": 50, "font_size": 36}}

TEACHING SEQUENCE GUIDELINES:
1. Start with "explanation_start" - Introduction with title
2. Create 4-7 "explanation_step" entries
3. Each step should:
   - Clear canvas OR build on previous step
   - Add visual elements progressively
   - Provide clear narration for TTS
   - Use PDF images when relevant
4. Use colors appropriate to subject:
   - Biology: Greens (#16a34a, #22c55e), Blues (#0284c7)
   - Physics: Blues (#3b82f6), Purples (#8b5cf6)
   - Chemistry: Blues (#3b82f6), Reds (#ef4444), Grays (#6b7280)
   - Math: Blacks (#1f2937), Blues (#2563eb)

EXAMPLE OUTPUT FORMAT:
{{
    "teaching_sequence": [
        {{
            "type": "explanation_start",
            "text_explanation": "Today we'll learn about Photosynthesis - how plants make food using sunlight.",
            "tts_text": "Hello! Today we'll explore photosynthesis, the amazing process plants use to create their own food using sunlight.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "Photosynthesis", "x_percent": 50, "y_percent": 30, "font_size": 48, "color": "#16a34a", "align": "center"}},
                {{"action": "write_text", "text": "How Plants Make Food", "x_percent": 50, "y_percent": 45, "font_size": 24, "color": "#6b7280", "align": "center"}}
            ]
        }},
        {{
            "type": "explanation_step",
            "text_explanation": "Photosynthesis requires three key ingredients: Sunlight, Water, and Carbon Dioxide.",
            "tts_text": "For photosynthesis to occur, plants need three essential ingredients: sunlight from the sun, water from the soil, and carbon dioxide from the air.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "Three Key Ingredients", "x_percent": 50, "y_percent": 10, "font_size": 30, "color": "#16a34a", "align": "center"}},
                {{"action": "draw_text_box", "text": "☀️ Sunlight", "x_percent": 20, "y_percent": 40, "width_percent": 20, "height": 60, "color": "#fef3c7", "stroke": "#f59e0b"}},
                {{"action": "draw_text_box", "text": "💧 Water", "x_percent": 50, "y_percent": 40, "width_percent": 20, "height": 60, "color": "#dbeafe", "stroke": "#3b82f6"}},
                {{"action": "draw_text_box", "text": "🌫️ CO₂", "x_percent": 80, "y_percent": 40, "width_percent": 20, "height": 60, "color": "#e0e7ff", "stroke": "#6366f1"}}
            ]
        }},
        {{
            "type": "explanation_step",
            "text_explanation": "Here's the chemical equation: 6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂",
            "tts_text": "The chemical equation shows that six molecules of carbon dioxide plus six molecules of water, using light energy, produce one molecule of glucose and six molecules of oxygen.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "The Chemical Equation", "x_percent": 50, "y_percent": 15, "font_size": 28, "color": "#16a34a", "align": "center"}},
                {{"action": "draw_equation", "latex": "6CO_2 + 6H_2O + \\\\text{{Light}} \\\\rightarrow C_6H_{{12}}O_6 + 6O_2", "x_percent": 50, "y_percent": 45, "font_size": 24}},
                {{"action": "write_text", "text": "Glucose (Food) + Oxygen", "x_percent": 50, "y_percent": 70, "font_size": 20, "color": "#6b7280", "align": "center"}}
            ]
        }}
    ],
    "images": []
}}

Now generate teaching sequence for the given topic and lesson content. Return ONLY valid JSON.
"""

async def generate_visualization_v2(lesson_content: str, topic: str, images_info: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate Konva.js-compatible teaching sequence with whiteboard commands
    """
    if not GEMINI_MODEL:
        logger.warning("Gemini not available, using fallback")
        return generate_fallback_visualization_v2(topic)
    
    try:
        # Prepare images info
        images_summary = []
        if images_info:
            images_summary = [{"id": img.get("id"), "description": img.get("description", "")} for img in images_info]
        
        # Build prompt
        prompt = WHITEBOARD_VISUALIZATION_PROMPT.format(
            topic=topic,
            lesson_content=lesson_content[:3000],
            images_info=json.dumps(images_summary)
        )
        
        # Generate with Gemini
        logger.info(f"🎨 Generating Konva.js visualization for topic: {topic}")
        response = GEMINI_MODEL.generate_content(
            prompt,
            generation_config={
                "temperature": 0.5,
                "max_output_tokens": 8000,
            }
        )
        
        # Extract JSON
        response_text = response.candidates[0].content.parts[0].text
        logger.info(f"📝 LLM Response length: {len(response_text)} chars")
        
        # Parse JSON (handle markdown code blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
        
        if json_match:
            viz_data = json.loads(json_match.group(1))
            
            # Validate with Pydantic
            validated = VisualizationDataV2(**viz_data)
            logger.info(f"✅ Generated {len(validated.teaching_sequence)} teaching steps")
            
            return validated.dict()
        else:
            logger.error("❌ Could not extract JSON from response")
            return generate_fallback_visualization_v2(topic)
            
    except Exception as e:
        logger.error(f"❌ Visualization generation failed: {e}")
        return generate_fallback_visualization_v2(topic)

def generate_fallback_visualization_v2(topic: str) -> Dict[str, Any]:
    """Fallback visualization when AI generation fails"""
    return {
        "teaching_sequence": [
            {
                "type": "explanation_start",
                "text_explanation": f"Welcome to the lesson on {topic}!",
                "tts_text": f"Welcome! Let's begin learning about {topic}.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": topic, "x_percent": 50, "y_percent": 40, "font_size": 48, "color": "#1e40af", "align": "center"},
                    {"action": "write_text", "text": "Interactive Lesson", "x_percent": 50, "y_percent": 55, "font_size": 24, "color": "#6b7280", "align": "center"}
                ]
            },
            {
                "type": "explanation_step",
                "text_explanation": "Let's explore this topic together with visual aids and explanations.",
                "tts_text": "Let's explore this topic together. Pay attention to the visual explanations.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": "Key Concepts", "x_percent": 50, "y_percent": 30, "font_size": 36, "color": "#1e40af", "align": "center"},
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 60, "radius": 80, "fill": "#dbeafe", "stroke": "#3b82f6"}
                ]
            }
        ],
        "images": []
    }

# ==================== DEDICATED VISUALIZATION LLM ====================
async def generate_visualization_with_llm(topic: str, explanation: str, lesson_content: str) -> List[Dict[str, Any]]:
    """
    🎨 DEDICATED LLM CALL FOR EXTRAORDINARY VISUALIZATIONS
    
    This function ONLY focuses on creating amazing, topic-specific visualizations.
    The lesson service handles educational content, this handles visual excellence.
    
    Returns: List of visualization scenes with icons, images, subject-specific shapes
    """
    if not GEMINI_MODEL:
        logger.warning("⚠️ Gemini not available, using fallback visualization")
        return _generate_fallback_visualization(topic, explanation)
    
    try:
        logger.info(f"🎨 Generating extraordinary visualization for: {topic}")
        
        # VISUALIZATION-FOCUSED PROMPT (No educational content generation)
        prompt = f"""You are an EXTRAORDINARY VISUALIZATION EXPERT. Create stunning, topic-specific visualizations that make learning intuitive and beautiful.

TOPIC: {topic}

LESSON CONTENT:
{lesson_content[:2000]}

EXPLANATION:
{explanation[:500]}

YOUR TASK: Generate ONLY visualization JSON (NO educational content). Focus on:

1. **SUBJECT-SPECIFIC SHAPES**: Real diagrams, not generic rectangles
   - Biology: Leaf paths, chloroplast structures, cell organelles, DNA helixes
   - Physics/Electronics: Battery icons, resistor zigzags, circuit paths, wave patterns
   - Chemistry: Molecule structures (H2O with angle), beaker/flask shapes, electron orbits
   - Computer Science: CPU diagrams, binary flows, network topologies
   - Mathematics: Coordinate axes, parabola curves, geometric proofs

2. **ICONS** (14 available): sun, leaf, battery, molecule, atom, beaker, flask, lightbulb, cpu, heart, tree, cloud, water-droplet, lightning
   Example: {{"type": "icon", "name": "leaf", "x": 100, "y": 100, "width": 80, "height": 80, "fill": "#2ecc71"}}

3. **IMAGES** for complex shapes (use placeholder format):
   Example: {{"type": "image", "src": "https://via.placeholder.com/200x200?text=Chloroplast+Structure", "x": 300, "y": 300, "width": 200, "height": 200}}

4. **PATHS** for custom shapes (SVG path data):
   Example: {{"type": "path", "data": "M 10,30 A 20,20 0,0,1 50,30", "stroke": "#3498db", "strokeWidth": 3}}

5. **ANIMATIONS** (GSAP): fadeIn, draw, move, pulse, glow, rotate, scale, orbit
   Example: {{"shape_index": 0, "type": "fadeIn", "duration": 1.5, "delay": 0}}

6. **COLORS**: Topic-appropriate palettes
   - Biology: Greens (#2ecc71, #27ae60), Blues (water), Yellows (sun)
   - Physics: Blues/Purples (#3498db, #9b59b6), Grays (conductors)
   - Chemistry: Blues (#3498db), Reds (#e74c3c), Grays (#95a5a6)

IMPORTANT:
- First scene: "intro" - Overview with key visual elements
- Remaining scenes: Specific concepts with animations
- Use icons for simple symbols (sun, leaf, battery)
- Use images for complex structures (chloroplast, transistor, DNA)
- Use paths for custom shapes (resistor zigzag, parabola curves)
- Each scene 10-20 seconds duration
- Animations should reveal content progressively (fadeIn → draw → move)

Return ONLY JSON array of scenes:
```json
[
  {{
    "scene_id": "intro",
    "title": "Introduction",
    "duration": 15.0,
    "shapes": [
      {{"type": "icon", "name": "leaf", "x": 400, "y": 300, "width": 120, "height": 120, "fill": "#2ecc71"}},
      {{"type": "icon", "name": "sun", "x": 800, "y": 200, "width": 100, "height": 100, "fill": "#f39c12"}},
      {{"type": "image", "src": "https://via.placeholder.com/250x250?text=Chloroplast+with+Grana", "x": 600, "y": 400, "width": 250, "height": 250}},
      {{"type": "arrow", "points": [400, 400, 600, 450], "stroke": "#3498db", "strokeWidth": 3}}
    ],
    "animations": [
      {{"shape_index": 0, "type": "fadeIn", "duration": 1.5}},
      {{"shape_index": 1, "type": "pulse", "duration": 2, "repeat": -1}},
      {{"shape_index": 2, "type": "fadeIn", "duration": 2, "delay": 1}},
      {{"shape_index": 3, "type": "draw", "duration": 1.5, "delay": 2}}
    ],
    "audio": {{
      "text": "Photosynthesis: how plants convert sunlight into energy",
      "start_time": 0,
      "duration": 15
    }}
  }},
  ... more scenes ...
]
```

Generate 3-5 scenes with extraordinary, topic-specific visualizations."""

        # Call Gemini
        response = GEMINI_MODEL.generate_content(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 8000,
            }
        )
        
        # Extract JSON from response
        response_text = response.candidates[0].content.parts[0].text
        logger.info(f"🎨 LLM Response length: {len(response_text)} chars")
        
        # Extract JSON array from markdown code blocks or raw text
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'(\[.*?\])', response_text, re.DOTALL)
        
        if json_match:
            scenes_data = json.loads(json_match.group(1))
            logger.info(f"✅ Generated {len(scenes_data)} extraordinary visualization scenes")
            return scenes_data
        else:
            logger.error("❌ Could not extract JSON from LLM response")
            return _generate_fallback_visualization(topic, explanation)
            
    except Exception as e:
        logger.error(f"❌ LLM visualization generation failed: {e}")
        return _generate_fallback_visualization(topic, explanation)

def _generate_fallback_visualization(topic: str, explanation: str) -> List[Dict[str, Any]]:
    """Fallback visualization when LLM fails"""
    logger.info(f"📦 Using fallback visualization for: {topic}")
    
    return [
        {
            "scene_id": "intro",
            "title": "Introduction",
            "duration": 15.0,
            "shapes": [
                {"type": "circle", "x": 960, "y": 540, "radius": 150, "fill": "#3498db", "stroke": "#2980b9", "strokeWidth": 3},
                {"type": "text", "x": 960, "y": 540, "text": topic, "fontSize": 32, "fill": "white", "align": "center"}
            ],
            "animations": [
                {"shape_index": 0, "type": "fadeIn", "duration": 2.0},
                {"shape_index": 1, "type": "fadeIn", "duration": 2.0, "delay": 0.5}
            ],
            "audio": {
                "text": f"Let's learn about {topic}",
                "start_time": 0,
                "duration": 15
            }
        }
    ]

@app.post("/api/visualizations/process", response_model=VisualizationResponseModel)
async def process_visualization(viz_request: VisualizationRequestModel):
    """
    🎨 TWO-STAGE ARCHITECTURE: Visualization Service with Dedicated LLM
    
    1. Receives lesson content from Lesson Service (educational content already generated)
    2. Calls dedicated Gemini LLM to generate EXTRAORDINARY visualizations
    3. Validates, sequences, and optimizes visualization with perfect coordinates
    4. Returns optimized visualization data to Teaching Service
    """
    try:
        logger.info(f"📥 Received visualization request for lesson: {viz_request.lesson_id}")
        logger.info(f"🎯 Topic: {viz_request.topic}")
        
        # 🎨 STAGE 1: Generate extraordinary visualizations with dedicated LLM
        logger.info("🎨 Calling dedicated LLM for visualization generation...")
        llm_generated_scenes = await generate_visualization_with_llm(
            topic=viz_request.topic,
            explanation=viz_request.explanation,
            lesson_content=viz_request.explanation[:3000]  # Pass lesson context
        )
        
        # Replace original scenes with LLM-generated extraordinary visualizations
        viz_request.scenes = []
        for scene_data in llm_generated_scenes:
            try:
                viz_request.scenes.append(VisualizationSceneModel(**scene_data))
            except Exception as e:
                logger.warning(f"⚠️ Scene validation failed: {e}, using raw data")
                # If validation fails, keep raw data for processor to handle
        
        if not viz_request.scenes and llm_generated_scenes:
            # Fallback: use raw scene data
            logger.info("📦 Using raw scene data from LLM")
        
        # 🎨 STAGE 2: Process and validate visualization (coordinate management, overlap prevention)
        logger.info("🔧 Processing and optimizing visualization...")
        processed_data = processor.process_visualization(viz_request)
        
        # Generate visualization ID
        viz_id = f"viz_{viz_request.lesson_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Store in database
        viz_document = {
            "visualization_id": viz_id,
            "lesson_id": viz_request.lesson_id,
            "topic": viz_request.topic,
            "explanation": viz_request.explanation,
            "session_id": viz_request.session_id,
            "status": "processed",
            "scenes": processed_data["scenes"],
            "total_duration": processed_data["total_duration"],
            "canvas": processed_data["canvas"],
            "errors": processed_data["errors"],
            "warnings": processed_data["warnings"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await visualization_db.visualizations.insert_one(viz_document)
        logger.info(f"✅ Stored visualization: {viz_id}")
        
        # Notify Teaching Service via WebSocket if session_id provided
        if viz_request.session_id and viz_request.session_id in manager.active_connections:
            await manager.send_message(viz_request.session_id, {
                "type": "visualization_ready",
                "visualization_id": viz_id,
                "lesson_id": viz_request.lesson_id
            })
        
        return VisualizationResponseModel(
            visualization_id=viz_id,
            lesson_id=viz_request.lesson_id,
            status="processed",
            scenes=processed_data["scenes"],
            total_duration=processed_data["total_duration"],
            created_at=viz_document["created_at"],
            errors=processed_data["errors"],
            warnings=processed_data["warnings"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualizations/{visualization_id}")
async def get_visualization(visualization_id: str):
    """Retrieve processed visualization by ID"""
    try:
        viz = await visualization_db.visualizations.find_one({"visualization_id": visualization_id})
        
        if not viz:
            raise HTTPException(status_code=404, detail="Visualization not found")
        
        # Convert ObjectId to string
        viz["_id"] = str(viz["_id"])
        return viz
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualizations/lesson/{lesson_id}")
async def get_visualizations_by_lesson(lesson_id: str):
    """Get all visualizations for a specific lesson"""
    try:
        cursor = visualization_db.visualizations.find({"lesson_id": lesson_id})
        visualizations = await cursor.to_list(length=100)
        
        for viz in visualizations:
            viz["_id"] = str(viz["_id"])
        
        return {"lesson_id": lesson_id, "visualizations": visualizations}
        
    except Exception as e:
        logger.error(f"Error retrieving visualizations for lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/visualization/v2/{lesson_id}")
async def get_visualization_v2(lesson_id: str):
    """
    Get visualization in new Konva.js whiteboard format
    Returns teaching_sequence with whiteboard commands
    """
    try:
        logger.info(f"Fetching v2 visualization for lesson: {lesson_id}")
        
        # Try to get existing visualization from database
        viz = await visualization_db.visualizations_v2.find_one({"lesson_id": lesson_id})
        
        if viz:
            viz["_id"] = str(viz["_id"])
            logger.info(f"✅ Found existing v2 visualization")
            return viz
        
        # If not found, generate new one
        logger.info(f"No existing v2 visualization, generating new one...")
        
        # Get lesson data from lesson service
        try:
            lesson_response = await asyncio.to_thread(
                lambda: __import__('requests').get(f"http://localhost:8003/api/lessons/{lesson_id}")
            )
            if lesson_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Lesson not found")
            
            response_data = lesson_response.json()
            # Response structure: { success: true, lesson: {...} }
            lesson_data = response_data.get('lesson', response_data)
            
            # Get lesson content and metadata
            lesson_content = lesson_data.get('lesson_content', lesson_data.get('content', ''))
            topic = lesson_data.get('lesson_title', lesson_data.get('title', 'Educational Topic'))
            images = lesson_data.get('pdf_images', [])
            
        except Exception as e:
            logger.error(f"Failed to fetch lesson data: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch lesson data")
        
        # Generate visualization v2
        viz_data = await generate_visualization_v2(lesson_content, topic, images)
        
        # Store in database
        viz_doc = {
            "lesson_id": lesson_id,
            "teaching_sequence": viz_data['teaching_sequence'],
            "images": viz_data.get('images', []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = await visualization_db.visualizations_v2.insert_one(viz_doc)
        viz_doc["_id"] = str(result.inserted_id)
        
        logger.info(f"✅ Generated and stored v2 visualization")
        return viz_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_visualization_v2: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/visualization/{session_id}")
async def visualization_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time visualization streaming
    Used by Teaching Service to receive visualization updates
    """
    await manager.connect(session_id, websocket)
    
    try:
        while True:
            # Receive messages from Teaching Service
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
            elif message_type == "request_visualization":
                lesson_id = data.get("lesson_id")
                # Fetch and send visualization
                viz = await visualization_db.visualizations.find_one({"lesson_id": lesson_id})
                if viz:
                    viz["_id"] = str(viz["_id"])
                    await websocket.send_json({"type": "visualization_data", "data": viz})
                else:
                    await websocket.send_json({"type": "error", "message": "Visualization not found"})
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

# ==================== Main ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
