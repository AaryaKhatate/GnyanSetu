"""
GnyanSetu Visualization Orchestrator
====================================
Transforms LLM instructions into perfect visual diagrams with coordinated animations
Handles Konva canvas, GSAP animations, and PixiJS effects with smart coordinate management
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class VisualElementType(Enum):
    """Types of visual elements"""
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    IMAGE = "image"
    PATH = "path"
    GROUP = "group"

class AnimationType(Enum):
    """Types of animations"""
    DRAW = "draw"
    FADE_IN = "fadeIn"
    FADE_OUT = "fadeOut"
    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"
    PULSE = "pulse"
    GLOW = "glow"
    WRITE = "write"

class LayoutZone(Enum):
    """Canvas layout zones for smart positioning"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

@dataclass
class CanvasDimensions:
    """Canvas dimensions and zones"""
    width: int = 1920
    height: int = 1080
    padding: int = 50
    zone_width: int = 580  # (1920 - 2*50 - 2*20) / 3
    zone_height: int = 310  # (1080 - 2*50 - 2*20) / 3

@dataclass
class VisualElement:
    """Represents a visual element to be rendered"""
    id: str
    type: VisualElementType
    zone: LayoutZone
    properties: Dict
    animation: Optional[Dict] = None
    layer: int = 0  # z-index for layering
    sync_audio: bool = False  # Sync with audio narration
    
@dataclass
class VisualizationScene:
    """Complete visualization scene with timing"""
    id: str
    elements: List[VisualElement]
    duration: float  # seconds
    audio_text: str  # Text for TTS narration
    background: Optional[Dict] = None

class CoordinateManager:
    """
    Smart coordinate management to prevent overlap and ensure perfect arrangement
    """
    
    def __init__(self, canvas: CanvasDimensions):
        self.canvas = canvas
        self.occupied_spaces = {zone: [] for zone in LayoutZone}
        
    def get_zone_coordinates(self, zone: LayoutZone) -> Tuple[int, int]:
        """Get base coordinates for a zone"""
        zone_map = {
            LayoutZone.TOP_LEFT: (self.canvas.padding, self.canvas.padding),
            LayoutZone.TOP_CENTER: (self.canvas.padding + self.canvas.zone_width + 20, self.canvas.padding),
            LayoutZone.TOP_RIGHT: (self.canvas.padding + 2 * (self.canvas.zone_width + 20), self.canvas.padding),
            
            LayoutZone.CENTER_LEFT: (self.canvas.padding, self.canvas.padding + self.canvas.zone_height + 20),
            LayoutZone.CENTER: (self.canvas.padding + self.canvas.zone_width + 20, self.canvas.padding + self.canvas.zone_height + 20),
            LayoutZone.CENTER_RIGHT: (self.canvas.padding + 2 * (self.canvas.zone_width + 20), self.canvas.padding + self.canvas.zone_height + 20),
            
            LayoutZone.BOTTOM_LEFT: (self.canvas.padding, self.canvas.padding + 2 * (self.canvas.zone_height + 20)),
            LayoutZone.BOTTOM_CENTER: (self.canvas.padding + self.canvas.zone_width + 20, self.canvas.padding + 2 * (self.canvas.zone_height + 20)),
            LayoutZone.BOTTOM_RIGHT: (self.canvas.padding + 2 * (self.canvas.zone_width + 20), self.canvas.padding + 2 * (self.canvas.zone_height + 20))
        }
        return zone_map[zone]
    
    def allocate_space(self, zone: LayoutZone, width: int, height: int) -> Tuple[int, int]:
        """
        Allocate space in a zone, preventing overlap
        Returns (x, y) coordinates
        """
        base_x, base_y = self.get_zone_coordinates(zone)
        
        # Find available position in zone
        occupied = self.occupied_spaces[zone]
        
        if not occupied:
            # First element in zone - center it
            x = base_x + (self.canvas.zone_width - width) // 2
            y = base_y + (self.canvas.zone_height - height) // 2
        else:
            # Stack vertically with spacing
            last_elem = occupied[-1]
            x = base_x + (self.canvas.zone_width - width) // 2
            y = last_elem['y'] + last_elem['height'] + 20
            
            # If overflow, move to next column
            if y + height > base_y + self.canvas.zone_height:
                x = last_elem['x'] + last_elem['width'] + 20
                y = base_y
        
        # Record occupied space
        self.occupied_spaces[zone].append({
            'x': x, 'y': y, 
            'width': width, 
            'height': height
        })
        
        return (x, y)
    
    def clear_zone(self, zone: LayoutZone):
        """Clear a zone for reuse"""
        self.occupied_spaces[zone] = []

