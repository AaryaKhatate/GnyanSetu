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

import sys
import os

# Force UTF-8 encoding for Windows console - MUST BE BEFORE ANY OTHER IMPORTS
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Literal, TYPE_CHECKING
from enum import Enum
import json
import logging
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from collections import defaultdict
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
VISUALIZATION_DB_NAME = "visualization_db"
PORT = 8006

# Gemini AI Configuration for Visualization Generation
# Use the SAME API key as lesson service
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY environment variable is not set!")
    logger.error("Please set GEMINI_API_KEY in your .env file or environment variables")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use gemini-2.0-flash-exp for fast, efficient generation
    GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info(" Gemini AI configured for visualization generation")
else:
    GEMINI_MODEL = None
    logger.warning(" Gemini API key not found - visualization generation will use fallback")

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
        logger.info(f" Connected to MongoDB: {VISUALIZATION_DB_NAME}")
        
    except Exception as e:
        logger.error(f" Failed to connect to MongoDB: {e}")
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

OUTPUT: Generate a JSON object with 4-6 step-by-step teaching sequence using whiteboard commands.

CRITICAL RULES:
1. Each step MUST have BOTH visual elements AND detailed narration
2. Use LOTS of text to explain concepts (not just labels)
3. Build progressively - each step adds to previous (don't always clear_all)
4. Keep it EDUCATIONAL - explain WHY and HOW, not just WHAT

WHITEBOARD COMMANDS AVAILABLE:
1. clear_all - Clear the canvas
   {{"action": "clear_all"}}

2. write_text - Display text at position (percentage-based, 0-100)
   {{"action": "write_text", "text": "...", "x_percent": 50, "y_percent": 20, "font_size": 30, "color": "#1e40af", "align": "center"}}
   - x_percent: 0 = left edge, 50 = center, 100 = right edge
   - y_percent: 0 = top edge, 50 = middle, 100 = bottom edge
   - align: "left", "center", or "right"

3. draw_text_box - Text in colored box
   {{"action": "draw_text_box", "text": "...", "x_percent": 30, "y_percent": 40, "width_percent": 25, "height": 80, "color": "#bfdbfe", "stroke": "#60a5fa"}}
   - width_percent: 15-30 recommended (percentage of canvas width)
   - Position is CENTER of the box

4. draw_circle - Circle shape
   {{"action": "draw_circle", "x_percent": 50, "y_percent": 50, "radius": 40, "fill": "#dcfce7", "stroke": "#10b981", "stroke_width": 3}}

5. draw_rectangle - Rectangle
   {{"action": "draw_rectangle", "x_percent": 40, "y_percent": 40, "width_percent": 20, "height": 80, "fill": "#fee2e2", "stroke": "#ef4444", "stroke_width": 2}}
   - Position is CENTER of the rectangle

6. draw_line - Connect points
   {{"action": "draw_line", "points_percent": [[10,20], [90,20]], "stroke": "#374151", "stroke_width": 3}}
   - Each point is [x_percent, y_percent]

7. draw_arrow - Arrow with direction
   {{"action": "draw_arrow", "from_percent": [20,50], "to_percent": [80,50], "color": "#065f46", "thickness": 3}}
   - from_percent and to_percent are [x_percent, y_percent]

8. draw_image - Display extracted PDF image
   {{"action": "draw_image", "image_id": "pdf_img_0", "x_percent": 50, "y_percent": 50, "scale": 0.8}}

COORDINATE SYSTEM - SAFE ZONES:
- Canvas is 1920x1080 pixels (16:9 aspect ratio)
- Use percentage coordinates (0-100) for x_percent and y_percent
- SAFE ZONES for readable content:
  * Top title area: y_percent 8-15
  * Subtitle area: y_percent 18-25
  * Main content area: y_percent 30-75
  * Bottom notes area: y_percent 80-92
- HORIZONTAL LAYOUT:
  * Left column: x_percent 10-30
  * Center column: x_percent 40-60
  * Right column: x_percent 70-90
- Leave margins: Don't use x_percent < 5 or > 95, y_percent < 5 or > 95

TEACHING SEQUENCE STRUCTURE:
1. Start with "explanation_start" - Title + Introduction (MUST have text explanation)
2. Create 3-5 "explanation_step" entries (each MUST explain a concept)
3. End with "explanation_end" - Summary + Key Takeaways
4. Each step should:
   - Have 4-8 visual elements (mix of text, shapes, arrows)
   - Include LOTS of explanatory text (not just labels)
   - Build on previous step when possible
   - Provide detailed narration (2-4 sentences minimum)
   - Focus on TEACHING, not just showing

EXAMPLE OUTPUT (Photosynthesis):
{{
    "teaching_sequence": [
        {{
            "type": "explanation_start",
            "text_explanation": "Today we'll learn about Photosynthesis - the process by which plants make their own food using sunlight.",
            "tts_text": "Hello! Welcome to our lesson on photosynthesis. This is one of the most important processes in nature. Let's explore how plants create food from sunlight, water, and carbon dioxide.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "🌿 Photosynthesis", "x_percent": 50, "y_percent": 12, "font_size": 54, "color": "#16a34a", "align": "center"}},
                {{"action": "write_text", "text": "How Plants Make Food", "x_percent": 50, "y_percent": 20, "font_size": 26, "color": "#6b7280", "align": "center"}},
                {{"action": "write_text", "text": "The process that powers nearly all life on Earth", "x_percent": 50, "y_percent": 35, "font_size": 22, "color": "#374151", "align": "center"}},
                {{"action": "draw_circle", "x_percent": 15, "y_percent": 60, "radius": 55, "fill": "#fef3c7", "stroke": "#f59e0b", "stroke_width": 3}},
                {{"action": "write_text", "text": "Sunlight", "x_percent": 15, "y_percent": 60, "font_size": 20, "color": "#92400e", "align": "center"}},
                {{"action": "draw_circle", "x_percent": 50, "y_percent": 60, "radius": 55, "fill": "#dbeafe", "stroke": "#3b82f6", "stroke_width": 3}},
                {{"action": "write_text", "text": "Water", "x_percent": 50, "y_percent": 60, "font_size": 20, "color": "#1e40af", "align": "center"}},
                {{"action": "draw_circle", "x_percent": 85, "y_percent": 60, "radius": 55, "fill": "#e0e7ff", "stroke": "#6366f1", "stroke_width": 3}},
                {{"action": "write_text", "text": "CO₂", "x_percent": 85, "y_percent": 60, "font_size": 20, "color": "#3730a3", "align": "center"}},
                {{"action": "write_text", "text": "The Three Essential Ingredients", "x_percent": 50, "y_percent": 85, "font_size": 24, "color": "#059669", "align": "center"}}
            ]
        }},
        {{
            "type": "explanation_step",
            "text_explanation": "Photosynthesis occurs in special cell structures called chloroplasts. Chloroplasts contain chlorophyll, the green pigment that captures sunlight energy.",
            "tts_text": "Now let's look inside a plant cell. Photosynthesis takes place in tiny green structures called chloroplasts. These chloroplasts contain chlorophyll, which is what makes plants green and allows them to capture energy from sunlight.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "Where Does It Happen?", "x_percent": 50, "y_percent": 12, "font_size": 44, "color": "#16a34a", "align": "center"}},
                {{"action": "draw_circle", "x_percent": 50, "y_percent": 50, "radius": 180, "fill": "#dcfce7", "stroke": "#22c55e", "stroke_width": 4}},
                {{"action": "write_text", "text": "Chloroplast", "x_percent": 50, "y_percent": 28, "font_size": 28, "color": "#15803d", "align": "center"}},
                {{"action": "draw_circle", "x_percent": 42, "y_percent": 48, "radius": 32, "fill": "#86efac", "stroke": "#16a34a", "stroke_width": 3}},
                {{"action": "draw_circle", "x_percent": 58, "y_percent": 48, "radius": 32, "fill": "#86efac", "stroke": "#16a34a", "stroke_width": 3}},
                {{"action": "draw_circle", "x_percent": 42, "y_percent": 58, "radius": 32, "fill": "#86efac", "stroke": "#16a34a", "stroke_width": 3}},
                {{"action": "draw_circle", "x_percent": 58, "y_percent": 58, "radius": 32, "fill": "#86efac", "stroke": "#16a34a", "stroke_width": 3}},
                {{"action": "write_text", "text": "Thylakoids", "x_percent": 50, "y_percent": 75, "font_size": 22, "color": "#15803d", "align": "center"}},
                {{"action": "write_text", "text": "(Stack of membranes where light reactions occur)", "x_percent": 50, "y_percent": 82, "font_size": 18, "color": "#6b7280", "align": "center"}},
                {{"action": "write_text", "text": "Chlorophyll molecules capture sunlight here!", "x_percent": 50, "y_percent": 90, "font_size": 20, "color": "#059669", "align": "center"}}
            ]
        }},
        {{
            "type": "explanation_step",
            "text_explanation": "The chemical equation for photosynthesis is: 6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂. This shows how carbon dioxide and water are converted into glucose and oxygen.",
            "tts_text": "Here's the chemical equation that describes photosynthesis. Six molecules of carbon dioxide combine with six molecules of water. Using energy from sunlight, these are transformed into one molecule of glucose, which is the food for the plant, plus six molecules of oxygen, which is released into the air.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "The Chemical Equation", "x_percent": 50, "y_percent": 10, "font_size": 44, "color": "#16a34a", "align": "center"}},
                {{"action": "draw_text_box", "text": "6 CO₂", "x_percent": 15, "y_percent": 35, "width_percent": 14, "height": 70, "color": "#e0e7ff", "stroke": "#6366f1", "font_size": 24}},
                {{"action": "write_text", "text": "+", "x_percent": 25, "y_percent": 35, "font_size": 36, "color": "#6b7280", "align": "center"}},
                {{"action": "draw_text_box", "text": "6 H₂O", "x_percent": 32, "y_percent": 35, "width_percent": 14, "height": 70, "color": "#dbeafe", "stroke": "#3b82f6", "font_size": 24}},
                {{"action": "write_text", "text": "+", "x_percent": 42, "y_percent": 35, "font_size": 36, "color": "#6b7280", "align": "center"}},
                {{"action": "draw_text_box", "text": "☀️ Light", "x_percent": 50, "y_percent": 35, "width_percent": 14, "height": 70, "color": "#fef3c7", "stroke": "#f59e0b", "font_size": 22}},
                {{"action": "draw_arrow", "from_percent": [60, 35], "to_percent": [72, 35], "color": "#16a34a", "thickness": 5}},
                {{"action": "draw_text_box", "text": "C₆H₁₂O₆", "x_percent": 85, "y_percent": 28, "width_percent": 16, "height": 70, "color": "#dcfce7", "stroke": "#22c55e", "font_size": 22}},
                {{"action": "write_text", "text": "+", "x_percent": 85, "y_percent": 42, "font_size": 32, "color": "#6b7280", "align": "center"}},
                {{"action": "draw_text_box", "text": "6 O₂", "x_percent": 85, "y_percent": 50, "width_percent": 16, "height": 60, "color": "#dbeafe", "stroke": "#3b82f6", "font_size": 24}},
                {{"action": "write_text", "text": "Glucose (Food for plant)", "x_percent": 85, "y_percent": 65, "font_size": 18, "color": "#15803d", "align": "center"}},
                {{"action": "write_text", "text": "Oxygen (Released to air)", "x_percent": 85, "y_percent": 70, "font_size": 18, "color": "#0369a1", "align": "center"}},
                {{"action": "write_text", "text": "This reaction captures energy from the Sun and stores it in chemical bonds", "x_percent": 50, "y_percent": 88, "font_size": 20, "color": "#374151", "align": "center"}}
            ]
        }},
        {{
            "type": "explanation_end",
            "text_explanation": "Summary: Photosynthesis is how plants convert light energy into chemical energy stored in glucose. This process provides food for plants and oxygen for all living things.",
            "tts_text": "To summarize what we've learned: Photosynthesis is the remarkable process where plants use sunlight, water, and carbon dioxide to create glucose and release oxygen. This process is essential for life on Earth, providing food for plants and oxygen for animals and humans to breathe.",
            "whiteboard_commands": [
                {{"action": "clear_all"}},
                {{"action": "write_text", "text": "Key Takeaways 🎯", "x_percent": 50, "y_percent": 10, "font_size": 48, "color": "#16a34a", "align": "center"}},
                {{"action": "draw_text_box", "text": "1. Chloroplasts capture sunlight", "x_percent": 50, "y_percent": 30, "width_percent": 70, "height": 65, "color": "#dbeafe", "stroke": "#3b82f6", "font_size": 22}},
                {{"action": "draw_text_box", "text": "2. Converts CO₂ + H₂O into Glucose + O₂", "x_percent": 50, "y_percent": 45, "width_percent": 70, "height": 65, "color": "#fef3c7", "stroke": "#f59e0b", "font_size": 22}},
                {{"action": "draw_text_box", "text": "3. Powers nearly all life on Earth!", "x_percent": 50, "y_percent": 60, "width_percent": 70, "height": 65, "color": "#dcfce7", "stroke": "#22c55e", "font_size": 22}},
                {{"action": "write_text", "text": "Without photosynthesis, there would be no food or oxygen!", "x_percent": 50, "y_percent": 78, "font_size": 24, "color": "#dc2626", "align": "center"}},
                {{"action": "write_text", "text": "🌍 Plants are the foundation of life on Earth 🌱", "x_percent": 50, "y_percent": 90, "font_size": 26, "color": "#059669", "align": "center"}}
            ]
        }}
    ],
    "images": []
}}

