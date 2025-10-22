import json
import os
import sys

# Ensure the 'lessons' package is on sys.path when running this script directly
CURRENT_DIR = os.path.dirname(__file__)
LESSON_SERVICE_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if LESSON_SERVICE_ROOT not in sys.path:
    sys.path.insert(0, LESSON_SERVICE_ROOT)

from lessons.visualization_extractor import VisualizationExtractor

# Construct a deliberately messy visualization payload
viz = {
    "topic": "Test Topic",
    "scenes": [
        {
            "scene_id": "scene_1",
            "title": "Intro",
            "duration": "12",
            "shapes": [
                {"type": "line", "points": [0, 0, 100, 100], "stroke": "#000", "dash": "abc"},
                {"type": "arrow", "points": [10, 10, 50, 50], "stroke": "#f00", "lineDash": [5, "x", 5]},
                {"type": "circle", "x": "100", "y": "200", "radius": "50", "strokeWidth": "3"},
                {"type": "rectangle", "x": "bad", "y": 10, "width": "100", "height": "notnum"},
                {"type": "text", "text": "Hello", "fontSize": "24"}
            ],
            "animations": [
                {"shape_index": 0, "type": "draw", "duration": "2", "delay": "0.2"},
                {"shape_index": 10, "type": "fadeIn"}  # invalid index, should be dropped
            ]
        },
        {
            "scene_id": "scene_1",  # duplicate on purpose
            "title": "Duplicate",
            "duration": 0.5,  # too small, should clamp to 1.0
            "shapes": [
                {"type": "line", "points": [0, 0, 10, 10], "dash": []},  # empty dash should be removed
            ]
        },
    ]
}

sanitized = VisualizationExtractor.sanitize_visualization(viz)

# Assertions / checks
scenes = sanitized.get("scenes", [])
assert len(scenes) == 2, "Expected 2 scenes"
assert scenes[0]["scene_id"] == "scene_1"
assert scenes[1]["scene_id"].startswith("scene_1"), "Duplicate scene_id should be suffixed"
assert isinstance(scenes[0]["duration"], float) and scenes[0]["duration"] == 12.0
assert scenes[1]["duration"] == 1.0, "Duration should be clamped to >= 1.0"

# Validate shapes
s0_shapes = scenes[0]["shapes"]
# dash invalid -> removed
assert "dash" not in s0_shapes[0]
# lineDash invalid -> removed
assert "lineDash" not in s0_shapes[1]
# numeric coercions
assert s0_shapes[2]["x"] == 100.0 and s0_shapes[2]["y"] == 200.0 and s0_shapes[2]["radius"] == 50.0 and s0_shapes[2]["strokeWidth"] == 3.0
# invalid numeric -> removed
assert "x" not in s0_shapes[3] and "height" not in s0_shapes[3]

# animations: second one should be dropped due to invalid index
assert len(scenes[0]["animations"]) == 1 and scenes[0]["animations"][0]["shape_index"] == 0

print("SANITIZER_SMOKE_TEST: PASS")
