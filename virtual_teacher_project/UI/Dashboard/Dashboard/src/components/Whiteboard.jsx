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
} from "lucide-react";
import TeachingCanvas from "./TeachingCanvas";

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
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [slides, setSlides] = useState([]);
  const [lessonSteps, setLessonSteps] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState("Connecting...");
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [quizData, setQuizData] = useState(null);
  const [notesData, setNotesData] = useState(null);
  const [whiteboardCommands, setWhiteboardCommands] = useState([]);

  // TTS state
  const { speak, pauseResume, stop, isSpeaking, isPaused } = useTTS();
  const [autoPlay, setAutoPlay] = useState(true);
  const [currentSpeakingStep, setCurrentSpeakingStep] = useState(null);

  // Teaching mode state
  const [teachingMode, setTeachingMode] = useState(true); // Start with new teaching mode
  const [teachingSteps, setTeachingSteps] = useState([]);
  const [currentTeachingStep, setCurrentTeachingStep] = useState(null);
  const [currentTeachingStepIndex, setCurrentTeachingStepIndex] = useState(0);
  const [isTeaching, setIsTeaching] = useState(false);
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false); // Track lesson generation

  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);
  const teachingCanvasRef = useRef(null);
  const teachingStepsRef = useRef([]); // Add ref to track latest teaching steps

  // Update ref whenever teachingSteps changes
  useEffect(() => {
    teachingStepsRef.current = teachingSteps;
  }, [teachingSteps]);

  // Helper function to safely send WebSocket messages
  const sendWebSocketMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("Sending WebSocket message:", message);
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      console.error(
        "WebSocket not ready. Current state:",
        wsRef.current?.readyState
      );
      setStatus("Connection error - please try again");
      return false;
    }
  };

  // WebSocket connection
  useEffect(() => {
    // Prevent multiple connections - check all possible states
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      console.log(
        "WebSocket already connected or connecting, skipping reconnection. State:",
        wsRef.current.readyState
      );
      return;
    }

    const connectWebSocket = () => {
      // Close any existing connection first
      if (wsRef.current) {
        console.log("Closing existing WebSocket before creating new one");
        wsRef.current.close();
        wsRef.current = null;
      }

      const wsUrl = `ws://localhost:8001/ws/teacher/`;
      console.log("Creating new WebSocket connection to:", wsUrl);
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("WebSocket connected successfully");
        setIsConnected(true);
        setStatus("Connected! Starting lesson generation...");

        // Add a small delay to ensure WebSocket is fully ready
        setTimeout(() => {
          // Only send lesson generation request if we don't already have synchronized steps and not already generating
          if (teachingSteps.length === 0 && !isGeneratingLesson) {
            console.log("Starting lesson generation...");
            setIsGeneratingLesson(true);

            // Send PDF data to start lesson generation
            const pdfText = sessionStorage.getItem("pdfText");
            const pdfFilename =
              sessionStorage.getItem("pdfFilename") || pdfName;
            const message = {
              topic: pdfName,
              pdf_text: pdfText || "",
              pdf_filename: pdfFilename,
              user_id: currentUserId || "anonymous",
              conversation_id: currentConversationId || null,
            };

            console.log("Sending lesson generation request via WebSocket");
            sendWebSocketMessage(message);
          } else if (isGeneratingLesson) {
            console.log(
              "Lesson generation already in progress, skipping duplicate request"
            );
            setStatus("Lesson generation in progress...");
          } else if (teachingSteps.length > 0) {
            console.log(
              "Synchronized lesson already loaded, skipping automatic lesson generation"
            );
            console.log("Current teaching steps:", teachingSteps.length);
            setStatus("Ready - Synchronized lesson loaded");

            // If lesson is already loaded but not started, start it
            if (!isTeaching && autoPlay) {
              console.log("🚀 Auto-starting existing lesson");
              setTimeout(() => {
                startTeachingStep(teachingSteps[0], 0);
              }, 1000);
            }
          }
        }, 100); // 100ms delay
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
        setIsConnected(false);
        setStatus("Disconnected");

        // Only attempt to reconnect if the closure wasn't intentional
        if (event.code !== 1000) {
          // 1000 = normal closure
          console.log("Attempting to reconnect in 3 seconds...");
          setTimeout(connectWebSocket, 3000);
        } else {
          console.log("WebSocket closed normally, not reconnecting");
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("Connection error");
      };
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        console.log("Closing WebSocket connection on cleanup with normal code");
        wsRef.current.close(1000, "Component unmounting"); // 1000 = normal closure
        wsRef.current = null;
      }
    };
  }, []); // Remove pdfName dependency to prevent reconnections

  const handleWebSocketMessage = (data) => {
    console.log("📥 WebSocket message received:", data.type);

    switch (data.type) {
      case "status":
        setStatus(data.message);
        console.log("Status updated:", data.message);
        break;

      case "lesson_start":
        // Reset everything for new lesson
        setSlides([]);
        setCurrentSlide(0);
        setCurrentSpeakingStep(null);
        setTeachingSteps([]);
        setCurrentTeachingStep(null);
        setIsTeaching(false);
        clearQueue();
        setStatus(data.message || "Generating lesson content...");
        console.log("New lesson generation started");
        break;

      case "generation_progress":
        // Show generation progress
        setStatus(
          data.status || `Generating... (${data.buffer_length} characters)`
        );
        break;

      case "lesson_ready":
        // All teaching steps received - now we can start synchronized lesson
        console.log("🎓 === LESSON READY DEBUG ===");
        console.log("Total steps received:", data.total_steps);
        console.log(
          "Teaching steps array length:",
          data.teaching_steps?.length
        );
        console.log("Current teaching steps length:", teachingSteps.length);
        console.log("Currently teaching:", isTeaching);
        console.log("Current speaking step:", currentSpeakingStep);

        // Prevent overwriting lesson if one is already in progress
        if (
          teachingSteps.length > 0 &&
          (isTeaching || currentSpeakingStep !== null)
        ) {
          console.log(
            "🚫 Lesson already in progress, ignoring duplicate lesson_ready"
          );
          return;
        }

        if (data.teaching_steps && data.teaching_steps.length > 0) {
          // Debug first step specifically
          const firstStep = data.teaching_steps[0];
          console.log("🔍 === FIRST STEP ANALYSIS ===");
          console.log("Step 1 object:", firstStep);
          console.log("Step 1 keys:", Object.keys(firstStep));
          console.log("Step 1 speech_text:", firstStep.speech_text);
          console.log(
            "Step 1 speech_text length:",
            firstStep.speech_text?.length
          );
          console.log("Step 1 speech_text type:", typeof firstStep.speech_text);
          console.log("Step 1 drawing_commands:", firstStep.drawing_commands);
          console.log(
            "Step 1 drawing_commands count:",
            firstStep.drawing_commands?.length
          );
          console.log("================================");
        }

        // Log each step content in detail for debugging
        if (data.teaching_steps) {
          data.teaching_steps.forEach((step, index) => {
            console.log(`=== STEP ${index + 1} CONTENT ===`);
            console.log(`Step number: ${step.step}`);
            console.log(`Speech text: "${step.speech_text}"`);
            console.log(`Speech text length: ${step.speech_text?.length}`);
            console.log(
              `Drawing commands: ${step.drawing_commands?.length || 0}`
            );
            if (step.drawing_commands?.length > 0) {
              step.drawing_commands.forEach((cmd, cmdIndex) => {
                console.log(
                  `  Command ${cmdIndex + 1}: ${cmd.action} - ${
                    cmd.text || "no text"
                  }`
                );
              });
            }
            console.log("========================");
          });
        }

        setTeachingSteps(data.teaching_steps || []);
        setStatus(`Lesson ready! ${data.total_steps} steps prepared.`);
        setIsGeneratingLesson(false); // Reset generation flag

        // Auto-switch to teaching mode
        setTeachingMode(true);

        // Auto-start the lesson after a brief delay (if autoPlay is enabled)
        if (autoPlay && data.teaching_steps && data.teaching_steps.length > 0) {
          console.log("🚀 Auto-starting synchronized lesson in 2 seconds...");
          setTimeout(() => {
            console.log("🎬 Starting lesson with first step");
            startTeachingStep(data.teaching_steps[0], 0);
          }, 2000); // 2 second delay to let user see the "lesson ready" message
        } else {
          console.log("⏸️ Auto-play disabled or no steps available");
        }
        break;

      case "conversation_created":
        console.log("Conversation created:", data.conversation_id, data.title);
        // Notify parent component about new conversation
        if (onConversationCreated) {
          onConversationCreated(data.conversation_id, data.title);
        }
        break;

      case "teaching_step":
        // COMPLETELY DISABLED - Legacy system that causes duplicate content
        console.log(
          "LEGACY teaching_step message IGNORED - using synchronized lesson system"
        );
        console.log("Received data:", data.data);
        break;

      case "lesson_step":
        // COMPLETELY DISABLED - Legacy system that causes duplicate content
        console.log(
          "LEGACY lesson_step message IGNORED - using synchronized lesson system"
        );
        console.log("Received data:", data.data);
        break;

      case "notes_and_quiz_ready":
        setQuizData(data.data.quiz);
        setNotesData(data.data.notes_content);
        console.log("Quiz and notes data received, storing for later use");
        // Don't call onQuizDataReceived here - wait for lesson to complete
        break;

      case "lesson_end":
        setIsGeneratingLesson(false); // Reset generation flag
        // Only process lesson_end for legacy lessons, ignore for synchronized lessons
        if (teachingSteps.length === 0) {
          setStatus("Lesson generation completed!");
          if (autoPlay) {
            speak("Lesson completed. Great job!", () => {});
          }
          // Lesson will auto-advance through slides, user can manually start quiz when ready
        } else {
          console.log(
            "Ignoring legacy lesson_end - synchronized lesson already loaded"
          );
        }
        break;

      case "error":
        setStatus(`Error: ${data.message}`);
        setIsGeneratingLesson(false); // Reset generation flag on error
        console.error("WebSocket error:", data);
        break;

      default:
        console.log("Unknown message type:", data.type);
    }
  };

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

      setCurrentSpeakingStep(step.step);
      setCurrentTeachingStepIndex(stepIndex !== undefined ? stepIndex : 0);
      setCurrentTeachingStep(step);
      setIsTeaching(true); // Ensure we're in teaching mode

      // Clear canvas for new step
      if (teachingCanvasRef.current) {
        teachingCanvasRef.current.clearCanvas();
        console.log("🎨 Canvas cleared for step", stepIndex + 1);
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
        step.drawing_commands.forEach((command, index) => {
          console.log(`Drawing command ${index + 1}:`, command);
          if (teachingCanvasRef.current) {
            setTimeout(() => {
              teachingCanvasRef.current.addDrawingCommand(command);
            }, command.time || index * 500); // Stagger commands by 500ms
          }
        });
      } else {
        console.warn("⚠️ No drawing commands for step", stepIndex + 1);
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
            <div
              className={`px-3 py-1 rounded-full text-sm ${
                isConnected
                  ? "bg-green-500/20 text-green-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {isConnected ? "● Connected" : "● Disconnected"}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-slate-300 text-sm">{status}</span>

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

              {teachingSteps.length > 0 && (
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
            <TeachingCanvas
              ref={teachingCanvasRef}
              teachingStep={currentTeachingStep}
              isPlaying={isTeaching}
              onStepComplete={handleTeachingStepComplete}
              canvasWidth={isFullscreen ? window.innerWidth * 0.9 : 800}
              canvasHeight={isFullscreen ? window.innerHeight * 0.7 : 600}
            />
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