IMPORTANT GUIDELINES:
- Generate 4-6 steps total (intro + 2-4 middle steps + conclusion)
- Each step MUST have educational value and teach something new
- Use descriptive text extensively - explain concepts clearly
- TTS text should be 2-4 sentences that a teacher would say
- Build progressively - show how concepts connect
- Use appropriate colors for the subject matter
- Keep coordinates within safe zones

Now generate a comprehensive teaching sequence for the given topic. Return ONLY valid JSON.
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
        
        # Generate with Gemini with retry logic for quota errors
        logger.info(f"🎨 Generating Konva.js visualization for topic: {topic}")
        
        max_retries = 2
        retry_delay = 20  # seconds
        
        for attempt in range(max_retries):
            try:
                response = GEMINI_MODEL.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.5,
                        "max_output_tokens": 8000,
                    }
                )
                
                # Extract JSON
                response_text = response.candidates[0].content.parts[0].text
                logger.info(f"✅ LLM Response length: {len(response_text)} chars")
                
                # Parse JSON (handle markdown code blocks)
                # Use greedy matching for proper nested JSON handling
                json_match = re.search(r'```json\s*(\{.*\})\s*```', response_text, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                
                if json_match:
                    try:
                        viz_data = json.loads(json_match.group(1))
                        
                        # Validate with Pydantic
                        validated = VisualizationDataV2(**viz_data)
                        logger.info(f"✅ Generated {len(validated.teaching_sequence)} teaching steps")
                        
                        return validated.dict()
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parsing failed: {e}")
                        logger.error(f"Response excerpt: {response_text[:500]}")
                        return generate_fallback_visualization_v2(topic)
                    except Exception as e:
                        logger.error(f"❌ Validation failed: {e}")
                        return generate_fallback_visualization_v2(topic)
                else:
                    logger.error("❌ Could not extract JSON from response")
                    return generate_fallback_visualization_v2(topic)
                    
            except Exception as api_error:
                error_str = str(api_error)
                
                # Check if it's a quota error
                if '429' in error_str or 'quota' in error_str.lower():
                    logger.warning(f"⚠️ Quota exceeded (attempt {attempt + 1}/{max_retries})")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.warning("⚠️ Max retries reached, using fallback visualization")
                        return generate_fallback_visualization_v2(topic)
                else:
                    # Other error, don't retry
                    raise api_error
            
    except Exception as e:
        logger.error(f"❌ Visualization generation failed: {e}")
        return generate_fallback_visualization_v2(topic)

def generate_fallback_visualization_v2(topic: str) -> Dict[str, Any]:
    """Enhanced fallback visualization when AI generation fails"""
    logger.info(f"🔄 Using enhanced fallback visualization for: {topic}")
    
    # Create a comprehensive 6-step lesson structure
    return {
        "teaching_sequence": [
            {
                "type": "explanation_start",
                "text_explanation": f"Welcome to the interactive lesson on {topic}!",
                "tts_text": f"Welcome! Today we'll explore {topic} with visual explanations and interactive elements.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    # Title
                    {"action": "write_text", "text": topic, "x_percent": 50, "y_percent": 15, "font_size": 56, "color": "#1e40af", "align": "center"},
                    # Subtitle
                    {"action": "write_text", "text": "Interactive Learning Experience", "x_percent": 50, "y_percent": 25, "font_size": 28, "color": "#6b7280", "align": "center"},
                    # Decorative elements
                    {"action": "draw_rectangle", "x_percent": 50, "y_percent": 20, "width_percent": 60, "height": 3, "fill": "#3b82f6", "stroke": "#3b82f6"},
                    # Main content box
                    {"action": "draw_text_box", "text": "Let's Begin!", "x_percent": 50, "y_percent": 50, "width_percent": 50, "height": 80, "color": "#dbeafe", "stroke": "#3b82f6"},
                    # Icon indicators
                    {"action": "draw_circle", "x_percent": 20, "y_percent": 70, "radius": 40, "fill": "#fef3c7", "stroke": "#f59e0b"},
                    {"action": "write_text", "text": "Learn", "x_percent": 20, "y_percent": 70, "font_size": 18, "color": "#92400e", "align": "center"},
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 70, "radius": 40, "fill": "#dbeafe", "stroke": "#3b82f6"},
                    {"action": "write_text", "text": "Explore", "x_percent": 50, "y_percent": 70, "font_size": 18, "color": "#1e40af", "align": "center"},
                    {"action": "draw_circle", "x_percent": 80, "y_percent": 70, "radius": 40, "fill": "#d1fae5", "stroke": "#10b981"},
                    {"action": "write_text", "text": "Practice", "x_percent": 80, "y_percent": 70, "font_size": 18, "color": "#065f46", "align": "center"}
                ]
            },
            {
                "type": "explanation_step",
                "text_explanation": f"Introduction to {topic}: Understanding the fundamentals and core concepts.",
                "tts_text": f"Let's start by understanding what {topic} is all about and why it's important.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    # Section title
                    {"action": "write_text", "text": "What is it?", "x_percent": 50, "y_percent": 12, "font_size": 42, "color": "#1e40af", "align": "center"},
                    # Main definition box
                    {"action": "draw_text_box", "text": "Core Concept", "x_percent": 50, "y_percent": 35, "width_percent": 70, "height": 120, "color": "#eff6ff", "stroke": "#3b82f6"},
                    # Key points
                    {"action": "draw_circle", "x_percent": 15, "y_percent": 60, "radius": 8, "fill": "#3b82f6", "stroke": "#3b82f6"},
                    {"action": "write_text", "text": "Fundamental Principles", "x_percent": 20, "y_percent": 60, "font_size": 22, "color": "#1f2937"},
                    {"action": "draw_circle", "x_percent": 15, "y_percent": 70, "radius": 8, "fill": "#3b82f6", "stroke": "#3b82f6"},
                    {"action": "write_text", "text": "Key Components", "x_percent": 20, "y_percent": 70, "font_size": 22, "color": "#1f2937"},
                    {"action": "draw_circle", "x_percent": 15, "y_percent": 80, "radius": 8, "fill": "#3b82f6", "stroke": "#3b82f6"},
                    {"action": "write_text", "text": "Practical Applications", "x_percent": 20, "y_percent": 80, "font_size": 22, "color": "#1f2937"}
                ]
            },
            {
                "type": "explanation_step",
                "text_explanation": f"Key components and important elements of {topic}.",
                "tts_text": "Now let's examine the key components and how they work together.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": "Key Components", "x_percent": 50, "y_percent": 12, "font_size": 42, "color": "#7c3aed", "align": "center"},
                    # Component boxes
                    {"action": "draw_text_box", "text": "Component 1", "x_percent": 25, "y_percent": 40, "width_percent": 30, "height": 100, "color": "#fef3c7", "stroke": "#f59e0b"},
                    {"action": "draw_text_box", "text": "Component 2", "x_percent": 75, "y_percent": 40, "width_percent": 30, "height": 100, "color": "#dbeafe", "stroke": "#3b82f6"},
                    # Connection arrow
                    {"action": "draw_arrow", "from_percent": [40, 40], "to_percent": [60, 40], "color": "#6b7280", "thickness": 3},
                    # Result box
                    {"action": "draw_text_box", "text": "Result", "x_percent": 50, "y_percent": 70, "width_percent": 40, "height": 90, "color": "#d1fae5", "stroke": "#10b981"}
                ]
            },
            {
                "type": "explanation_step",
                "text_explanation": f"How {topic} works: Step-by-step process and mechanisms.",
                "tts_text": "Let's break down the process into simple, easy-to-understand steps.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": "The Process", "x_percent": 50, "y_percent": 12, "font_size": 42, "color": "#059669", "align": "center"},
                    # Step 1
                    {"action": "draw_circle", "x_percent": 20, "y_percent": 35, "radius": 35, "fill": "#fef3c7", "stroke": "#f59e0b"},
                    {"action": "write_text", "text": "1", "x_percent": 20, "y_percent": 35, "font_size": 32, "color": "#92400e", "align": "center"},
                    {"action": "write_text", "text": "Step One", "x_percent": 20, "y_percent": 50, "font_size": 20, "color": "#1f2937", "align": "center"},
                    # Arrow 1
                    {"action": "draw_arrow", "from_percent": [28, 35], "to_percent": [42, 35], "color": "#6b7280", "thickness": 2},
                    # Step 2
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 35, "radius": 35, "fill": "#dbeafe", "stroke": "#3b82f6"},
                    {"action": "write_text", "text": "2", "x_percent": 50, "y_percent": 35, "font_size": 32, "color": "#1e40af", "align": "center"},
                    {"action": "write_text", "text": "Step Two", "x_percent": 50, "y_percent": 50, "font_size": 20, "color": "#1f2937", "align": "center"},
                    # Arrow 2
                    {"action": "draw_arrow", "from_percent": [58, 35], "to_percent": [72, 35], "color": "#6b7280", "thickness": 2},
                    # Step 3
                    {"action": "draw_circle", "x_percent": 80, "y_percent": 35, "radius": 35, "fill": "#d1fae5", "stroke": "#10b981"},
                    {"action": "write_text", "text": "3", "x_percent": 80, "y_percent": 35, "font_size": 32, "color": "#065f46", "align": "center"},
                    {"action": "write_text", "text": "Step Three", "x_percent": 80, "y_percent": 50, "font_size": 20, "color": "#1f2937", "align": "center"},
                    # Summary box
                    {"action": "draw_text_box", "text": "Process Overview", "x_percent": 50, "y_percent": 75, "width_percent": 70, "height": 80, "color": "#f3f4f6", "stroke": "#6b7280"}
                ]
            },
            {
                "type": "explanation_step",
                "text_explanation": f"Practical applications and real-world examples of {topic}.",
                "tts_text": "Let's see how this applies to real-world situations and practical examples.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": "Real-World Applications", "x_percent": 50, "y_percent": 12, "font_size": 42, "color": "#dc2626", "align": "center"},
                    # Example 1
                    {"action": "draw_text_box", "text": "Example 1", "x_percent": 30, "y_percent": 35, "width_percent": 35, "height": 90, "color": "#fef2f2", "stroke": "#dc2626"},
                    {"action": "draw_circle", "x_percent": 30, "y_percent": 30, "radius": 12, "fill": "#dc2626", "stroke": "#dc2626"},
                    # Example 2
                    {"action": "draw_text_box", "text": "Example 2", "x_percent": 70, "y_percent": 35, "width_percent": 35, "height": 90, "color": "#eff6ff", "stroke": "#3b82f6"},
                    {"action": "draw_circle", "x_percent": 70, "y_percent": 30, "radius": 12, "fill": "#3b82f6", "stroke": "#3b82f6"},
                    # Use cases
                    {"action": "draw_text_box", "text": "Common Use Cases", "x_percent": 50, "y_percent": 65, "width_percent": 70, "height": 100, "color": "#fef3c7", "stroke": "#f59e0b"},
                    # Benefit indicators
                    {"action": "draw_circle", "x_percent": 20, "y_percent": 85, "radius": 25, "fill": "#d1fae5", "stroke": "#10b981"},
                    {"action": "write_text", "text": "✓", "x_percent": 20, "y_percent": 85, "font_size": 28, "color": "#065f46", "align": "center"},
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 85, "radius": 25, "fill": "#d1fae5", "stroke": "#10b981"},
                    {"action": "write_text", "text": "✓", "x_percent": 50, "y_percent": 85, "font_size": 28, "color": "#065f46", "align": "center"},
                    {"action": "draw_circle", "x_percent": 80, "y_percent": 85, "radius": 25, "fill": "#d1fae5", "stroke": "#10b981"},
                    {"action": "write_text", "text": "✓", "x_percent": 80, "y_percent": 85, "font_size": 28, "color": "#065f46", "align": "center"}
                ]
            },
            {
                "type": "explanation_end",
                "text_explanation": f"Summary and key takeaways about {topic}. You've completed this lesson!",
                "tts_text": "Great job! Let's recap what we've learned and highlight the key takeaways.",
                "whiteboard_commands": [
                    {"action": "clear_all"},
                    {"action": "write_text", "text": "Summary & Key Takeaways", "x_percent": 50, "y_percent": 10, "font_size": 44, "color": "#7c3aed", "align": "center"},
                    # Trophy/completion icon
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 30, "radius": 50, "fill": "#fef3c7", "stroke": "#f59e0b"},
                    {"action": "write_text", "text": "★", "x_percent": 50, "y_percent": 30, "font_size": 48, "color": "#f59e0b", "align": "center"},
                    # Key points boxes
                    {"action": "draw_text_box", "text": "Key Point 1", "x_percent": 25, "y_percent": 55, "width_percent": 30, "height": 70, "color": "#dbeafe", "stroke": "#3b82f6"},
                    {"action": "draw_text_box", "text": "Key Point 2", "x_percent": 50, "y_percent": 55, "width_percent": 30, "height": 70, "color": "#fef3c7", "stroke": "#f59e0b"},
                    {"action": "draw_text_box", "text": "Key Point 3", "x_percent": 75, "y_percent": 55, "width_percent": 30, "height": 70, "color": "#d1fae5", "stroke": "#10b981"},
                    # Completion message
                    {"action": "draw_text_box", "text": "Lesson Complete! 🎉", "x_percent": 50, "y_percent": 80, "width_percent": 60, "height": 80, "color": "#ede9fe", "stroke": "#7c3aed"},
                    # Progress indicators
                    {"action": "draw_circle", "x_percent": 30, "y_percent": 92, "radius": 8, "fill": "#10b981", "stroke": "#10b981"},
                    {"action": "draw_circle", "x_percent": 40, "y_percent": 92, "radius": 8, "fill": "#10b981", "stroke": "#10b981"},
                    {"action": "draw_circle", "x_percent": 50, "y_percent": 92, "radius": 8, "fill": "#10b981", "stroke": "#10b981"},
                    {"action": "draw_circle", "x_percent": 60, "y_percent": 92, "radius": 8, "fill": "#10b981", "stroke": "#10b981"},
                    {"action": "draw_circle", "x_percent": 70, "y_percent": 92, "radius": 8, "fill": "#10b981", "stroke": "#10b981"}
                ]
            }
        ],
        "images": []
    }

