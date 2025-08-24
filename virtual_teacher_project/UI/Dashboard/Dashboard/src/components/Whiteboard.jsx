import React, { useState, useEffect } from "react";
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
  isFullscreen,
  onToggleFullscreen,
}) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [slides] = useState([
    { id: 1, title: "Introduction", content: "Welcome to the lesson" },
    { id: 2, title: "Key Concepts", content: "Understanding the fundamentals" },
    { id: 3, title: "Examples", content: "Real-world applications" },
    { id: 4, title: "Summary", content: "Key takeaways" },
  ]);

  // Simulate lesson progress
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setTimeout(() => {
      if (currentSlide < slides.length - 1) {
        setCurrentSlide((prev) => prev + 1);
      } else {
        // Lesson complete - generate slides before completing
        generateSlides();
        setTimeout(() => {
          onLessonComplete();
        }, 1000);
      }
    }, 3000); // 3 seconds per slide

    return () => clearTimeout(timer);
  }, [currentSlide, isPlaying, slides.length, onLessonComplete]);

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
          <h1 className="text-xl font-semibold text-white">
            Lesson: {pdfName}
          </h1>
          <div className="flex items-center gap-3">
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
          className={`w-full aspect-video bg-white rounded-xl shadow-2xl flex items-center justify-center ${
            isFullscreen ? "max-w-none max-h-none h-full" : "max-w-4xl"
          }`}
        >
          <div className="text-center">
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
          </div>
        </motion.div>
      </div>

      {/* Control Bar - Always centered horizontally */}
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

      {/* Slide Thumbnails */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className={`fixed bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2 z-50 ${
          isFullscreen
            ? "opacity-0 hover:opacity-100 transition-opacity duration-300"
            : ""
        }`}
      >
        {slides.slice(0, currentSlide + 1).map((slide, index) => (
          <button
            key={slide.id}
            onClick={() => handleSlideClick(index)}
            className={`w-16 h-12 rounded-lg transition-all duration-200 ${
              index === currentSlide
                ? "bg-blue-500 ring-2 ring-blue-400"
                : "bg-slate-700/60 hover:bg-slate-600/60"
            }`}
          >
            <div className="text-xs text-white font-medium">{index + 1}</div>
          </button>
        ))}
      </motion.div>
    </div>
  );
};

export default Whiteboard;
