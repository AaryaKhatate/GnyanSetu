import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  Minimize2,
  X,
  Volume2,
  VolumeX,
  Square,
  Layers,
  Wifi,
  WifiOff,
} from "lucide-react";
import TeachingCanvas from "./TeachingCanvas";
import TeachingCanvasFixed from "./TeachingCanvasFixed";
import KonvaTeachingBoard from "./KonvaTeachingBoard";
import { useTeachingWebSocket } from "./useTeachingWebSocket";

// Text-to-Speech Hook
const useTTS = () => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const speechSynthRef = useRef(null);

  const speak = useCallback((text, onEnd) => {
    if (!text || !window.speechSynthesis) {
      console.warn("Text-to-Speech not available");
      if (onEnd) onEnd();
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      console.error("Speech synthesis error");
      if (onEnd) onEnd();
    };

    speechSynthRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  const pauseResume = useCallback(() => {
    if (!window.speechSynthesis) return;

    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    } else if (isSpeaking && isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  }, [isSpeaking, isPaused]);

  const stop = useCallback(() => {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  }, []);

  return { speak, pauseResume, stop, isSpeaking, isPaused };
};

const Whiteboard = ({
  pdfName,
  onLessonComplete,
  onExit,
  onSlidesGenerated,
  onQuizDataReceived,
  isFullscreen,
  onToggleFullscreen,
  currentUserId,
  currentConversationId,
  onConversationCreated,
  pdfData, // Add PDF data prop for WebSocket
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [slides, setSlides] = useState([]);
  const [lessonSteps, setLessonSteps] = useState([]);
  const [chatMessage, setChatMessage] = useState("");
  
  // Teaching state variables
  const [teachingSteps, setTeachingSteps] = useState([]);
  const [currentTeachingStep, setCurrentTeachingStep] = useState(null);
  const [currentTeachingStepIndex, setCurrentTeachingStepIndex] = useState(0);
  const [isTeaching, setIsTeaching] = useState(false);
  const [teachingMode, setTeachingMode] = useState(true);
  const [currentSpeakingStep, setCurrentSpeakingStep] = useState(null);
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false);
  const [status, setStatus] = useState("Connecting...");
  const [quizData, setQuizData] = useState(null);
  const [notesData, setNotesData] = useState(null);
  const [autoPlay, setAutoPlay] = useState(true);
  
  // ✨ Visualization state - NEW!
  const [hasVisualization, setHasVisualization] = useState(false);
  const [visualizationScenes, setVisualizationScenes] = useState([]);
  const [currentVisualizationScene, setCurrentVisualizationScene] = useState(0);
  
  // Refs for managing state in callbacks
  const teachingStepsRef = useRef([]);
  const pdfSentRef = useRef(false); // Track if PDF has been sent
  
  // WebSocket integration - MUST be called before any useEffect that uses 'connected'
  const {
    connected,
    sessionId,
    messages,
    lessonCommands,
    currentStep,
    isPlaying: wsIsPlaying,
    sendPDFDocument,
    sendMessage,
    startLesson,
    stopLesson,
    sendTestPDF
  } = useTeachingWebSocket();

  // Expose test function globally for debugging
  useEffect(() => {
    window.sendTestPDF = sendTestPDF;
    window.testTeaching = () => {
      console.log('🧪 Testing teaching functionality...');
      if (connected) {
        sendTestPDF();
      } else {
        console.error('❌ WebSocket not connected');
      }
    };
    
    return () => {
      delete window.sendTestPDF;
      delete window.testTeaching;
    };
  }, [sendTestPDF, connected]);

  // REMOVED - Consolidated into single loader below

  // Handle lesson command execution on canvas
  const handleCommandExecuted = useCallback((command, stepIndex) => {
    console.log('Command executed on canvas:', command, 'Step:', stepIndex);
    
    // Execute command on canvas
    if (canvasRef.current && canvasRef.current.executeCommand) {
      canvasRef.current.executeCommand(command, stepIndex);
    }
  }, []);

  // Start lesson playback
  const handlePlayLesson = useCallback(() => {
    if (lessonCommands.length === 0) {
      console.warn('No lesson commands available');
      return;
    }
    
    console.log('Starting lesson with', lessonCommands.length, 'commands');
    
    // Clear canvas before starting
    if (canvasRef.current && canvasRef.current.clearCanvas) {
      canvasRef.current.clearCanvas();
    }
    
    // Start lesson execution
    startLesson(handleCommandExecuted);
  }, [lessonCommands, startLesson, handleCommandExecuted]);

  // Stop lesson playback
  const handleStopLesson = useCallback(() => {
    stopLesson();
  }, [stopLesson]);

  const canvasRef = useRef(null);
  const { speak, pauseResume, stop, isSpeaking, isPaused } = useTTS();

  // ============================================================
  // FETCH VISUALIZATION V2 - New Konva.js whiteboard format
  // ============================================================
  const fetchVisualizationV2 = async (lessonId) => {
    console.log('🎨 === FETCHING VISUALIZATION V2 ===');
    console.log('🎨 Lesson ID:', lessonId);
    
    try {
      const response = await fetch(`http://localhost:8006/visualization/v2/${lessonId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🎨 ✅ Fetched v2 visualization:', data);
      console.log('🎨 Teaching sequence steps:', data.teaching_sequence?.length || 0);
      
      // Convert v2 format to existing teaching steps format (keeps UI unchanged!)
      const convertedSteps = data.teaching_sequence.map((step, index) => ({
        step: index + 1,
        title: `Step ${index + 1}`, // Extract from first command if needed
        speech_text: step.tts_text || step.text_explanation || '',
        text_explanation: step.text_explanation || '',
        drawing_commands: step.whiteboard_commands || []
      }));
      
      console.log('🎨 ✅ Converted', convertedSteps.length, 'steps to existing format');
      console.log('🎨 First converted step:', convertedSteps[0]);
      
      return convertedSteps;
      
    } catch (error) {
      console.error('🎨 ❌ Error fetching visualization v2:', error);
      return null;
    }
  };

  // ============================================================
  // IMMEDIATE CHECK ON MOUNT - Force check sessionStorage
  // ============================================================
  useEffect(() => {
    console.log('🔥 === IMMEDIATE MOUNT CHECK ===');
    console.log('🔥 Component just mounted, checking sessionStorage immediately...');
    
    const loadLessonFromStorage = async () => {
      try {
        const lessonDataStr = sessionStorage.getItem('lessonData');
        console.log('🔥 sessionStorage lessonData exists:', !!lessonDataStr);
        
        if (lessonDataStr) {
          const lessonData = JSON.parse(lessonDataStr);
          console.log('🔥 Parsed lesson data:', lessonData);
          
          // ✨ PRIORITY 1: Try fetching v2 visualization if lessonId exists
          const lessonId = sessionStorage.getItem('lessonId');
          if (lessonId) {
            console.log('🎨 === ATTEMPTING V2 VISUALIZATION FETCH ===');
            console.log('🎨 Found lessonId in sessionStorage:', lessonId);
            
            const v2Steps = await fetchVisualizationV2(lessonId);
            
            if (v2Steps && v2Steps.length > 0) {
              console.log('🎨 ✅ SUCCESS! Using v2 visualization with', v2Steps.length, 'steps');
              setTeachingSteps(v2Steps);
              setStatus(`✨ Interactive lesson ready! ${v2Steps.length} steps prepared.`);
              setTeachingMode(true);
              
              // Also load quiz/notes if available
              if (lessonData.quiz_data) {
                setQuizData(lessonData.quiz_data);
              }
              if (lessonData.notes_data) {
                setNotesData(lessonData.notes_data);
              }
              
              console.log('🎨 ✅ V2 visualization loaded successfully!');
              return true;
            } else {
              console.log('🎨 ⚠️ V2 fetch failed, falling back to old format');
            }
          }
          
          // ✨ PRIORITY 2: Check for OLD visualization data (fallback)
          if (lessonData.visualization_data && lessonData.visualization_data.scenes) {
            console.log('✨✨✨ OLD VISUALIZATION DATA FOUND! ✨✨✨');
            console.log('✨ Topic:', lessonData.visualization_data.topic);
            console.log('✨ Scenes:', lessonData.visualization_data.scenes.length);
            console.log('✨ First scene:', lessonData.visualization_data.scenes[0]);
            
            setHasVisualization(true);
            setVisualizationScenes(lessonData.visualization_data.scenes);
            setTeachingMode(true);
            setStatus(`✨ Interactive visualization ready! ${lessonData.visualization_data.scenes.length} scenes`);
            
            // Also load quiz/notes if available
            if (lessonData.quiz_data) {
              setQuizData(lessonData.quiz_data);
            }
            if (lessonData.notes_data) {
              setNotesData(lessonData.notes_data);
            }
            
            console.log('✨ OLD Visualization mode activated!');
            return true;
          }
          
          console.log('🔥 Has teaching_steps:', !!lessonData.teaching_steps);
          console.log('🔥 Teaching steps count:', lessonData.teaching_steps?.length);
          
          // ✅ NEW: If teaching_steps doesn't exist, create them from lesson_content
          if (!lessonData.teaching_steps && (lessonData.lesson_content || lessonData.content)) {
            console.log('🔥 ⚠️ No teaching_steps found, generating from lesson_content...');
            
            // Use lesson_content or content field
            const content = lessonData.lesson_content || lessonData.content;
            console.log('🔥 Content to parse:', content?.substring(0, 200));
            
            // Try splitting by level-3 headers (###) first for subsections
            let sections = content.split(/\n### /).filter(s => s.trim());
            
            // If no subsections found, try level-2 headers (##)
            if (sections.length <= 1) {
              sections = content.split(/\n## /).filter(s => s.trim());
            }
            
            console.log('🔥 Found', sections.length, 'sections');
            
            const steps = sections
              .filter(section => section.trim().length > 0)
              .map((section, index) => {
                const lines = section.split('\n');
                const title = lines[0].replace(/^#+ /, '').trim();
                const contentText = lines.slice(1).join('\n').trim();
                
                // Clean up the content for speech
                const speechText = contentText
                  .replace(/[#*_`]/g, '') // Remove markdown symbols
                  .replace(/\n+/g, ' ')   // Replace newlines with spaces
                  .substring(0, 500);     // Limit to 500 chars
                
                return {
                  step: index + 1,
                  title: title,
                  speech_text: `${title}. ${speechText}`,
                  text_explanation: contentText,
                  drawing_commands: [
                    {
                      type: "text",
                      action: "write_text",
                      text: title,
                      x_percent: 10,
                      y_percent: 10,
                      font_size: 32,
                      color: "#1e40af",
                      time: 0
                    },
                    {
                      type: "text",
                      action: "write_text",
                      text: contentText.substring(0, 200) + "...",
                      x_percent: 10,
                      y_percent: 25,
                      font_size: 18,
                      color: "#1f2937",
                      time: 500
                    }
                  ]
                };
              });
            
            lessonData.teaching_steps = steps;
            console.log('🔥 ✅ Generated', steps.length, 'teaching steps from content');
            console.log('🔥 First step:', steps[0]);
            console.log('🔥 First step title:', steps[0]?.title);
            console.log('🔥 First step speech:', steps[0]?.speech_text?.substring(0, 100));
          }
          
          if (lessonData.teaching_steps && lessonData.teaching_steps.length > 0) {
            console.log('🔥 ✅ FOUND LESSON DATA ON MOUNT!');
            console.log('🔥 Loading', lessonData.teaching_steps.length, 'steps immediately');
            
            setTeachingSteps(lessonData.teaching_steps);
            setTeachingMode(true);
            setStatus(`Lesson loaded! ${lessonData.teaching_steps.length} steps ready.`);
            
            console.log('🔥 State updated immediately on mount');
            return true;
          }
        } else {
          console.log('🔥 No lesson data in sessionStorage on mount');
        }
      } catch (error) {
        console.error('🔥 Error in immediate mount check:', error);
      }
      return false;
    };
    
    // Try immediately (now async)
    loadLessonFromStorage();
    
    console.log('🔥 === END IMMEDIATE MOUNT CHECK ===');
  }, []); // Empty dependency array - run once on mount

  // Debug: Monitor canvas ref
  useEffect(() => {
    console.log('🔍 === CANVAS REF DEBUG ===');
    console.log('🔍 canvasRef.current:', canvasRef.current);
    console.log('🔍 canvasRef.current exists:', !!canvasRef.current);
    if (canvasRef.current) {
      console.log('🔍 canvasRef methods:', Object.keys(canvasRef.current));
      console.log('🔍 clearCanvas method:', typeof canvasRef.current.clearCanvas);
      console.log('🔍 addDrawingCommand method:', typeof canvasRef.current.addDrawingCommand);
    }
    console.log('🔍 === END CANVAS REF DEBUG ===');
  }, [canvasRef.current]);

  // Define startTeachingStep function before its usage
  const startTeachingStep = useCallback(
    (step, stepIndex) => {
      if (!step) {
        console.error("❌ No step provided to startTeachingStep");
        return;
      }

      console.log(`🎯 === STARTING STEP ${stepIndex + 1} ===`);
      console.log("Step object:", step);
      console.log("Speech text:", step.speech_text);
      console.log("Speech text type:", typeof step.speech_text);
      console.log(
        "Speech text empty?",
        !step.speech_text || step.speech_text.trim() === ""
      );
      console.log("Drawing commands:", step.drawing_commands);
      console.log("Drawing commands count:", step.drawing_commands?.length);

      console.log(`⚙️ Setting current teaching step to:`, step);
      setCurrentSpeakingStep(step.step);
      setCurrentTeachingStepIndex(stepIndex !== undefined ? stepIndex : 0);
      setCurrentTeachingStep(step);
      console.log(`⚙️ Current teaching step state updated`);
      setIsTeaching(true); // Ensure we're in teaching mode
      console.log(`⚙️ isTeaching set to true`);

      // Clear canvas for new step
      if (canvasRef.current && typeof canvasRef.current.clearCanvas === 'function') {
        canvasRef.current.clearCanvas();
        console.log("🎨 Canvas cleared for step", stepIndex + 1);
      } else {
        console.warn("⚠️ Canvas clearCanvas method not available");
      }

      // Validate and prepare speech text
      let speechText = step.speech_text;
      if (!speechText || speechText.trim() === "") {
        console.warn("⚠️ Empty speech text for step", stepIndex + 1);
        console.log("Raw speech_text value:", JSON.stringify(step.speech_text));

        // Try to find alternative text
        if (step.text_explanation) {
          console.log(
            "📝 Using text_explanation as fallback:",
            step.text_explanation
          );
          speechText = step.text_explanation;
        } else {
          console.error(
            "❌ No valid speech content found for step",
            stepIndex + 1
          );
          speechText = `This is step ${
            stepIndex + 1
          } of the lesson. Let's continue with the next concept.`;
        }
      }

      // Execute drawing commands first
      if (step.drawing_commands && step.drawing_commands.length > 0) {
        console.log(
          `🎨 Executing ${step.drawing_commands.length} drawing commands`
        );
        console.log(`🎨 ===== DRAWING COMMANDS DEBUG =====`);
        console.log(`🎨 canvasRef.current EXISTS:`, !!canvasRef.current);
        console.log(`🎨 Full drawing commands array:`, JSON.stringify(step.drawing_commands, null, 2));
        
        step.drawing_commands.forEach((command, index) => {
          console.log(`🎨 Drawing command ${index + 1}:`, command);
          console.log(`🎨   Command type:`, command.type);
          console.log(`🎨   Command action:`, command.action);
          console.log(`🎨   Command structure:`, Object.keys(command));
          
          // NOTE: TeachingCanvas handles drawing animation internally via useEffect
          // No need to manually call addDrawingCommand here - it causes duplicates!
          // The canvas will automatically render drawing_commands when isPlaying=true
        });
        console.log(`🎨 ===== END DRAWING COMMANDS DEBUG =====`);
      } else {
        console.warn("⚠️ No drawing commands for step", stepIndex + 1);
        console.log("⚠️ Step object structure:", Object.keys(step));
        console.log("⚠️ step.drawing_commands value:", step.drawing_commands);
      }

      // Start speech with proper completion callback
      console.log(
        `🗣️ Starting speech for step ${stepIndex + 1}:`,
        speechText.substring(0, 100) + "..."
      );
      console.log(`🎮 AutoPlay enabled:`, autoPlay);
      console.log(`📊 Teaching steps length:`, teachingSteps.length);
      setStatus(`Teaching step ${stepIndex + 1} of ${teachingSteps.length}`);

      speak(
        speechText,
        () => {
          console.log(`✅ Step ${stepIndex + 1} speech completed`);
          console.log(
            `🔍 Completion callback triggered for step ${stepIndex + 1}`
          );
          setCurrentSpeakingStep(null);

          // Auto-advance to next step
          const nextStepIndex = stepIndex + 1;
          const currentTeachingSteps = teachingStepsRef.current; // Use ref to get latest state
          console.log(`📈 Next step index would be: ${nextStepIndex}`);
          console.log(
            `📏 Total steps available: ${currentTeachingSteps.length}`
          );
          console.log(`🎮 AutoPlay status: ${autoPlay}`);

          if (nextStepIndex < currentTeachingSteps.length && autoPlay) {
            console.log(`⏭️ Auto-advancing to step ${nextStepIndex + 1}`);
            console.log(
              `🎯 Next step object:`,
              currentTeachingSteps[nextStepIndex]
            );
            setTimeout(() => {
              console.log(`🚀 Actually starting step ${nextStepIndex + 1} now`);
              startTeachingStep(
                currentTeachingSteps[nextStepIndex],
                nextStepIndex
              );
            }, 1500); // 1.5 second pause between steps
          } else if (nextStepIndex >= currentTeachingSteps.length) {
            console.log("🎉 All steps completed!");
            setStatus("Lesson completed! Great job!");
            setIsTeaching(false);
            speak("Lesson completed. Great job!", () => {
              console.log("🏁 Lesson completion message finished");
            });
          } else {
            console.log("⏸️ Auto-play disabled, waiting for manual advance");
            console.log(
              `❌ AutoPlay: ${autoPlay}, NextIndex: ${nextStepIndex}, TotalSteps: ${currentTeachingSteps.length}`
            );
            setStatus(
              `Step ${stepIndex + 1} complete. Click Next to continue.`
            );
          }
        },
        true
      );

      console.log(`=== STEP ${stepIndex + 1} SETUP COMPLETE ===`);
    },
    [speak, autoPlay, stop] // Remove teachingSteps from dependencies to avoid stale closure
  );

  // Update ref whenever teachingSteps changes & Auto-start trigger
  useEffect(() => {
    teachingStepsRef.current = teachingSteps;
    console.log('📊 teachingSteps updated:', teachingSteps.length, 'steps');
    
    // Auto-start if we just got steps and haven't started yet
    if (teachingSteps.length > 0 && !isTeaching && !pdfSentRef.current && connected) {
      console.log('🚀 AUTO-START TRIGGER: Steps loaded, starting lesson...');
      pdfSentRef.current = true; // Mark as processed
      
      setTimeout(() => {
        console.log('🎬 AUTO-START: Starting first step');
        startTeachingStep(teachingSteps[0], 0);
      }, 2000);
    }
  }, [teachingSteps, isTeaching, connected, startTeachingStep]);

  // ============================================================
  // SINGLE, CLEAN LESSON DATA LOADER
  // This is the ONLY place where we load teaching steps
  // ============================================================
  useEffect(() => {
    console.log('🎯 === SINGLE LESSON LOADER ===');
    console.log('🎯 Connected:', connected);
    console.log('🎯 Already processed:', pdfSentRef.current);
    console.log('🎯 Current teachingSteps:', teachingSteps.length);
    console.log('🎯 pdfData:', pdfData);
    console.log('🎯 pdfData exists:', !!pdfData);
    console.log('🎯 pdfData.lessonData:', pdfData?.lessonData);
    console.log('🎯 pdfData.lessonData exists:', !!pdfData?.lessonData);
    console.log('🎯 teaching_steps:', pdfData?.lessonData?.teaching_steps);
    console.log('🎯 teaching_steps count:', pdfData?.lessonData?.teaching_steps?.length || 0);
    
    // Only run when connected
    if (!connected) {
      console.log('⏭️ Skipping: Not connected');
      return;
    }
    
    // Skip if already processed AND we already have steps
    if (pdfSentRef.current && teachingSteps.length > 0) {
      console.log('⏭️ Skipping: Already processed and have teaching steps');
      return;
    }
    
    // IIFE to handle async operations
    (async () => {
      // Try to load lesson data from multiple sources
      let lessonSteps = null;
      let dataSource = 'none';
      
      // Source 0: Try v2 API first if lessonId exists in sessionStorage
      const lessonId = sessionStorage.getItem('lessonId');
      if (lessonId && !pdfSentRef.current) {
        console.log('🎨 === ATTEMPTING V2 API FETCH IN LOADER ===');
        console.log('🎨 Lesson ID from sessionStorage:', lessonId);
        
        const v2Steps = await fetchVisualizationV2(lessonId);
        
        if (v2Steps && v2Steps.length > 0) {
          console.log('🎨 ✅ SUCCESS! Loaded', v2Steps.length, 'steps from v2 API');
          lessonSteps = v2Steps;
          dataSource = 'visualizationV2API';
        } else {
          console.log('🎨 ⚠️ V2 API fetch failed, trying other sources...');
        }
      }
      
      // Source 1: pdfData prop (if v2 didn't work)
      if (!lessonSteps && pdfData?.lessonData?.teaching_steps?.length > 0) {
        console.log('✅ Found lesson in pdfData prop:', pdfData.lessonData.teaching_steps.length, 'steps');
        lessonSteps = pdfData.lessonData.teaching_steps;
        dataSource = 'pdfData';
      }
      // Source 2: sessionStorage (backup)
      else if (!lessonSteps) {
        console.log('🔍 Checking sessionStorage for lesson data...');
        try {
          const lessonDataStr = sessionStorage.getItem('lessonData');
          console.log('🔍 sessionStorage lessonData string:', lessonDataStr?.substring(0, 200));
          if (lessonDataStr) {
            const lessonData = JSON.parse(lessonDataStr);
            console.log('🔍 Parsed lessonData:', lessonData);
            if (lessonData?.teaching_steps?.length > 0) {
              console.log('✅ Found lesson in sessionStorage:', lessonData.teaching_steps.length, 'steps');
              lessonSteps = lessonData.teaching_steps;
              dataSource = 'sessionStorage';
            } else {
              console.log('❌ sessionStorage lessonData has no teaching_steps');
            }
          } else {
            console.log('❌ No lessonData in sessionStorage');
          }
        } catch (error) {
          console.error('❌ Error loading from sessionStorage:', error);
        }
      }
    
      // If we found lesson steps, use them
      if (lessonSteps && lessonSteps.length > 0) {
        console.log('✅ ✨ LOADING', lessonSteps.length, 'TEACHING STEPS FROM', dataSource.toUpperCase(), '!');
        console.log('📚 First step:', lessonSteps[0]);
        console.log('📚 First step keys:', Object.keys(lessonSteps[0]));
        console.log('📚 First step speech_text:', lessonSteps[0].speech_text?.substring(0, 100));
        
        setTeachingSteps(lessonSteps);
        setStatus(`Lesson ready! ${lessonSteps.length} steps prepared.`);
        setTeachingMode(true);
        pdfSentRef.current = true;
        
        console.log('✅ State updated: teachingSteps set, teachingMode=true, pdfSentRef=true');
        
        // Auto-start the lesson
        console.log('🚀 Auto-starting lesson in 2 seconds...');
        setTimeout(() => {
          console.log('🎬 STARTING FIRST STEP NOW!');
          console.log('🎬 Step to start:', lessonSteps[0]);
          startTeachingStep(lessonSteps[0], 0);
        }, 2000);
      }
      // Otherwise, send PDF to teaching service for generation
      else if (pdfData && !pdfSentRef.current) {
        console.log('❌ No pre-generated lesson, sending PDF to Teaching Service...');
        console.log('📤 PDF data to send:', {
          topic: pdfData.topic,
          pdf_filename: pdfData.pdf_filename,
          pdf_text_length: pdfData.pdf_text?.length,
          has_lessonData: !!pdfData.lessonData
        });
        setTimeout(() => {
          sendPDFDocument(pdfData);
          pdfSentRef.current = true;
          console.log('✅ PDF sent to Teaching Service, pdfSentRef=true');
        }, 500);
      } else {
        console.log('❌ No pdfData available or already sent');
        console.log('   - pdfData:', !!pdfData);
        console.log('   - pdfSentRef.current:', pdfSentRef.current);
      }
      
      console.log('🎯 === END SINGLE LESSON LOADER ===');
    })(); // End of async IIFE
    
  }, [connected, pdfData, teachingSteps.length, sendPDFDocument, startTeachingStep, fetchVisualizationV2]); // Added fetchVisualizationV2 to dependencies

  // Execute whiteboard commands for canvas drawing
  const executeWhiteboardCommands = (commands) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    commands.forEach((cmd) => {
      switch (cmd.action) {
        case "clear_all":
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          break;

        case "write_text":
          ctx.font = `${cmd.font_size || 20}px Arial`;
          ctx.fillStyle = cmd.color || "black";
          ctx.textAlign = cmd.align || "left";
          const x = (cmd.x_percent / 100) * canvas.width;
          const y = (cmd.y_percent / 100) * canvas.height;
          ctx.fillText(cmd.text, x, y);
          break;

        case "draw_shape":
          ctx.strokeStyle = cmd.stroke || "black";
          ctx.fillStyle = cmd.color || "#f3f4f6";
          const shapeX = (cmd.x_percent / 100) * canvas.width;
          const shapeY = (cmd.y_percent / 100) * canvas.height;
          const width = (cmd.width_percent / 100) * canvas.width;
          const height = (cmd.height_percent / 100) * canvas.height;

          if (cmd.shape === "rect") {
            ctx.fillRect(shapeX, shapeY, width, height);
            ctx.strokeRect(shapeX, shapeY, width, height);
          } else if (cmd.shape === "circle") {
            ctx.beginPath();
            ctx.arc(
              shapeX + width / 2,
              shapeY + height / 2,
              Math.min(width, height) / 2,
              0,
              2 * Math.PI
            );
            ctx.fill();
            ctx.stroke();
          }
          break;

        case "draw_arrow":
          if (cmd.points && cmd.points.length === 4) {
            ctx.strokeStyle = cmd.color || "black";
            ctx.lineWidth = 2;
            const [x1, y1, x2, y2] = cmd.points.map((p, i) =>
              i % 2 === 0 ? (p / 100) * canvas.width : (p / 100) * canvas.height
            );

            // Draw line
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            // Draw arrowhead
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const arrowLength = 10;
            ctx.beginPath();
            ctx.moveTo(x2, y2);
            ctx.lineTo(
              x2 - arrowLength * Math.cos(angle - Math.PI / 6),
              y2 - arrowLength * Math.sin(angle - Math.PI / 6)
            );
            ctx.moveTo(x2, y2);
            ctx.lineTo(
              x2 - arrowLength * Math.cos(angle + Math.PI / 6),
              y2 - arrowLength * Math.sin(angle + Math.PI / 6)
            );
            ctx.stroke();
          }
          break;
      }
    });
  };

  // Auto-advance slides
  useEffect(() => {
    if (!isPlaying || slides.length === 0) return;

    const timer = setTimeout(() => {
      if (currentSlide < slides.length - 1) {
        setCurrentSlide(currentSlide + 1);
      } else {
        // End of lesson
        setIsPlaying(false);
        setStatus("Lesson completed!");
      }
    }, 4000);

    return () => clearTimeout(timer);
  }, [currentSlide, isPlaying, slides.length]);

  // Execute whiteboard commands when slide changes
  useEffect(() => {
    if (slides[currentSlide] && slides[currentSlide].commands) {
      executeWhiteboardCommands(slides[currentSlide].commands);
    }
  }, [currentSlide]);

  // Generate slides as images
  const generateSlides = async () => {
    const slideImages = [];

    for (let i = 0; i < slides.length; i++) {
      const slideData = slides[i];
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      // Set canvas size
      canvas.width = 1200;
      canvas.height = 800;

      // Background
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Add some styling to make it look like a proper slide
      ctx.fillStyle = "#1e40af";
      ctx.fillRect(0, 0, canvas.width, 100);

      // Title
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 48px Arial";
      ctx.textAlign = "center";
      ctx.fillText(slideData.title, canvas.width / 2, 60);

      // Content
      ctx.fillStyle = "#1f2937";
      ctx.font = "32px Arial";
      ctx.textAlign = "center";
      ctx.fillText(slideData.content, canvas.width / 2, canvas.height / 2);

      // Footer
      ctx.fillStyle = "#6b7280";
      ctx.font = "24px Arial";
      ctx.textAlign = "center";
      ctx.fillText(
        `Slide ${i + 1} of ${slides.length}`,
        canvas.width / 2,
        canvas.height - 50
      );

      // Convert to blob
      const blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, "image/png")
      );
      slideImages.push({
        title: slideData.title,
        image: blob,
        filename: `slide-${i + 1}-${slideData.title
          .toLowerCase()
          .replace(/\s+/g, "-")}.png`,
      });
    }

    // Pass slides to parent component
    onSlidesGenerated(slideImages);
  };

  const handleSlideClick = (slideIndex) => {
    setCurrentSlide(slideIndex);
  };

  const rewind = () => {
    setCurrentSlide((prev) => Math.max(0, prev - 1));
  };

  const forward = () => {
    // Only allow forward if we're not on the latest slide
    setCurrentSlide((prev) => {
      if (prev < slides.length - 1) {
        return prev + 1;
      }
      return prev; // Stay on current slide if already at the last one
    });
  };

  // Manual speak function for current slide
  const speakCurrentSlide = useCallback(() => {
    if (slides[currentSlide] && slides[currentSlide].tts_text) {
      setCurrentSpeakingStep(currentSlide + 1);
      speak(slides[currentSlide].tts_text, () => {
        setCurrentSpeakingStep(null);
      });
    }
  }, [slides, currentSlide, speak]);

  // Teaching step management functions
  // Synchronized lesson playback functions
  const startSynchronizedLesson = useCallback((steps) => {
    if (!steps || steps.length === 0) return;

    console.log(`Starting synchronized lesson with ${steps.length} steps`);
    setCurrentTeachingStepIndex(0);
    setStatus("Lesson starting...");

    // Start with first step
    setTimeout(() => {
      startTeachingStep(steps[0], 0);
    }, 1000);
  }, []);

  const playLesson = useCallback(() => {
    if (teachingSteps.length > 0) {
      startSynchronizedLesson(teachingSteps);
    }
  }, [teachingSteps, startSynchronizedLesson]);

  const pauseLesson = useCallback(() => {
    stop(); // Stop current speech
    setStatus("Lesson paused");
  }, [stop]);

  const nextStep = useCallback(() => {
    const nextIndex = currentTeachingStepIndex + 1;
    if (nextIndex < teachingSteps.length) {
      stop(); // Stop current speech
      startTeachingStep(teachingSteps[nextIndex], nextIndex);
    }
  }, [currentTeachingStepIndex, teachingSteps, stop]);

  const previousStep = useCallback(() => {
    const prevIndex = currentTeachingStepIndex - 1;
    if (prevIndex >= 0) {
      stop(); // Stop current speech
      startTeachingStep(teachingSteps[prevIndex], prevIndex);
    }
  }, [currentTeachingStepIndex, teachingSteps, stop]);

  // Legacy startTeachingStep function for backward compatibility
  const startTeachingStepLegacy = useCallback(
    (step) => {
      if (!step) {
        console.log("No step provided to startTeachingStep");
        return;
      }

      console.log(
        "Starting teaching step:",
        step.step,
        "Speech text:",
        step.speech_text?.substring(0, 50) + "..."
      );
      setCurrentSpeakingStep(step.step);

      // Ensure we have speech text
      const speechText =
        step.speech_text || "Let me explain this concept to you.";

      // Start speech with improved error handling
      speak(speechText, () => {
        console.log("Speech completed for step:", step.step);
        setCurrentSpeakingStep(null);

        // Auto-advance to next step if available
        const currentIndex = teachingSteps.findIndex(
          (s) => s.step === step.step
        );
        console.log(
          "Current step index:",
          currentIndex,
          "Total steps:",
          teachingSteps.length
        );

        if (currentIndex >= 0 && currentIndex < teachingSteps.length - 1) {
          setTimeout(() => {
            const nextStep = teachingSteps[currentIndex + 1];
            console.log("Auto-advancing to next step:", nextStep.step);
            setCurrentTeachingStep(nextStep);
            startTeachingStepLegacy(nextStep);
          }, 1500); // 1.5 second pause between steps
        } else {
          console.log("No more steps to advance to, ending teaching session");
          setIsTeaching(false);
        }
      });
    },
    [speak, teachingSteps]
  );

  const handleTeachingStepComplete = useCallback(() => {
    console.log("Teaching step drawing completed");
    // Drawing animation completed, but speech might still be ongoing
  }, []);

  const switchToTeachingMode = useCallback(() => {
    setTeachingMode(true);
    // Start with first teaching step if available
    if (teachingSteps.length > 0 && !isTeaching) {
      setCurrentTeachingStep(teachingSteps[0]);
      setIsTeaching(true);
      startTeachingStep(teachingSteps[0]);
    }
  }, [teachingSteps, isTeaching, startTeachingStep]);

  const switchToSlideMode = useCallback(() => {
    setTeachingMode(false);
    stop(); // Stop any ongoing speech
    setIsTeaching(false);
    setCurrentTeachingStep(null);
  }, [stop]);

  // Handle sending chat messages to teaching service
  const handleSendMessage = useCallback(() => {
    if (!chatMessage.trim() || !connected) return;
    
    console.log('📤 Sending message to teaching service:', chatMessage);
    sendMessage(chatMessage);
    setChatMessage(''); // Clear input
  }, [chatMessage, connected, sendMessage]);

  return (
    <div
      className={`relative h-screen overflow-hidden ${
        isFullscreen ? "h-full" : ""
      }`}
    >
      {/* Top Bar - Only show in normal mode */}
      {!isFullscreen && (
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex items-center justify-between p-4 border-b border-slate-700/40 bg-slate-800/60 backdrop-blur-sm"
        >
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold text-white">
              Lesson: {pdfName}
            </h1>
            {/* WebSocket Connection Status */}
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                connected
                  ? "bg-green-500/20 text-green-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
              {connected ? "● Teaching Service Connected" : "● Teaching Service Disconnected"}
            </div>
            {sessionId && (
              <div className="text-xs text-slate-400">
                Session: {sessionId}
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-slate-300 text-sm">{status}</span>
            
            {/* Interactive Teaching Mode Button */}
            {teachingSteps.length > 0 && (
              <button
                onClick={() => {
                  const lessonId = sessionStorage.getItem('lessonId');
                  if (lessonId) {
                    window.location.href = `/teaching/${lessonId}`;
                  } else {
                    window.location.href = '/teaching';
                  }
                }}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg text-sm font-semibold text-white shadow-lg transform transition hover:scale-105"
                title="Open Interactive Teaching Mode"
              >
                🎓 Start Interactive Teaching
              </button>
            )}

            {/* WebSocket Lesson Controls */}
            {connected && lessonCommands.length > 0 && (
              <div className="flex items-center gap-2 border-l border-slate-600 pl-3">
                <button
                  onClick={handlePlayLesson}
                  disabled={isPlaying || wsIsPlaying}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Start AI lesson"
                >
                  ▶️ Play AI Lesson
                </button>

                <button
                  onClick={handleStopLesson}
                  disabled={!isPlaying && !wsIsPlaying}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Stop lesson"
                >
                  ⏹️ Stop
                </button>
                
                <span className="text-xs text-slate-400">
                  {currentStep}/{lessonCommands.length} steps
                </span>
              </div>
            )}

            {/* Audio Controls */}
            <div className="flex items-center gap-2 border-l border-slate-600 pl-3">
              <button
                onClick={() => setAutoPlay(!autoPlay)}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  autoPlay
                    ? "bg-green-600 hover:bg-green-700 text-white"
                    : "bg-slate-600 hover:bg-slate-500 text-slate-300"
                }`}
                title={`Auto-speak: ${autoPlay ? "ON" : "OFF"}`}
              >
                <Volume2 size={14} />
              </button>

              <button
                onClick={speakCurrentSlide}
                disabled={isSpeaking}
                className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs disabled:opacity-50 transition-colors"
                title="Speak current slide"
              >
                🔊
              </button>

              <button
                onClick={pauseResume}
                disabled={!isSpeaking}
                className="px-2 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-xs disabled:opacity-50 transition-colors"
                title={isPaused ? "Resume" : "Pause"}
              >
                {isPaused ? "▶️" : "⏸️"}
              </button>

              <button
                onClick={stop}
                disabled={!isSpeaking}
                className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs disabled:opacity-50 transition-colors"
                title="Stop speaking"
              >
                <Square size={12} />
              </button>

              {currentSpeakingStep && (
                <span className="text-xs text-blue-300">
                  🔊 Step {currentSpeakingStep}
                </span>
              )}
            </div>

            {/* Mode Toggle */}
            <div className="flex items-center gap-2 border-l border-slate-600 pl-3">
              <button
                onClick={
                  teachingMode ? switchToSlideMode : switchToTeachingMode
                }
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  teachingMode
                    ? "bg-purple-600 hover:bg-purple-700 text-white"
                    : "bg-slate-600 hover:bg-slate-500 text-slate-300"
                }`}
                title={`Mode: ${
                  teachingMode ? "Interactive Teaching" : "Static Slides"
                }`}
              >
                <Layers size={14} className="mr-1" />
                {teachingMode ? "Teaching" : "Slides"}
              </button>

              {/* ✨ Visualization Progress Indicator */}
              {hasVisualization && (
                <span className="text-xs text-purple-300 font-medium">
                  ✨ Scene {currentVisualizationScene + 1} / {visualizationScenes.length}
                </span>
              )}

              {teachingSteps.length > 0 && !hasVisualization && (
                <span className="text-xs text-slate-400">
                  {teachingSteps.length} steps
                </span>
              )}
            </div>

            {/* Synchronized Teaching Controls */}
            {teachingMode && teachingSteps.length > 0 && (
              <div className="flex items-center gap-2 border-l border-slate-600 pl-3">
                <button
                  onClick={playLesson}
                  disabled={isSpeaking}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Start lesson"
                >
                  ▶️ Play
                </button>

                <button
                  onClick={pauseLesson}
                  disabled={!isSpeaking}
                  className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Pause lesson"
                >
                  ⏸️ Pause
                </button>

                <button
                  onClick={previousStep}
                  disabled={currentTeachingStepIndex <= 0 || isSpeaking}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Previous step"
                >
                  ⏮️ Prev
                </button>

                <button
                  onClick={nextStep}
                  disabled={
                    currentTeachingStepIndex >= teachingSteps.length - 1 ||
                    isSpeaking
                  }
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Next step"
                >
                  ⏭️ Next
                </button>

                <span className="text-sm text-slate-400">
                  Step {currentTeachingStepIndex + 1} / {teachingSteps.length}
                </span>
              </div>
            )}

            {/* Quiz button - show when lesson is completed and quiz data is available */}
            {!isPlaying && quizData && (
              <button
                onClick={() => {
                  if (onQuizDataReceived) {
                    onQuizDataReceived(quizData, notesData);
                  }
                  onLessonComplete();
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Start Quiz
              </button>
            )}

            <button
              onClick={onToggleFullscreen}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Maximize2 size={18} />
              Full Screen
            </button>
            <button
              onClick={onExit}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors mr-4"
            >
              <X size={18} />
              Exit
            </button>
          </div>
        </motion.div>
      )}

      {/* Whiteboard Area - Non-scrollable */}
      <div
        className={`flex flex-col items-center justify-center p-8 overflow-hidden ${
          isFullscreen ? "h-full" : "h-[calc(100vh-80px)]"
        }`}
      >
        <motion.div
          key={
            teachingMode
              ? `teaching-${currentTeachingStep?.step || 0}`
              : `slide-${currentSlide}`
          }
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className={`w-full aspect-video bg-white rounded-xl shadow-2xl flex items-center justify-center relative ${
            isFullscreen ? "max-w-none max-h-none h-full" : "max-w-4xl"
          }`}
        >
          {teachingMode ? (
            /* Interactive Teaching Canvas */
            <>
              {console.log('🎨 === RENDERING TEACHING CANVAS ===')}
              {console.log('🎨 teachingMode:', teachingMode)}
              {console.log('🎨 hasVisualization:', hasVisualization)}
              {console.log('🎨 visualizationScenes:', visualizationScenes.length)}
              {console.log('🎨 currentTeachingStep:', currentTeachingStep)}
              {console.log('🎨 === END RENDERING DEBUG ===')}
              
              {hasVisualization ? (
                /* ✨ NEW: Konva Visualization Mode with Images & Animations */
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
                  {console.log('✨ Rendering KonvaTeachingBoard with', visualizationScenes.length, 'scenes')}
                  <KonvaTeachingBoard
                    scenes={visualizationScenes}
                    autoPlay={autoPlay}
                    onSceneComplete={(sceneIndex) => {
                      console.log('✨ Scene completed:', sceneIndex);
                      setCurrentVisualizationScene(sceneIndex + 1);
                      
                      // Speak scene completion
                      if (autoPlay) {
                        speak(`Scene ${sceneIndex + 1} completed.`);
                      }
                      
                      // If all scenes completed, offer quiz
                      if (sceneIndex >= visualizationScenes.length - 1) {
                        console.log('✨ All visualization scenes completed!');
                        setStatus('Visualization complete! Ready for quiz.');
                        
                        if (quizData && onQuizDataReceived) {
                          setTimeout(() => {
                            onQuizDataReceived(quizData, notesData);
                          }, 2000);
                        }
                      }
                    }}
                  />
                </div>
              ) : (
                /* Fallback: Original Teaching Canvas */
                <TeachingCanvasFixed
                  ref={canvasRef}
                  teachingStep={currentTeachingStep}
                  isPlaying={isTeaching || isPlaying}
                  onStepComplete={handleTeachingStepComplete}
                  canvasWidth={isFullscreen ? window.innerWidth * 0.9 : 800}
                  canvasHeight={isFullscreen ? window.innerHeight * 0.7 : 600}
                  lessonCommands={lessonCommands}
                  onCommandExecuted={handleCommandExecuted}
                />
              )}
            </>
          ) : connected && lessonCommands.length > 0 ? (
            /* WebSocket AI Teaching Mode */
            <div className="w-full h-full relative">
              <TeachingCanvasFixed
                ref={canvasRef}
                teachingStep={null}
                isPlaying={isPlaying || wsIsPlaying}
                onStepComplete={() => console.log('AI lesson step complete')}
                canvasWidth={isFullscreen ? window.innerWidth * 0.9 : 800}
                canvasHeight={isFullscreen ? window.innerHeight * 0.7 : 600}
                lessonCommands={lessonCommands}
                onCommandExecuted={handleCommandExecuted}
              />
              
              {/* Chat overlay for AI interaction */}
              <div className="absolute bottom-4 right-4 w-80 bg-white/90 backdrop-blur rounded-lg p-4 shadow-lg">
                <div className="h-40 overflow-y-auto mb-3 text-sm">
                  {messages.slice(-5).map((msg, index) => (
                    <div key={index} className={`mb-2 ${
                      msg.type === 'user' ? 'text-blue-600' : 
                      msg.type === 'teacher' ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      <strong>{msg.type === 'user' ? 'You' : msg.type === 'teacher' ? 'AI Teacher' : 'System'}:</strong> {msg.message}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask the AI teacher..."
                    className="flex-1 px-2 py-1 border rounded text-sm"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!chatMessage.trim()}
                    className="px-3 py-1 bg-blue-500 text-white rounded text-sm disabled:opacity-50"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Traditional Slide Mode */
            <>
              {/* Canvas for whiteboard commands */}
              <canvas
                ref={canvasRef}
                width={1200}
                height={800}
                className="absolute inset-0 w-full h-full"
                style={{ imageRendering: "crisp-edges" }}
              />

              {/* Content overlay */}
              <div className="relative z-10 text-center p-8">
                {slides.length > 0 && slides[currentSlide] ? (
                  <>
                    <h2
                      className={`font-bold text-slate-800 mb-4 ${
                        isFullscreen ? "text-4xl mb-6" : "text-3xl"
                      }`}
                    >
                      {slides[currentSlide].title}
                    </h2>
                    <p
                      className={`text-slate-600 ${
                        isFullscreen ? "text-2xl leading-relaxed" : "text-xl"
                      }`}
                    >
                      {slides[currentSlide].content}
                    </p>
                  </>
                ) : (
                  <div className="text-slate-400">
                    <div className="text-6xl mb-4">📚</div>
                    <p className="text-xl">Upload a PDF to start your lesson</p>
                  </div>
                )}
              </div>
            </>
          )}
        </motion.div>
      </div>

      {/* Control Bar - Always centered horizontally */}
      {slides.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`fixed bottom-20 left-1/2 transform -translate-x-1/2 flex items-center justify-center gap-4 bg-slate-800/80 backdrop-blur-sm rounded-full px-6 py-3 border border-slate-700/40 z-50 ${
            isFullscreen
              ? "opacity-0 hover:opacity-100 transition-opacity duration-300"
              : ""
          }`}
        >
          <button
            onClick={rewind}
            disabled={currentSlide === 0}
            className={`p-3 rounded-full transition-colors ${
              currentSlide === 0
                ? "text-slate-500 cursor-not-allowed"
                : "text-white hover:bg-slate-700/60"
            }`}
          >
            <SkipBack size={24} />
          </button>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-3 hover:bg-slate-700/60 rounded-full transition-colors"
          >
            {isPlaying ? (
              <Pause size={24} className="text-white" />
            ) : (
              <Play size={24} className="text-white" />
            )}
          </button>

          <button
            onClick={forward}
            disabled={currentSlide === slides.length - 1}
            className={`p-3 rounded-full transition-colors ${
              currentSlide === slides.length - 1
                ? "text-slate-500 cursor-not-allowed opacity-50"
                : "text-white hover:bg-slate-700/60"
            }`}
          >
            <SkipForward size={24} />
          </button>
        </motion.div>
      )}

      {/* Slide Thumbnails - Scrollable */}
      {slides.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 ${
            isFullscreen
              ? "opacity-0 hover:opacity-100 transition-opacity duration-300"
              : ""
          }`}
        >
          {/* Scrollable container for slide numbers */}
          <div className="max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl overflow-x-auto scrollbar-hide">
            <div className="flex gap-2 px-4 py-2">
              {slides.slice(0, currentSlide + 1).map((slide, index) => (
                <button
                  key={slide.id}
                  onClick={() => handleSlideClick(index)}
                  className={`relative flex-shrink-0 w-16 h-12 rounded-lg transition-all duration-200 ${
                    index === currentSlide
                      ? "bg-blue-500 ring-2 ring-blue-400 scale-110"
                      : "bg-slate-700/60 hover:bg-slate-600/60"
                  } ${
                    currentSpeakingStep === index + 1
                      ? "ring-2 ring-green-400 animate-pulse"
                      : ""
                  }`}
                >
                  <div className="text-xs text-white font-medium flex items-center justify-center h-full">
                    {index + 1}
                  </div>
                  {currentSpeakingStep === index + 1 && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Whiteboard;