class VisualizationOrchestrator:
    """
    Main orchestrator that converts LLM instructions to visual scenes
    """
    
    def __init__(self, canvas_dims: Optional[CanvasDimensions] = None):
        self.canvas = canvas_dims or CanvasDimensions()
        self.coord_manager = CoordinateManager(self.canvas)
        self.scenes: List[VisualizationScene] = []
        
    def parse_llm_instruction(self, instruction: Dict) -> VisualizationScene:
        """
        Parse LLM visual instruction JSON into a VisualizationScene
        
        Expected format:
        {
            "scene_id": "solar_system_intro",
            "duration": 10.0,
            "audio_text": "Let's explore the solar system...",
            "background": {"type": "stars", "count": 100},
            "elements": [
                {
                    "type": "circle",
                    "zone": "center",
                    "properties": {
                        "radius": 100,
                        "fill": "yellow",
                        "label": "Sun"
                    },
                    "animation": {
                        "type": "fadeIn",
                        "duration": 2.0,
                        "delay": 0
                    }
                }
            ]
        }
        """
        scene_id = instruction.get('scene_id', 'scene_1')
        duration = instruction.get('duration', 5.0)
        audio_text = instruction.get('audio_text', '')
        background = instruction.get('background')
        
        elements = []
        for idx, elem_data in enumerate(instruction.get('elements', [])):
            element = self._create_visual_element(elem_data, idx)
            elements.append(element)
        
        scene = VisualizationScene(
            id=scene_id,
            elements=elements,
            duration=duration,
            audio_text=audio_text,
            background=background
        )
        
        logger.info(f"Parsed scene '{scene_id}' with {len(elements)} elements")
        return scene
    
    def _create_visual_element(self, elem_data: Dict, index: int) -> VisualElement:
        """Create a visual element with smart coordinate allocation"""
        elem_type = VisualElementType(elem_data['type'])
        zone = LayoutZone(elem_data.get('zone', 'center'))
        properties = elem_data.get('properties', {})
        animation = elem_data.get('animation')
        layer = elem_data.get('layer', 0)
        sync_audio = elem_data.get('sync_audio', False)
        
        # Calculate element dimensions
        width, height = self._calculate_dimensions(elem_type, properties)
        
        # Allocate coordinates to prevent overlap
        x, y = self.coord_manager.allocate_space(zone, width, height)
        
        # Add coordinates to properties
        properties['x'] = x
        properties['y'] = y
        properties['width'] = width
        properties['height'] = height
        
        element = VisualElement(
            id=f"elem_{index}_{elem_type.value}",
            type=elem_type,
            zone=zone,
            properties=properties,
            animation=animation,
            layer=layer,
            sync_audio=sync_audio
        )
        
        return element
    
    def _calculate_dimensions(self, elem_type: VisualElementType, props: Dict) -> Tuple[int, int]:
        """Calculate element dimensions based on type"""
        if elem_type == VisualElementType.CIRCLE:
            radius = props.get('radius', 50)
            return (radius * 2, radius * 2)
        
        elif elem_type == VisualElementType.RECTANGLE:
            return (props.get('width', 100), props.get('height', 100))
        
        elif elem_type == VisualElementType.TEXT:
            text = props.get('text', '')
            font_size = props.get('fontSize', 16)
            # Rough estimate: char_width * text_length
            return (len(text) * font_size * 0.6, font_size * 1.5)
        
        elif elem_type == VisualElementType.IMAGE:
            return (props.get('width', 200), props.get('height', 200))
        
        elif elem_type == VisualElementType.LINE or elem_type == VisualElementType.ARROW:
            points = props.get('points', [0, 0, 100, 0])
            x_coords = points[::2]
            y_coords = points[1::2]
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            return (width, height)
        
        return (100, 100)  # Default
    
    def create_konva_json(self, scene: VisualizationScene) -> Dict:
        """
        Convert scene to Konva.js compatible JSON
        """
        konva_stage = {
            "attrs": {
                "width": self.canvas.width,
                "height": self.canvas.height
            },
            "className": "Stage",
            "children": []
        }
        
        # Background layer
        if scene.background:
            bg_layer = self._create_background_layer(scene.background)
            konva_stage["children"].append(bg_layer)
        
        # Main content layer
        main_layer = {
            "attrs": {},
            "className": "Layer",
            "children": []
        }
        
        # Sort elements by layer for proper z-index
        sorted_elements = sorted(scene.elements, key=lambda e: e.layer)
        
        for element in sorted_elements:
            konva_shape = self._element_to_konva(element)
            main_layer["children"].append(konva_shape)
        
        konva_stage["children"].append(main_layer)
        
        return konva_stage
    
    def _element_to_konva(self, element: VisualElement) -> Dict:
        """Convert VisualElement to Konva shape"""
        base_attrs = {
            "id": element.id,
            "x": element.properties['x'],
            "y": element.properties['y']
        }
        
        if element.type == VisualElementType.CIRCLE:
            return {
                "attrs": {
                    **base_attrs,
                    "radius": element.properties.get('radius', 50),
                    "fill": element.properties.get('fill', '#3498db'),
                    "stroke": element.properties.get('stroke', '#2980b9'),
                    "strokeWidth": element.properties.get('strokeWidth', 2)
                },
                "className": "Circle"
            }
        
        elif element.type == VisualElementType.RECTANGLE:
            return {
                "attrs": {
                    **base_attrs,
                    "width": element.properties.get('width', 100),
                    "height": element.properties.get('height', 100),
                    "fill": element.properties.get('fill', '#2ecc71'),
                    "stroke": element.properties.get('stroke', '#27ae60'),
                    "strokeWidth": element.properties.get('strokeWidth', 2),
                    "cornerRadius": element.properties.get('cornerRadius', 5)
                },
                "className": "Rect"
            }
        
        elif element.type == VisualElementType.TEXT:
            return {
                "attrs": {
                    **base_attrs,
                    "text": element.properties.get('text', ''),
                    "fontSize": element.properties.get('fontSize', 16),
                    "fontFamily": element.properties.get('fontFamily', 'Arial'),
                    "fill": element.properties.get('fill', '#000000'),
                    "align": element.properties.get('align', 'left')
                },
                "className": "Text"
            }
        
        elif element.type == VisualElementType.IMAGE:
            return {
                "attrs": {
                    **base_attrs,
                    "image": element.properties.get('src', ''),
                    "width": element.properties.get('width', 200),
                    "height": element.properties.get('height', 200)
                },
                "className": "Image"
            }
        
        elif element.type == VisualElementType.ARROW:
            return {
                "attrs": {
                    **base_attrs,
                    "points": element.properties.get('points', [0, 0, 100, 0]),
                    "stroke": element.properties.get('stroke', '#e74c3c'),
                    "strokeWidth": element.properties.get('strokeWidth', 3),
                    "pointerLength": element.properties.get('pointerLength', 10),
                    "pointerWidth": element.properties.get('pointerWidth', 10)
                },
                "className": "Arrow"
            }
        
        return {}
    
    def create_gsap_animations(self, scene: VisualizationScene) -> List[Dict]:
        """
        Create GSAP animation timeline for the scene
        """
        animations = []
        
        for element in scene.elements:
            if element.animation:
                anim = self._create_gsap_animation(element)
                animations.append(anim)
        
        return animations
    
    def _create_gsap_animation(self, element: VisualElement) -> Dict:
        """Convert element animation to GSAP format"""
        anim = element.animation
        anim_type = AnimationType(anim.get('type', 'fadeIn'))
        
        base_anim = {
            "target": f"#{element.id}",
            "duration": anim.get('duration', 1.0),
            "delay": anim.get('delay', 0),
            "ease": anim.get('ease', 'power2.inOut')
        }
        
        if anim_type == AnimationType.FADE_IN:
            base_anim["from"] = {"opacity": 0}
            base_anim["to"] = {"opacity": 1}
        
        elif anim_type == AnimationType.DRAW:
            base_anim["from"] = {"drawSVG": "0%"}
            base_anim["to"] = {"drawSVG": "100%"}
        
        elif anim_type == AnimationType.MOVE:
            base_anim["to"] = {
                "x": anim.get('toX', element.properties['x']),
                "y": anim.get('toY', element.properties['y'])
            }
        
        elif anim_type == AnimationType.ROTATE:
            base_anim["to"] = {"rotation": anim.get('degrees', 360)}
        
        elif anim_type == AnimationType.SCALE:
            base_anim["to"] = {"scale": anim.get('scale', 1.5)}
        
        elif anim_type == AnimationType.PULSE:
            base_anim["to"] = {"scale": 1.2}
            base_anim["yoyo"] = True
            base_anim["repeat"] = -1
        
        return base_anim
    
    def _create_background_layer(self, bg_config: Dict) -> Dict:
        """Create background layer (stars, gradient, etc.)"""
        bg_type = bg_config.get('type', 'solid')
        
        if bg_type == 'stars':
            # PixiJS star field
            return {
                "attrs": {"id": "background_stars"},
                "className": "Layer",
                "children": [],
                "pixi": {
                    "type": "stars",
                    "count": bg_config.get('count', 100)
                }
            }
        
        elif bg_type == 'gradient':
            return {
                "attrs": {
                    "id": "background_gradient",
                    "fillLinearGradientStartPoint": {"x": 0, "y": 0},
                    "fillLinearGradientEndPoint": {"x": 0, "y": self.canvas.height},
                    "fillLinearGradientColorStops": bg_config.get('colors', [0, '#1e3c72', 1, '#2a5298'])
                },
                "className": "Rect"
            }
        
        return {}
    
    def generate_teaching_visualization(self, lesson_content: str, pdf_images: List[Dict]) -> List[VisualizationScene]:
        """
        Generate complete visualization from lesson content and PDF images
        This would typically call the LLM to generate visualization instructions
        """
        # This is a placeholder - in production, this would:
        # 1. Send lesson_content + pdf_images to LLM
        # 2. LLM returns structured visualization instructions
        # 3. Parse those instructions into scenes
        
        scenes = []
        
        # Example: Create intro scene with PDF image
        if pdf_images:
            intro_instruction = {
                "scene_id": "intro_with_image",
                "duration": 8.0,
                "audio_text": "Let's begin by looking at this diagram from your textbook",
                "elements": [
                    {
                        "type": "image",
                        "zone": "center",
                        "properties": {
                            "src": pdf_images[0]['url'],
                            "width": 600,
                            "height": 400
                        },
                        "animation": {
                            "type": "fadeIn",
                            "duration": 1.5
                        },
                        "layer": 0
                    },
                    {
                        "type": "text",
                        "zone": "top_center",
                        "properties": {
                            "text": pdf_images[0].get('caption', 'Diagram'),
                            "fontSize": 24,
                            "fill": "#2c3e50"
                        },
                        "animation": {
                            "type": "fadeIn",
                            "duration": 1.0,
                            "delay": 0.5
                        },
                        "layer": 1
                    }
                ]
            }
            scene = self.parse_llm_instruction(intro_instruction)
            scenes.append(scene)
        
        return scenes

