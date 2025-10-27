"""
GnyanSetu - System Architecture Diagram Generator
Creates detailed PNG diagrams for system architecture and workflow
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# Create figure for System Architecture - LARGER SIZE, BIGGER TEXT
fig1, ax1 = plt.subplots(1, 1, figsize=(24, 24))
ax1.set_xlim(0, 24)
ax1.set_ylim(0, 24)
ax1.axis('off')

# Title
ax1.text(12, 23, 'GNYANSETU - SYSTEM ARCHITECTURE', 
         fontsize=36, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#2196F3', edgecolor='black', linewidth=4))

# ============================================================================
# USER FLOW - STEP BY STEP IN SQUARE LAYOUT
# ============================================================================

# STEP 1: User Authentication (Top Left)
step1_box = FancyBboxPatch((1, 17), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#F44336', facecolor='#FFCDD2', linewidth=4)
ax1.add_patch(step1_box)
ax1.text(4, 20.5, 'STEP 1: AUTHENTICATION', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#F44336', edgecolor='black'))
ax1.text(4, 19.8, 'USER SERVICE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(4, 19.2, 'Port: 8002', fontsize=14, ha='center')
ax1.text(4, 18.5, '✓ Login/Signup\n✓ JWT Tokens\n✓ Google OAuth\n✓ Password Reset', 
         fontsize=13, ha='center')

# Arrow to Step 2
ax1.annotate('', xy=(8, 19.5), xytext=(7, 19.5),
            arrowprops=dict(arrowstyle='->', lw=4, color='black'))
ax1.text(7.5, 20, 'Login Success', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# STEP 2: PDF Upload (Top Right)
step2_box = FancyBboxPatch((8.5, 17), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#2196F3', facecolor='#BBDEFB', linewidth=4)
ax1.add_patch(step2_box)
ax1.text(11.5, 20.5, 'STEP 2: UPLOAD PDF', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#2196F3', edgecolor='black'))
ax1.text(11.5, 19.8, 'LESSON SERVICE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(11.5, 19.2, 'Port: 8003', fontsize=14, ha='center')
ax1.text(11.5, 18.5, '✓ PDF Processing\n✓ OCR (Tesseract)\n✓ Image Extraction\n✓ Text Extraction', 
         fontsize=13, ha='center')

# Arrow to Step 3
ax1.annotate('', xy=(11.5, 16.8), xytext=(11.5, 17),
            arrowprops=dict(arrowstyle='->', lw=4, color='black'))
ax1.text(12.5, 16.9, 'PDF Processed', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# STEP 3: AI Lesson Generation (Middle Right)
step3_box = FancyBboxPatch((8.5, 11), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#4CAF50', facecolor='#C8E6C9', linewidth=4)
ax1.add_patch(step3_box)
ax1.text(11.5, 14.5, 'STEP 3: AI GENERATION', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#4CAF50', edgecolor='black'))
ax1.text(11.5, 13.8, 'GEMINI AI ENGINE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(11.5, 13.2, 'gemini-2.0-flash-exp', fontsize=14, ha='center')
ax1.text(11.5, 12.5, '✓ Multimodal AI\n✓ Text + Images\n✓ 30-60s Generation\n✓ Subject-Specific', 
         fontsize=13, ha='center')

# Arrow to Step 4
ax1.annotate('', xy=(8.3, 13), xytext=(8.5, 13),
            arrowprops=dict(arrowstyle='->', lw=4, color='black'))
ax1.text(8, 13.5, 'Lesson Ready', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# STEP 4: Visualization Generation (Middle Left)
step4_box = FancyBboxPatch((1, 11), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#FF5722', facecolor='#FFCCBC', linewidth=4)
ax1.add_patch(step4_box)
ax1.text(4, 14.5, 'STEP 4: VISUALIZE', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#FF5722', edgecolor='black'))
ax1.text(4, 13.8, 'VISUALIZATION SERVICE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(4, 13.2, 'Port: 8006', fontsize=14, ha='center')
ax1.text(4, 12.5, '✓ 9-Zone Canvas\n✓ 14 Icons\n✓ 11 Animations\n✓ Subject Diagrams', 
         fontsize=13, ha='center')

# Arrow to Step 5
ax1.annotate('', xy=(4, 10.8), xytext=(4, 11),
            arrowprops=dict(arrowstyle='->', lw=4, color='black'))
ax1.text(5, 10.9, 'Visuals Created', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# STEP 5: Interactive Teaching (Bottom Left)
step5_box = FancyBboxPatch((1, 5), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#9C27B0', facecolor='#E1BEE7', linewidth=4)
ax1.add_patch(step5_box)
ax1.text(4, 8.5, 'STEP 5: TEACHING', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#9C27B0', edgecolor='black'))
ax1.text(4, 7.8, 'TEACHING SERVICE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(4, 7.2, 'Port: 8004 (WebSocket)', fontsize=14, ha='center')
ax1.text(4, 6.5, '✓ Real-time AI Chat\n✓ Voice Synthesis\n✓ Canvas Drawing\n✓ Step-by-Step', 
         fontsize=13, ha='center')

# Arrow to Step 6
ax1.annotate('', xy=(8, 7), xytext=(7, 7),
            arrowprops=dict(arrowstyle='->', lw=4, color='black'))
ax1.text(7.5, 7.5, 'Start Teaching', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# STEP 6: Quiz & Assessment (Bottom Right)
step6_box = FancyBboxPatch((8.5, 5), 6, 4.5, boxstyle="round,pad=0.2",
                           edgecolor='#FFC107', facecolor='#FFECB3', linewidth=4)
ax1.add_patch(step6_box)
ax1.text(11.5, 8.5, 'STEP 6: ASSESSMENT', fontsize=18, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#FFC107', edgecolor='black'))
ax1.text(11.5, 7.8, 'QUIZ/NOTES SERVICE', fontsize=16, weight='bold', ha='center', style='italic')
ax1.text(11.5, 7.2, 'Port: 8005', fontsize=14, ha='center')
ax1.text(11.5, 6.5, '✓ Auto MCQ Gen\n✓ Notes Summary\n✓ Quiz Results\n✓ Performance Track', 
         fontsize=13, ha='center')

# API Gateway (Center - connecting all services)
gateway_box = FancyBboxPatch((16, 9), 7, 6, boxstyle="round,pad=0.3",
                             edgecolor='#FF9800', facecolor='#FFE0B2', linewidth=5)
ax1.add_patch(gateway_box)
ax1.text(19.5, 13.5, 'API GATEWAY', fontsize=20, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#FF9800', edgecolor='black'))
ax1.text(19.5, 12.7, 'Port: 8000', fontsize=16, ha='center', weight='bold')
ax1.text(19.5, 12, 'FastAPI + HTTPX', fontsize=14, ha='center', style='italic')
ax1.text(19.5, 11.2, '✓ Central Routing\n✓ Load Balancing\n✓ Timeout (180s)\n✓ CORS Handler\n✓ Health Checks', 
         fontsize=13, ha='center')
ax1.text(19.5, 9.7, 'Routes ALL requests\nto microservices', fontsize=13, ha='center', 
         weight='bold', style='italic',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

# Arrows from services to API Gateway
for x, y in [(7, 19.5), (14.5, 19.5), (14.5, 13), (7, 13), (7, 7), (14.5, 7)]:
    ax1.annotate('', xy=(16, 12), xytext=(x, y),
                arrowprops=dict(arrowstyle='->', lw=3, color='#FF9800', linestyle='--'))

# Database Layer (Bottom)
db_box = FancyBboxPatch((1, 1), 21, 2.8, boxstyle="round,pad=0.2",
                        edgecolor='#00BCD4', facecolor='#B2EBF2', linewidth=4)
ax1.add_patch(db_box)
ax1.text(11.5, 3.2, 'MONGODB DATABASE LAYER (Database per Service)', 
         fontsize=18, weight='bold', ha='center')

db_names = [
    ('users_db', 2.5),
    ('lesson_db', 6),
    ('teaching_db', 9.5),
    ('quiz_db', 13),
    ('viz_db', 16.5),
    ('sessions', 20)
]
for name, x in db_names:
    ax1.text(x, 2.2, name, fontsize=14, ha='center', weight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#00BCD4', linewidth=2))

# Frontend (Top Center)
frontend_box = FancyBboxPatch((16, 17), 7, 4.5, boxstyle="round,pad=0.2",
                              edgecolor='#4CAF50', facecolor='#C8E6C9', linewidth=4)
ax1.add_patch(frontend_box)
ax1.text(19.5, 20.5, 'FRONTEND', fontsize=20, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#4CAF50', edgecolor='black'))
ax1.text(19.5, 19.5, 'React 18 + Konva.js', fontsize=15, ha='center', weight='bold')
ax1.text(19.5, 18.7, 'Landing Page (3000)\nDashboard (3001)', fontsize=13, ha='center')
ax1.text(19.5, 17.8, '✓ User Interface\n✓ Canvas Rendering\n✓ Voice Synthesis', 
         fontsize=13, ha='center')

# Arrow from Frontend to Gateway
ax1.annotate('', xy=(19.5, 15), xytext=(19.5, 17),
            arrowprops=dict(arrowstyle='<->', lw=4, color='black'))
ax1.text(20.5, 16, 'HTTP/WS', fontsize=12, ha='center', weight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow'))

# Technology Stack (Bottom Right)
tech_box = FancyBboxPatch((16, 1), 7, 2.8, boxstyle="round,pad=0.2",
                          edgecolor='#607D8B', facecolor='#CFD8DC', linewidth=3)
ax1.add_patch(tech_box)
ax1.text(19.5, 3.2, 'TECH STACK', fontsize=16, weight='bold', ha='center')
ax1.text(19.5, 2.6, 'AI: Gemini 2.0 Flash', fontsize=12, ha='center')
ax1.text(19.5, 2.2, 'Backend: Django + FastAPI', fontsize=12, ha='center')
ax1.text(19.5, 1.8, 'Frontend: React + Konva', fontsize=12, ha='center')
ax1.text(19.5, 1.4, 'DB: MongoDB', fontsize=12, ha='center')

plt.tight_layout()
plt.savefig('E:/Project/GnyanSetu/GNYANSETU_SYSTEM_ARCHITECTURE.png', dpi=400, bbox_inches='tight', facecolor='white')
print("✅ System Architecture diagram saved!")

plt.close()

# ============================================================================
# WORKFLOW FLOWCHART - SIMPLIFIED AND READABLE
# ============================================================================

fig2, ax2 = plt.subplots(1, 1, figsize=(18, 24))
ax2.set_xlim(0, 18)
ax2.set_ylim(0, 24)
ax2.axis('off')

# Title
ax2.text(9, 23.5, 'GNYANSETU - COMPLETE USER WORKFLOW', 
         fontsize=32, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='#2196F3', edgecolor='black', linewidth=4))

def draw_step(ax, x, y, width, height, title, details, color, step_num):
    """Draw a workflow step box"""
    box = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.15",
                         edgecolor='black', facecolor=color, linewidth=3)
    ax.add_patch(box)
    
    # Step number circle
    circle = Circle((x + 0.7, y + height - 0.7), 0.5, facecolor='black', edgecolor='white', linewidth=2)
    ax.add_patch(circle)
    ax.text(x + 0.7, y + height - 0.7, str(step_num), fontsize=18, ha='center', va='center',
           color='white', weight='bold')
    
    # Title
    ax.text(x + width/2, y + height - 0.7, title, fontsize=16, weight='bold', ha='center')
    
    # Details
    ax.text(x + width/2, y + height/2, details, fontsize=13, ha='center', va='center')

# Define workflow steps
steps = [
    (2, 20.5, 14, 2, 'USER OPENS LANDING PAGE', 'Opens http://localhost:3000\nSees login/signup interface', '#C8E6C9', 1),
    (2, 18, 14, 2, 'AUTHENTICATION', 'Enters email + password OR uses Google OAuth\nAPI Gateway → User Service (8002)\nJWT tokens generated and stored', '#BBDEFB', 2),
    (2, 15.5, 14, 2, 'REDIRECTED TO DASHBOARD', 'User lands on http://localhost:3001\nSees upload interface and previous lessons', '#C8E6C9', 3),
    (2, 13, 14, 2, 'UPLOAD PDF DOCUMENT', 'User selects PDF file and clicks upload\nPOST /api/generate-lesson/\nAPI Gateway → Lesson Service (8003)', '#FFE0B2', 4),
    (2, 10.5, 14, 2, 'PDF PROCESSING', 'Extract text (PyPDF2) + images (PIL)\nOCR on images (Tesseract)\nDetect subject (Biology/Physics/etc.)', '#BBDEFB', 5),
    (2, 8, 14, 2, 'AI LESSON GENERATION', 'Gemini 2.0 Flash receives text + 3 images\nGenerates markdown lesson + visualization JSON\nTime: 30-60 seconds', '#FFCDD2', 6),
    (2, 5.5, 14, 2, 'VISUALIZATION CREATION', 'Visualization Service (8006) processes JSON\n9-zone canvas layout with shapes, icons, animations\nReturns complete scene data', '#FFCCBC', 7),
    (2, 3, 14, 2, 'INTERACTIVE TEACHING', 'User clicks "Start Teaching"\nWebSocket connection to Teaching Service (8004)\nReal-time AI explanations + canvas animations + voice', '#E1BEE7', 8),
    (2, 0.5, 14, 2, 'QUIZ & ASSESSMENT', 'User takes quiz (Quiz Service 8005)\nAuto-generated MCQs from lesson\nImmediate feedback + score tracking', '#FFECB3', 9),
]

for step in steps:
    draw_step(ax2, *step)

# Draw arrows between steps
for i in range(len(steps) - 1):
    y_from = steps[i][1]  # y position
    y_to = steps[i+1][1] + steps[i+1][3]  # y position + height of next step
    ax2.annotate('', xy=(9, y_to), xytext=(9, y_from),
                arrowprops=dict(arrowstyle='->', lw=5, color='black'))

plt.tight_layout()
plt.savefig('E:/Project/GnyanSetu/GNYANSETU_WORKFLOW_FLOWCHART.png', dpi=400, bbox_inches='tight', facecolor='white')
print("✅ Workflow Flowchart saved!")

print("\n" + "="*80)
print("SUCCESS! Generated 2 detailed diagrams with LARGE TEXT:")
print("1. GNYANSETU_SYSTEM_ARCHITECTURE.png - Square layout with 6-step flow")
print("2. GNYANSETU_WORKFLOW_FLOWCHART.png - Complete user journey")
print("="*80)


# Frontend Layer
frontend_box = FancyBboxPatch((1, 11), 18, 1.8, boxstyle="round,pad=0.1", 
                              edgecolor='#4CAF50', facecolor='#C8E6C9', linewidth=3)
ax1.add_patch(frontend_box)
ax1.text(10, 12.5, 'FRONTEND LAYER', fontsize=16, weight='bold', ha='center')
ax1.text(5, 11.8, 'Landing Page\n(Port 3000)\n• Authentication\n• Google OAuth', 
         fontsize=10, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#4CAF50', linewidth=2))
ax1.text(10, 11.8, 'React.js 18', fontsize=12, weight='bold', ha='center')
ax1.text(15, 11.8, 'Dashboard\n(Port 3001)\n• Lesson Upload\n• Teaching Board\n• Quiz/Notes', 
         fontsize=10, ha='center', va='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#4CAF50', linewidth=2))

# Arrow from Frontend to Gateway
ax1.arrow(10, 11, 0, -0.5, head_width=0.3, head_length=0.2, fc='black', ec='black', linewidth=2)
ax1.text(10.5, 10.7, 'HTTP/WebSocket', fontsize=9, style='italic')

# API Gateway
gateway_box = FancyBboxPatch((3, 9), 14, 1.2, boxstyle="round,pad=0.1",
                             edgecolor='#FF9800', facecolor='#FFE0B2', linewidth=3)
ax1.add_patch(gateway_box)
ax1.text(10, 9.8, 'API GATEWAY (Port 8000) - FastAPI', fontsize=14, weight='bold', ha='center')
ax1.text(10, 9.3, 'Routing • Timeout Management (180s) • CORS • Health Checks', 
         fontsize=10, ha='center', style='italic')

# Microservices Layer Label
ax1.text(10, 8.3, 'MICROSERVICES LAYER', fontsize=16, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#E1BEE7', edgecolor='#9C27B0', linewidth=2))

# Microservice 1: User Authentication
service1_box = FancyBboxPatch((0.5, 5.5), 3.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#F44336', facecolor='#FFCDD2', linewidth=2)
ax1.add_patch(service1_box)
ax1.text(2.25, 7.5, 'USER AUTH\nService', fontsize=11, weight='bold', ha='center')
ax1.text(2.25, 7, 'Port: 8002', fontsize=9, ha='center', style='italic')
ax1.text(2.25, 6.5, 'Django REST\n+ MongoDB', fontsize=9, ha='center')
ax1.text(2.25, 6, '• JWT Tokens\n• Google OAuth\n• Sessions', fontsize=8, ha='center')

# Microservice 2: Lesson Generation
service2_box = FancyBboxPatch((4.5, 5.5), 3.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#2196F3', facecolor='#BBDEFB', linewidth=2)
ax1.add_patch(service2_box)
ax1.text(6.25, 7.5, 'LESSON GEN\nService', fontsize=11, weight='bold', ha='center')
ax1.text(6.25, 7, 'Port: 8003', fontsize=9, ha='center', style='italic')
ax1.text(6.25, 6.5, 'Django\n+ Gemini AI', fontsize=9, ha='center')
ax1.text(6.25, 6, '• PDF Process\n• OCR Images\n• AI Lessons', fontsize=8, ha='center')

# Microservice 3: Teaching
service3_box = FancyBboxPatch((8.5, 5.5), 3.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#4CAF50', facecolor='#C8E6C9', linewidth=2)
ax1.add_patch(service3_box)
ax1.text(10.25, 7.5, 'TEACHING\nService', fontsize=11, weight='bold', ha='center')
ax1.text(10.25, 7, 'Port: 8004', fontsize=9, ha='center', style='italic')
ax1.text(10.25, 6.5, 'Django Channels\n+ WebSockets', fontsize=9, ha='center')
ax1.text(10.25, 6, '• Real-time AI\n• Voice Synth\n• Canvas', fontsize=8, ha='center')

# Microservice 4: Quiz & Notes
service4_box = FancyBboxPatch((12.5, 5.5), 3.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#9C27B0', facecolor='#E1BEE7', linewidth=2)
ax1.add_patch(service4_box)
ax1.text(14.25, 7.5, 'QUIZ/NOTES\nService', fontsize=11, weight='bold', ha='center')
ax1.text(14.25, 7, 'Port: 8005', fontsize=9, ha='center', style='italic')
ax1.text(14.25, 6.5, 'FastAPI\n+ Gemini AI', fontsize=9, ha='center')
ax1.text(14.25, 6, '• MCQ Quiz\n• Notes Gen\n• Analytics', fontsize=8, ha='center')

# Microservice 5: Visualization
service5_box = FancyBboxPatch((16.5, 5.5), 3.5, 2.3, boxstyle="round,pad=0.1",
                              edgecolor='#FF5722', facecolor='#FFCCBC', linewidth=2)
ax1.add_patch(service5_box)
ax1.text(18.25, 7.5, 'VISUALIZE\nService', fontsize=11, weight='bold', ha='center')
ax1.text(18.25, 7, 'Port: 8006', fontsize=9, ha='center', style='italic')
ax1.text(18.25, 6.5, 'FastAPI\n+ Gemini AI', fontsize=9, ha='center')
ax1.text(18.25, 6, '• 9-Zone Grid\n• Animations\n• Icons', fontsize=8, ha='center')

# Arrows from Gateway to Services
for x_pos in [2.25, 6.25, 10.25, 14.25, 18.25]:
    ax1.arrow(10, 9, x_pos-10, -1.1, head_width=0.15, head_length=0.1, 
             fc='#FF9800', ec='#FF9800', linewidth=1.5, alpha=0.7)

# Database Layer
db_box = FancyBboxPatch((1, 3.5), 18, 1.5, boxstyle="round,pad=0.1",
                        edgecolor='#00BCD4', facecolor='#B2EBF2', linewidth=3)
ax1.add_patch(db_box)
ax1.text(10, 4.7, 'DATABASE LAYER - MongoDB (Database per Service)', 
         fontsize=14, weight='bold', ha='center')
ax1.text(3, 3.9, 'users_db\n(users, sessions)', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#00BCD4'))
ax1.text(6.5, 3.9, 'lesson_db\n(lessons, pdfs)', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#00BCD4'))
ax1.text(10, 3.9, 'teaching_db\n(sessions, chat)', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#00BCD4'))
ax1.text(13.5, 3.9, 'quiz_notes_db\n(quizzes, results)', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#00BCD4'))
ax1.text(17, 3.9, 'visualization_db\n(visuals)', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', edgecolor='#00BCD4'))

# Arrows from Services to Databases
for x_from, x_to in [(2.25, 3), (6.25, 6.5), (10.25, 10), (14.25, 13.5), (18.25, 17)]:
    ax1.arrow(x_from, 5.5, x_to-x_from, -1.4, head_width=0.1, head_length=0.08,
             fc='#00BCD4', ec='#00BCD4', linewidth=1.2, alpha=0.6)

# AI Engine Layer
ai_box = FancyBboxPatch((1, 1.8), 18, 1.2, boxstyle="round,pad=0.1",
                        edgecolor='#FFC107', facecolor='#FFECB3', linewidth=3)
ax1.add_patch(ai_box)
ax1.text(10, 2.7, 'AI/ML ENGINE', fontsize=14, weight='bold', ha='center')
ax1.text(10, 2.3, 'Google Gemini 2.0 Flash Experimental (Multimodal) • Gemini 2.5 Flash (Visualization)', 
         fontsize=10, ha='center')
ax1.text(10, 1.95, 'Vision Support • OCR (Tesseract) • Natural Language Processing • Code Generation', 
         fontsize=9, ha='center', style='italic')

# Technology Stack Box
tech_box = FancyBboxPatch((1, 0.3), 8, 1.2, boxstyle="round,pad=0.1",
                          edgecolor='#607D8B', facecolor='#CFD8DC', linewidth=2)
ax1.add_patch(tech_box)
ax1.text(5, 1.3, 'TECHNOLOGY STACK', fontsize=11, weight='bold', ha='center')
ax1.text(5, 0.9, 'Frontend: React 18, Konva.js, Web Speech API', fontsize=8, ha='center')
ax1.text(5, 0.6, 'Backend: Django 4.2, FastAPI, Django Channels', fontsize=8, ha='center')

# Key Features Box
features_box = FancyBboxPatch((11, 0.3), 8, 1.2, boxstyle="round,pad=0.1",
                              edgecolor='#8BC34A', facecolor='#DCEDC8', linewidth=2)
ax1.add_patch(features_box)
ax1.text(15, 1.3, 'KEY FEATURES', fontsize=11, weight='bold', ha='center')
ax1.text(15, 0.9, 'PDF → AI Lesson (30-60s) • Real-time Teaching (WebSocket)', fontsize=8, ha='center')
ax1.text(15, 0.6, 'Dynamic Visualizations • Adaptive Quizzes • Voice Synthesis', fontsize=8, ha='center')

plt.tight_layout()
plt.savefig('E:/Project/GnyanSetu/GNYANSETU_SYSTEM_ARCHITECTURE.png', dpi=300, bbox_inches='tight')
print("✅ System Architecture diagram saved!")

# Create figure for Workflow Flowchart
fig2, ax2 = plt.subplots(1, 1, figsize=(16, 20))
ax2.set_xlim(0, 16)
ax2.set_ylim(0, 20)
ax2.axis('off')

# Title
ax2.text(8, 19.5, 'GNYANSETU - COMPLETE WORKFLOW FLOWCHART', 
         fontsize=22, weight='bold', ha='center',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#2196F3', edgecolor='black', linewidth=2))

# User Registration/Login Flow
ax2.text(8, 18.8, 'PHASE 1: USER AUTHENTICATION', fontsize=14, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#FFEB3B', edgecolor='black'))

y_pos = 18.2
boxes = [
    ("User Opens\nLanding Page", '#C8E6C9'),
    ("Clicks\nSign Up/Login", '#C8E6C9'),
    ("Enters Credentials\nOR Google OAuth", '#BBDEFB'),
    ("API Gateway\nRoutes to User Service", '#FFE0B2'),
    ("Validate & Hash\nPassword (Bcrypt)", '#FFCDD2'),
    ("Store in MongoDB\nusers_db", '#B2EBF2'),
    ("Generate JWT\nAccess + Refresh Tokens", '#E1BEE7'),
    ("Return Tokens\nto Frontend", '#C8E6C9'),
    ("Store in localStorage\nRedirect to Dashboard", '#C8E6C9')
]

for i, (text, color) in enumerate(boxes):
    box = FancyBboxPatch((5.5, y_pos - i*0.8), 5, 0.6, boxstyle="round,pad=0.05",
                         edgecolor='black', facecolor=color, linewidth=1.5)
    ax2.add_patch(box)
    ax2.text(8, y_pos - i*0.8 + 0.3, text, fontsize=9, ha='center', va='center')
    if i < len(boxes) - 1:
        ax2.arrow(8, y_pos - i*0.8, 0, -0.15, head_width=0.2, head_length=0.05,
                 fc='black', ec='black', linewidth=1.5)

# Lesson Generation Flow
y_pos = 11.5
ax2.text(8, y_pos + 0.5, 'PHASE 2: LESSON GENERATION (PDF → AI Lesson)', 
         fontsize=14, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#FFEB3B', edgecolor='black'))

lesson_boxes = [
    ("User Uploads PDF\non Dashboard", '#C8E6C9'),
    ("POST /api/generate-lesson/\n+ multipart/form-data", '#C8E6C9'),
    ("API Gateway → Lesson Service\n(180s timeout)", '#FFE0B2'),
    ("Save PDF to\nuploads/user_id/", '#B2EBF2'),
    ("Extract Text (PyPDF2)\n+ Images (PIL)\n+ OCR (Tesseract)", '#BBDEFB'),
    ("Detect Subject\n(Biology/Physics/etc.)", '#E1BEE7'),
    ("Build Multimodal Prompt\nText + 3 Images", '#FFE0B2'),
    ("Call Gemini AI\n(30-60 seconds)", '#FFCDD2'),
    ("AI Returns:\nMarkdown Lesson\n+ Visualization JSON", '#C8E6C9'),
    ("Extract & Validate\nVisualization JSON", '#BBDEFB'),
    ("Store in MongoDB\nlesson_service_db", '#B2EBF2'),
    ("Return Lesson ID\n+ Content to Frontend", '#C8E6C9')
]

for i, (text, color) in enumerate(lesson_boxes):
    box = FancyBboxPatch((5.5, y_pos - i*0.65), 5, 0.5, boxstyle="round,pad=0.05",
                         edgecolor='black', facecolor=color, linewidth=1.5)
    ax2.add_patch(box)
    ax2.text(8, y_pos - i*0.65 + 0.25, text, fontsize=8, ha='center', va='center')
    if i < len(lesson_boxes) - 1:
        ax2.arrow(8, y_pos - i*0.65, 0, -0.12, head_width=0.2, head_length=0.03,
                 fc='black', ec='black', linewidth=1.5)

# Interactive Teaching Flow
y_pos = 3.8
ax2.text(8, y_pos + 0.5, 'PHASE 3: INTERACTIVE TEACHING (Real-time AI)', 
         fontsize=14, weight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='#FFEB3B', edgecolor='black'))

teaching_boxes = [
    ("User Clicks\n'Start Teaching'", '#C8E6C9'),
    ("Establish WebSocket\nws://localhost:8004/ws/teaching/", '#BBDEFB'),
    ("Teaching Service\nCreates Session", '#E1BEE7'),
    ("Load Lesson Content\n+ Visualization Data", '#B2EBF2'),
    ("Send Scene 1\nCanvas Data", '#FFE0B2'),
    ("Frontend Renders\nShapes (Konva.js)\n+ Voice Synthesis", '#C8E6C9'),
    ("User Asks Question\n'What is chlorophyll?'", '#FFCDD2'),
    ("Gemini AI Generates\nAnswer + Highlights Shape", '#E1BEE7'),
    ("Frontend Shows Answer\n+ Glows Shape", '#C8E6C9'),
    ("Repeat for 4-5 Scenes\nComplete Session", '#C8E6C9')
]

for i, (text, color) in enumerate(teaching_boxes):
    box = FancyBboxPatch((5.5, y_pos - i*0.5), 5, 0.4, boxstyle="round,pad=0.05",
                         edgecolor='black', facecolor=color, linewidth=1.5)
    ax2.add_patch(box)
    ax2.text(8, y_pos - i*0.5 + 0.2, text, fontsize=8, ha='center', va='center')
    if i < len(teaching_boxes) - 1:
        ax2.arrow(8, y_pos - i*0.5, 0, -0.08, head_width=0.2, head_length=0.02,
                 fc='black', ec='black', linewidth=1.5)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor='#C8E6C9', edgecolor='black', label='User Action'),
    mpatches.Patch(facecolor='#BBDEFB', edgecolor='black', label='Network/Communication'),
    mpatches.Patch(facecolor='#FFE0B2', edgecolor='black', label='API Gateway/Routing'),
    mpatches.Patch(facecolor='#FFCDD2', edgecolor='black', label='AI Processing'),
    mpatches.Patch(facecolor='#B2EBF2', edgecolor='black', label='Database Operation'),
    mpatches.Patch(facecolor='#E1BEE7', edgecolor='black', label='Service Processing')
]
ax2.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=9,
          bbox_to_anchor=(0.5, -0.02))

plt.tight_layout()
plt.savefig('E:/Project/GnyanSetu/GNYANSETU_WORKFLOW_FLOWCHART.png', dpi=300, bbox_inches='tight')
print("✅ Workflow Flowchart saved!")

print("\n" + "="*80)
print("SUCCESS! Generated 2 detailed diagrams:")
print("1. GNYANSETU_SYSTEM_ARCHITECTURE.png - Complete system architecture")
print("2. GNYANSETU_WORKFLOW_FLOWCHART.png - Detailed workflow flowchart")
print("="*80)
