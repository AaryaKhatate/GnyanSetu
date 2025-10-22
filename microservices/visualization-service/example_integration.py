"""
Complete End-to-End Example: Lesson Generation with Visualization
==================================================================

This example demonstrates the complete flow from PDF upload to visualization rendering.
"""

import requests
import json
import time

# ==================== Configuration ====================
LESSON_SERVICE_URL = "http://localhost:8003"
VISUALIZATION_SERVICE_URL = "http://localhost:8006"
TEACHING_SERVICE_URL = "http://localhost:8004"

# ==================== Step 1: Upload PDF & Generate Lesson ====================
def upload_pdf_and_generate_lesson():
    """
    Upload PDF to Lesson Service
    Lesson Service will generate:
    - Lesson content
    - Visualization JSON
    """
    print("📄 Step 1: Uploading PDF and generating lesson...")
    
    # Simulated lesson generation response
    # In reality, this comes from Lesson Service after PDF upload
    lesson_data = {
        "lesson_id": "lesson_photosynthesis_001",
        "title": "Photosynthesis",
        "content": "Photosynthesis is the process by which plants convert light energy...",
        "visualization": {
            "topic": "Photosynthesis",
            "explanation": "Visual breakdown of the photosynthesis process",
            "scenes": [
                {
                    "scene_id": "intro",
                    "title": "Introduction to Photosynthesis",
                    "duration": 12.0,
                    "shapes": [
                        {
                            "type": "text",
                            "zone": "top_center",
                            "text": "Photosynthesis",
                            "fontSize": 36,
                            "fill": "#2C3E50",
                            "fontFamily": "Arial"
                        },
                        {
                            "type": "image",
                            "zone": "center",
                            "src": "chloroplast.png",  # From PDF
                            "width": 300,
                            "height": 200
                        },
                        {
                            "type": "rectangle",
                            "zone": "center_left",
                            "width": 150,
                            "height": 100,
                            "fill": "#4CAF50",
                            "stroke": "#2E7D32",
                            "strokeWidth": 3,
                            "label": "Chloroplast"
                        }
                    ],
                    "animations": [
                        {
                            "shape_index": 0,
                            "type": "write",
                            "duration": 3.0,
                            "delay": 0.0
                        },
                        {
                            "shape_index": 1,
                            "type": "fadeIn",
                            "duration": 2.0,
                            "delay": 3.0
                        },
                        {
                            "shape_index": 2,
                            "type": "scale",
                            "duration": 2.0,
                            "delay": 5.0,
                            "from_props": {"scaleX": 0, "scaleY": 0},
                            "to_props": {"scaleX": 1, "scaleY": 1}
                        }
                    ],
                    "effects": {
                        "background": "#E8F5E9",
                        "glow": False
                    },
                    "audio": {
                        "text": "Photosynthesis occurs in the chloroplasts of plant cells. Let's explore how this amazing process works.",
                        "start_time": 0.0,
                        "duration": 12.0
                    }
                },
                {
                    "scene_id": "process",
                    "title": "The Process",
                    "duration": 15.0,
                    "shapes": [
                        {
                            "type": "circle",
                            "zone": "center_left",
                            "radius": 40,
                            "fill": "#FFA726",
                            "label": "CO2"
                        },
                        {
                            "type": "circle",
                            "zone": "bottom_left",
                            "radius": 40,
                            "fill": "#42A5F5",
                            "label": "H2O"
                        },
                        {
                            "type": "rectangle",
                            "zone": "center",
                            "width": 180,
                            "height": 120,
                            "fill": "#66BB6A",
                            "stroke": "#2E7D32",
                            "strokeWidth": 4,
                            "label": "Chloroplast"
                        },
                        {
                            "type": "circle",
                            "zone": "center_right",
                            "radius": 40,
                            "fill": "#FFEB3B",
                            "label": "Glucose"
                        },
                        {
                            "type": "circle",
                            "zone": "top_right",
                            "radius": 40,
                            "fill": "#90CAF9",
                            "label": "O2"
                        },
                        {
                            "type": "arrow",
                            "points": [200, 340, 400, 340],
                            "stroke": "#FF5722",
                            "strokeWidth": 4
                        },
                        {
                            "type": "arrow",
                            "points": [600, 340, 800, 340],
                            "stroke": "#4CAF50",
                            "strokeWidth": 4
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
                            "duration": 2.0,
                            "delay": 1.0
                        },
                        {
                            "shape_index": 5,
                            "type": "draw",
                            "duration": 2.0,
                            "delay": 2.0
                        },
                        {
                            "shape_index": 2,
                            "type": "pulse",
                            "duration": 2.0,
                            "delay": 4.0,
                            "repeat": 2
                        },
                        {
                            "shape_index": 6,
                            "type": "draw",
                            "duration": 2.0,
                            "delay": 8.0
                        },
                        {
                            "shape_index": 3,
                            "type": "fadeIn",
                            "duration": 2.0,
                            "delay": 10.0
                        },
                        {
                            "shape_index": 4,
                            "type": "fadeIn",
                            "duration": 2.0,
                            "delay": 11.0
                        }
                    ],
                    "effects": {
                        "background": "#E8F5E9",
                        "glow": True,
                        "glow_color": "#FDD835"
                    },
                    "audio": {
                        "text": "Carbon dioxide and water enter the chloroplast. With sunlight energy, they are transformed into glucose and oxygen. This is the fundamental equation of photosynthesis.",
                        "start_time": 0.0,
                        "duration": 15.0
                    }
                }
            ]
        }
    }
    
    print(f"✅ Lesson generated: {lesson_data['lesson_id']}")
    print(f"   Title: {lesson_data['title']}")
    print(f"   Scenes: {len(lesson_data['visualization']['scenes'])}")
    return lesson_data