def generate_solar_system_example():
    """
    Example: Generate Solar System visualization
    """
    orchestrator = VisualizationOrchestrator()
    
    instruction = {
        "scene_id": "solar_system",
        "duration": 15.0,
        "audio_text": "The solar system consists of the Sun at the center, with Earth orbiting around it. Watch as Earth completes its orbit.",
        "background": {"type": "stars", "count": 150},
        "elements": [
            # Sun
            {
                "type": "circle",
                "zone": "center",
                "properties": {
                    "radius": 80,
                    "fill": "#FDB813",
                    "stroke": "#F39C12",
                    "strokeWidth": 3
                },
                "animation": {
                    "type": "fadeIn",
                    "duration": 2.0
                },
                "layer": 0,
                "sync_audio": True
            },
            # Sun label
            {
                "type": "text",
                "zone": "center",
                "properties": {
                    "text": "Sun",
                    "fontSize": 20,
                    "fill": "#FFFFFF"
                },
                "animation": {
                    "type": "fadeIn",
                    "duration": 1.0,
                    "delay": 1.0
                },
                "layer": 1
            },
            # Earth
            {
                "type": "circle",
                "zone": "center_right",
                "properties": {
                    "radius": 30,
                    "fill": "#3498DB",
                    "stroke": "#2980B9",
                    "strokeWidth": 2
                },
                "animation": {
                    "type": "move",
                    "duration": 10.0,
                    "delay": 3.0,
                    "path": "circular"  # Custom: circular orbit
                },
                "layer": 0,
                "sync_audio": True
            },
            # Orbit line
            {
                "type": "circle",
                "zone": "center",
                "properties": {
                    "radius": 250,
                    "stroke": "#95A5A6",
                    "strokeWidth": 1,
                    "dash": [5, 5]
                },
                "animation": {
                    "type": "draw",
                    "duration": 2.0,
                    "delay": 2.0
                },
                "layer": -1
            }
        ]
    }
    
    scene = orchestrator.parse_llm_instruction(instruction)
    konva_json = orchestrator.create_konva_json(scene)
    gsap_anims = orchestrator.create_gsap_animations(scene)
    
    return {
        "scene": scene,
        "konva": konva_json,
        "animations": gsap_anims
    }

if __name__ == "__main__":
    # Test the system
    result = generate_solar_system_example()
    print("Konva JSON:")
    print(json.dumps(result['konva'], indent=2))
    print("\nGSAP Animations:")
    print(json.dumps(result['animations'], indent=2))