# ==================== DEDICATED VISUALIZATION LLM ====================
async def generate_visualization_with_llm(topic: str, explanation: str, lesson_content: str) -> List[Dict[str, Any]]:
    """
     DEDICATED LLM CALL FOR EXTRAORDINARY VISUALIZATIONS
    
    This function ONLY focuses on creating amazing, topic-specific visualizations.
    The lesson service handles educational content, this handles visual excellence.
    
    Returns: List of visualization scenes with icons, images, subject-specific shapes
    """
    if not GEMINI_MODEL:
        logger.warning(" Gemini not available, using fallback visualization")
        return _generate_fallback_visualization(topic, explanation)
    
    try:
        logger.info(f" Generating extraordinary visualization for: {topic}")
        
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
        logger.info(f" LLM Response length: {len(response_text)} chars")
        
        # Extract JSON array from markdown code blocks or raw text
        # Use greedy matching for proper nested JSON handling
        json_match = re.search(r'```json\s*(\[.*\])\s*```', response_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
        
        if json_match:
            try:
                scenes_data = json.loads(json_match.group(1))
                logger.info(f" Generated {len(scenes_data)} extraordinary visualization scenes")
                return scenes_data
            except json.JSONDecodeError as e:
                logger.error(f" JSON parsing failed: {e}")
                logger.error(f" Response excerpt: {response_text[:500]}")
                return _generate_fallback_visualization(topic, explanation)
        else:
            logger.error(" Could not extract JSON from LLM response")
            return _generate_fallback_visualization(topic, explanation)
            
    except Exception as e:
        logger.error(f" LLM visualization generation failed: {e}")
        return _generate_fallback_visualization(topic, explanation)

def _generate_fallback_visualization(topic: str, explanation: str) -> List[Dict[str, Any]]:
    """Fallback visualization when LLM fails"""
    logger.info(f"� Using fallback visualization for: {topic}")
    
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
   
    Please use GET /visualization/v2/{lesson_id} instead for new whiteboard format.
    
    This endpoint now redirects to v2 format.
    """
    try:
        logger.warning("⚠️ DEPRECATED endpoint /api/visualizations/process called")
        logger.info(f"🔄 Redirecting to v2 format for lesson: {viz_request.lesson_id}")
        
        # Generate v2 visualization instead
        viz_data = await generate_visualization_v2(
            lesson_content=viz_request.explanation,
            topic=viz_request.topic,
            images_info=None
        )
        
        # Store in v2 format
        viz_doc = {
            "lesson_id": viz_request.lesson_id,
            "teaching_sequence": viz_data['teaching_sequence'],
            "images": viz_data.get('images', []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = await visualization_db.visualizations_v2.insert_one(viz_doc)
        viz_id = str(result.inserted_id)
        
        logger.info(f"✅ Generated v2 visualization: {viz_id}")
        
        # Return in old format for compatibility but log warning
        return VisualizationResponseModel(
            visualization_id=viz_id,
            lesson_id=viz_request.lesson_id,
            status="processed",
            scenes=[],  # Empty - use v2 format instead
            total_duration=0,
            created_at=viz_doc["created_at"],
            errors=[],
            warnings=["This endpoint is deprecated. Use GET /visualization/v2/{lesson_id} instead"]
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
            logger.info(f" Found existing v2 visualization")
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
        
        logger.info(f" Generated and stored v2 visualization")
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
