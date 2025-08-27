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
} from "lucide-react";

const Whiteboard = ({
  pdfName,
  onLessonComplete,
  onExit,
  onSlidesGenerated,
  onQuizDataReceived,
  isFullscreen,
  onToggleFullscreen,
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

  const wsRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/teacher/`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        setStatus("Connected! Starting lesson generation...");

        // Send PDF data to start lesson generation
        const pdfText = sessionStorage.getItem("pdfText");
        const message = {
          topic: pdfName,
          pdf_text: pdfText || "",
        };

        wsRef.current.send(JSON.stringify(message));
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

        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
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
        wsRef.current.close();
      }
    };
  }, [pdfName]);

  const handleWebSocketMessage = (data) => {
    console.log("Received WebSocket message:", data);

    switch (data.type) {
      case "status":
        setStatus(data.message);
        console.log("Status updated:", data.message);
        break;

      case "lesson_step":
        const stepData = data.data;
        console.log("Lesson step received:", stepData);
        setLessonSteps((prev) => [...prev, stepData]);

        // Process whiteboard commands
        if (stepData.whiteboard_commands) {
          setWhiteboardCommands((prev) => [
            ...prev,
            ...stepData.whiteboard_commands,
          ]);
          executeWhiteboardCommands(stepData.whiteboard_commands);
        }

        // Convert to slide format for UI
        const slide = {
          id: Date.now(),
          title: `Step ${lessonSteps.length + 1}`,
          content: stepData.text_explanation,
          tts_text: stepData.tts_text,
          commands: stepData.whiteboard_commands,
        };

        setSlides((prev) => {
          const newSlides = [...prev, slide];
          console.log("Slides updated, total count:", newSlides.length);
          return newSlides;
        });

        // Start playing if this is the first step and not already playing
        if (lessonSteps.length === 0 && !isPlaying) {
          console.log("Auto-starting lesson playback for first slide");
          setIsPlaying(true);
          setCurrentSlide(0);
          setStatus("Lesson started!");
        } else {
          console.log(
            "Not auto-starting: lessonSteps.length =",
            lessonSteps.length,
            "isPlaying =",
            isPlaying
          );
        }
        break;

      case "notes_and_quiz_ready":
        setQuizData(data.data.quiz);
        setNotesData(data.data.notes_content);
        console.log("Quiz and notes data received, storing for later use");
        // Don't call onQuizDataReceived here - wait for lesson to complete
        break;

      case "lesson_end":
        setStatus("Lesson generation completed!");
        // Lesson will auto-advance through slides, user can manually start quiz when ready
        break;

      case "error":
        setStatus(`Error: ${data.message}`);
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
          key={currentSlide}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className={`w-full aspect-video bg-white rounded-xl shadow-2xl flex items-center justify-center relative ${
            isFullscreen ? "max-w-none max-h-none h-full" : "max-w-4xl"
          }`}
        >
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
                    isFullscreen ? "text-2xl" : "text-xl"
                  }`}
                >
                  {slides[currentSlide].content}
                </p>
                <div
                  className={`text-slate-500 ${
                    isFullscreen ? "mt-8 text-lg" : "mt-6 text-sm"
                  }`}
                >
                  Slide {currentSlide + 1} of {slides.length}
                </div>
              </>
            ) : (
              <div className="text-center">
                {/* Enhanced Loading UI */}
                <div className="flex flex-col items-center space-y-6">
                  {/* Animated Loading Spinner */}
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-slate-300 rounded-full animate-spin border-t-blue-500"></div>
                    <div className="absolute inset-0 w-16 h-16 border-4 border-transparent rounded-full animate-pulse border-t-blue-400"></div>
                  </div>

                  {/* Status Text */}
                  <div className="space-y-2">
                    <h3 className="text-2xl font-semibold text-slate-800">
                      Generating AI Lesson
                    </h3>
                    <p className="text-slate-600 text-lg max-w-md mx-auto">
                      {status}
                    </p>
                    {isConnected && (
                      <div className="flex items-center justify-center mt-3 space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-green-600 text-sm">
                          Connected
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Progress Animation */}
                  <div className="w-48 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full animate-pulse"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
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
                  className={`flex-shrink-0 w-16 h-12 rounded-lg transition-all duration-200 ${
                    index === currentSlide
                      ? "bg-blue-500 ring-2 ring-blue-400 scale-110"
                      : "bg-slate-700/60 hover:bg-slate-600/60"
                  }`}
                >
                  <div className="text-xs text-white font-medium flex items-center justify-center h-full">
                    {index + 1}
                  </div>
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
