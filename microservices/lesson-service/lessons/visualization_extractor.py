"""
Visualization JSON Extractor
Extracts and validates visualization JSON from LLM-generated lesson content
"""

import json
import re
import logging

logger = logging.getLogger(__name__)

class VisualizationExtractor:
    """Extract visualization JSON from lesson content"""
    
    @staticmethod
    def extract_visualization_json(lesson_content: str) -> dict:
        """
        Extract visualization JSON from lesson content
        Returns dict with visualization data or None if not found
        """
        try:
            # DEBUG: Log the content being searched
            logger.info(f"� DEBUG: Searching for visualization in content length: {len(lesson_content)}")
            logger.info(f"� DEBUG: Content preview (first 500 chars): {lesson_content[:500]}")
            
            # Look for ```visualization block - handles optional headers and multiple newlines
            # Pattern matches: ## Visualization JSON\n\n```visualization OR just ```visualization
            viz_pattern = r'(?:##\s*Visualization\s*JSON\s*\n+)?```visualization\s*\n+(.*?)```'
            match = re.search(viz_pattern, lesson_content, re.DOTALL | re.IGNORECASE)
            
            if not match:
                # DEBUG: Show what patterns we found
                logger.warning("No visualization block found in lesson content")
                if '```' in lesson_content:
                    logger.info(f"� DEBUG: Found ``` markers at positions: {[i for i, c in enumerate(lesson_content) if lesson_content[i:i+3] == '```'][:5]}")
                if 'visualization' in lesson_content.lower():
                    logger.info(f"� DEBUG: Found 'visualization' text in content")
                return None
            
            viz_json_str = match.group(1).strip()

            # Parse JSON
            viz_data = json.loads(viz_json_str)

            # Sanitize to ensure compatibility with frontend/visualization service
            viz_data = VisualizationExtractor.sanitize_visualization(viz_data)

            # Validate structure
            if not VisualizationExtractor.validate_visualization(viz_data):
                logger.error("Visualization JSON structure is invalid")
                return None
            
            logger.info(f" Extracted visualization: {viz_data.get('topic', 'Unknown')}")
            return viz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse visualization JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting visualization: {e}")
            return None
    
    @staticmethod
    def validate_visualization(viz_data: dict) -> bool:
        """Validate visualization JSON structure"""
        try:
            # Check required fields
            if "topic" not in viz_data:
                logger.error("Missing 'topic' field")
                return False
            
            if "scenes" not in viz_data or not isinstance(viz_data["scenes"], list):
                logger.error("Missing or invalid 'scenes' field")
                return False
            
            if len(viz_data["scenes"]) == 0:
                logger.error("No scenes in visualization")
                return False
            
            # Validate each scene
            for idx, scene in enumerate(viz_data["scenes"]):
                if not isinstance(scene, dict):
                    logger.error(f"Scene {idx} is not a dictionary")
                    return False
                
                if "scene_id" not in scene:
                    logger.error(f"Scene {idx} missing 'scene_id'")
                    return False
                
                if "duration" not in scene:
                    logger.error(f"Scene {idx} missing 'duration'")
                    return False
                
                if "shapes" not in scene or not isinstance(scene["shapes"], list):
                    logger.error(f"Scene {idx} missing or invalid 'shapes'")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    @staticmethod
    def _is_valid_dash(val) -> bool:
        """Check if a value is a valid dash array for Konva (array of numbers with length>0)."""
        if isinstance(val, list) and len(val) > 0:
            try:
                # ensure all are finite numbers
                return all(isinstance(x, (int, float)) for x in val)
            except Exception:
                return False
        return False

    @staticmethod
    def sanitize_visualization(viz_data: dict) -> dict:
        """Normalize visualization JSON: unique scene_ids, numeric durations, and safe shape props.

        - Ensure each scene has a unique scene_id; if duplicates, suffix with incremental index.
        - Coerce duration to float and clamp to [1, 60] defaulting to 10 if invalid.
        - For shapes, remove invalid dash/lineDash props that cause Canvas setLineDash errors.
        - Drop unknown fields that are clearly wrong types for critical props.
        """
        try:
            scenes = viz_data.get('scenes', []) or []
            seen_ids = set()
            id_counts = {}
            sanitized_scenes = []

            for idx, scene in enumerate(scenes):
                scene = dict(scene) if isinstance(scene, dict) else {}
                # Unique scene_id
                sid = scene.get('scene_id') or f'scene_{idx+1}'
                base_sid = sid
                if sid in seen_ids:
                    id_counts[base_sid] = id_counts.get(base_sid, 1) + 1
                    sid = f"{base_sid}_{id_counts[base_sid]}"
                seen_ids.add(sid)
                scene['scene_id'] = sid

                # Duration normalization
                dur = scene.get('duration', 10)
                try:
                    dur = float(dur)
                except Exception:
                    dur = 10.0
                if dur < 1:
                    dur = 1.0
                if dur > 60:
                    dur = 60.0
                scene['duration'] = dur

                # Shapes sanitation
                shapes = scene.get('shapes', []) or []
                sanitized_shapes = []
                for shp in shapes:
                    shp = dict(shp) if isinstance(shp, dict) else {}
                    # Remove invalid dash props
                    if 'lineDash' in shp and not VisualizationExtractor._is_valid_dash(shp.get('lineDash')):
                        shp.pop('lineDash', None)
                    if 'dash' in shp and not VisualizationExtractor._is_valid_dash(shp.get('dash')):
                        shp.pop('dash', None)
                    # Coerce numeric basics if provided as strings
                    for num_key in ['x', 'y', 'width', 'height', 'radius', 'strokeWidth', 'pointerLength', 'pointerWidth', 'rotation', 'opacity', 'fontSize']:
                        if num_key in shp and isinstance(shp[num_key], str):
                            try:
                                shp[num_key] = float(shp[num_key])
                            except Exception:
                                shp.pop(num_key, None)
                    # Points must be a flat list of numbers
                    if 'points' in shp:
                        pts = shp.get('points')
                        if not isinstance(pts, list) or not all(isinstance(p, (int, float)) for p in pts):
                            shp.pop('points', None)
                    sanitized_shapes.append(shp)
                scene['shapes'] = sanitized_shapes

                # Animations safety: keep only those with valid shape_index
                anims = scene.get('animations', []) or []
                safe_anims = []
                for a in anims:
                    a = dict(a) if isinstance(a, dict) else {}
                    si = a.get('shape_index')
                    if isinstance(si, int) and 0 <= si < len(sanitized_shapes):
                        # clean numbers if strings
                        for num_key in ['duration', 'delay']:
                            if num_key in a and isinstance(a[num_key], str):
                                try:
                                    a[num_key] = float(a[num_key])
                                except Exception:
                                    a.pop(num_key, None)
                        safe_anims.append(a)
                scene['animations'] = safe_anims

                sanitized_scenes.append(scene)

            viz_data['scenes'] = sanitized_scenes
            return viz_data
        except Exception as e:
            logger.warning(f"sanitize_visualization encountered an issue: {e}")
            return viz_data
    
    @staticmethod
    def replace_pdf_image_placeholders(viz_data: dict, pdf_images: list) -> dict:
        """
        Replace {{PDF_IMAGE_N}} placeholders with actual base64 image data
        
        Args:
            viz_data: Visualization dictionary with placeholders
            pdf_images: List of image dicts with 'base64' field
        
        Returns:
            Updated visualization data with actual image URLs
        """
        if not pdf_images:
            return viz_data
        
        try:
            viz_json_str = json.dumps(viz_data)
            
            # Replace each placeholder with actual base64 data
            for idx, img_data in enumerate(pdf_images):
                placeholder = f"{{{{PDF_IMAGE_{idx}}}}}"
                # Use the base64 data URL directly
                actual_image = img_data.get('base64', '')
                viz_json_str = viz_json_str.replace(placeholder, actual_image)
                logger.info(f" Replaced {placeholder} with image data ({len(actual_image)} chars)")
            
            return json.loads(viz_json_str)
            
        except Exception as e:
            logger.error(f"Error replacing image placeholders: {e}")
            return viz_data
    
    @staticmethod
    def generate_fallback_visualization(topic: str, explanation: str = "") -> dict:
        """
        Generate a basic fallback visualization if LLM doesn't provide one
        """
        return {
            "topic": topic,
            "explanation": explanation or f"Visual representation of {topic}",
            "scenes": [
                {
                    "scene_id": "intro",
                    "title": "Introduction",
                    "duration": 10.0,
                    "shapes": [
                        {
                            "type": "text",
                            "zone": "top_center",
                            "text": topic,
                            "fontSize": 32,
                            "fill": "#2C3E50",
                            "fontFamily": "Arial"
                        },
                        {
                            "type": "rectangle",
                            "zone": "center",
                            "width": 400,
                            "height": 200,
                            "fill": "#ECF0F1",
                            "stroke": "#34495E",
                            "strokeWidth": 3,
                            "label": "Content Area"
                        }
                    ],
                    "animations": [
                        {
                            "shape_index": 0,
                            "type": "fadeIn",
                            "duration": 2.0,
                            "delay": 0.0
                        },
                        {
                            "shape_index": 1,
                            "type": "fadeIn",
                            "duration": 1.5,
                            "delay": 2.0
                        }
                    ],
                    "effects": {
                        "background": "white",
                        "glow": False
                    },
                    "audio": {
                        "text": f"Let's explore {topic} together.",
                        "start_time": 0.0,
                        "duration": 10.0
                    }
                }
            ]
        }