# ==================== Step 2: Send to Visualization Orchestrator ====================
def process_visualization(lesson_data):
    """
    Send visualization JSON to Orchestrator for validation and optimization
    """
    print("\n🎨 Step 2: Processing visualization with Orchestrator...")
    
    # Prepare request
    viz_request = {
        "lesson_id": lesson_data["lesson_id"],
        "topic": lesson_data["visualization"]["topic"],
        "explanation": lesson_data["visualization"]["explanation"],
        "scenes": lesson_data["visualization"]["scenes"]
    }
    
    # Send to Visualization Orchestrator
    try:
        response = requests.post(
            f"{VISUALIZATION_SERVICE_URL}/api/visualizations/process",
            json=viz_request,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Visualization processed: {result['visualization_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Total Duration: {result['total_duration']}s")
        print(f"   Errors: {len(result.get('errors', []))}")
        print(f"   Warnings: {len(result.get('warnings', []))}")
        
        if result.get('warnings'):
            print("\n   ⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"      - {warning}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error processing visualization: {e}")
        return None

# ==================== Step 3: Retrieve Optimized Visualization ====================
def retrieve_visualization(visualization_id):
    """
    Retrieve optimized visualization from Orchestrator
    """
    print(f"\n📥 Step 3: Retrieving optimized visualization...")
    
    try:
        response = requests.get(
            f"{VISUALIZATION_SERVICE_URL}/api/visualizations/{visualization_id}",
            timeout=10
        )
        response.raise_for_status()
        
        viz_data = response.json()
        print(f"✅ Retrieved visualization")
        print(f"   Scenes: {len(viz_data['scenes'])}")
        print(f"   Canvas: {viz_data.get('canvas', {})}")
        
        return viz_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving visualization: {e}")
        return None

# ==================== Step 4: Stream to Frontend via Teaching Service ====================
def simulate_teaching_session(viz_data):
    """
    Simulate Teaching Service streaming visualization to frontend
    """
    print("\n📡 Step 4: Simulating teaching session...")
    print("   (In real implementation, this uses WebSocket)")
    
    for idx, scene in enumerate(viz_data['scenes']):
        print(f"\n   🎬 Scene {idx + 1}: {scene['title']}")
        print(f"      Duration: {scene['duration']}s")
        print(f"      Shapes: {len(scene['shapes'])}")
        print(f"      Animations: {len(scene['animations'])}")
        
        if scene.get('audio'):
            print(f"      🔊 Audio: \"{scene['audio']['text'][:50]}...\"")
        
        # Simulate scene duration
        # time.sleep(scene['duration'])
    
    print("\n✅ Teaching session complete!")

# ==================== Step 5: Frontend Rendering ====================
def generate_frontend_code(viz_data):
    """
    Generate React component code for rendering
    """
    print("\n💻 Step 5: Frontend Integration Code:")
    
    code = f"""
// React Component Usage
import React, {{ useState, useEffect }} from 'react';
import KonvaTeachingBoard from './components/KonvaTeachingBoard';

function PhotosynthesisLesson() {{
  const [scenes, setScenes] = useState([]);
  
  useEffect(() => {{
    // Fetch visualization
    fetch('http://localhost:8006/api/visualizations/{viz_data.get('visualization_id', 'viz_id')}')
      .then(res => res.json())
      .then(data => {{
        setScenes(data.scenes);
      }});
  }}, []);
  
  return (
    <div>
      <h1>{viz_data.get('topic', 'Lesson')}</h1>
      <KonvaTeachingBoard
        scenes={{scenes}}
        autoPlay={{true}}
        onSceneComplete={{(index) => console.log(`Scene ${{index}} complete`)}}
      />
    </div>
  );
}}

export default PhotosynthesisLesson;
"""
    
    print(code)

# ==================== Main Execution ====================
def main():
    print("=" * 60)
    print("  GnyanSetu - Complete Visualization Pipeline Demo")
    print("=" * 60)
    
    # Step 1: Generate lesson with visualization
    lesson_data = upload_pdf_and_generate_lesson()
    
    # Step 2: Process through Visualization Orchestrator
    processed_viz = process_visualization(lesson_data)
    
    if not processed_viz:
        print("\n❌ Failed to process visualization. Exiting.")
        return
    
    # Step 3: Retrieve optimized visualization
    viz_data = retrieve_visualization(processed_viz['visualization_id'])
    
    if not viz_data:
        print("\n❌ Failed to retrieve visualization. Exiting.")
        return
    
    # Step 4: Simulate teaching session
    simulate_teaching_session(viz_data)
    
    # Step 5: Generate frontend code
    generate_frontend_code(viz_data)
    
    print("\n" + "=" * 60)
    print("  ✅ Complete Pipeline Executed Successfully!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Start Visualization Service: cd visualization-service && python app.py")
    print("2. Upload real PDF to Lesson Service")
    print("3. Integrate KonvaTeachingBoard in your React app")
    print("4. Test with real-time WebSocket streaming")
    print("\n📚 See VISUALIZATION_ARCHITECTURE.md for details")

if __name__ == "__main__":
    main()
