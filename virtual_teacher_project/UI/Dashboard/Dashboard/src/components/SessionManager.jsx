import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Whiteboard from "./Whiteboard";
import Quiz from "./Quiz";
import Notes from "./Notes";

const SessionManager = ({
  pdfName,
  onExitSession,
  onFullscreenChange,
  currentUserId,
  currentConversationId,
  onConversationCreated,
}) => {
  const [currentStage, setCurrentStage] = useState("whiteboard"); // whiteboard, quiz, notes
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [sessionData, setSessionData] = useState({
    lessonCompleted: false,
    quizScore: 0,
    totalQuestions: 0,
    slides: [],
    quizData: null,
    notesData: null,
  });

  const toggleFullscreen = () => {
    const newFullscreenState = !isFullscreen;
    setIsFullscreen(newFullscreenState);

    // Notify parent component about fullscreen state change
    if (onFullscreenChange) {
      onFullscreenChange(newFullscreenState && currentStage === "whiteboard");
    }

    if (!isFullscreen) {
      // Entering fullscreen
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
      }
    } else {
      // Exiting fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const handleLessonComplete = () => {
    // Exit fullscreen when lesson completes and moving to quiz
    if (isFullscreen) {
      setIsFullscreen(false);
      if (onFullscreenChange) {
        onFullscreenChange(false);
      }
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }

    setSessionData((prev) => ({ ...prev, lessonCompleted: true }));

    // Add a small delay for smooth transition
    setTimeout(() => {
      setCurrentStage("quiz");
    }, 500);
  };

  const handleSlidesGenerated = (slides) => {
    setSessionData((prev) => ({ ...prev, slides }));
  };

  const handleQuizDataReceived = (quizData, notesData) => {
    setSessionData((prev) => ({
      ...prev,
      quizData: quizData,
      notesData: notesData,
    }));
  };

  const handleQuizComplete = (score, totalQuestions) => {
    setSessionData((prev) => ({
      ...prev,
      quizScore: score,
      totalQuestions,
    }));
    setCurrentStage("notes");
  };

  const handleRetakeLesson = () => {
    setCurrentStage("whiteboard");
    setSessionData({
      lessonCompleted: false,
      quizScore: 0,
      totalQuestions: 0,
    });
  };

  const handleEndSession = () => {
    onExitSession();
  };

  const renderStage = () => {
    switch (currentStage) {
      case "whiteboard":
        return (
          <Whiteboard
            pdfName={pdfName}
            onLessonComplete={handleLessonComplete}
            onExit={onExitSession}
            onSlidesGenerated={handleSlidesGenerated}
            onQuizDataReceived={handleQuizDataReceived}
            isFullscreen={isFullscreen}
            onToggleFullscreen={toggleFullscreen}
            currentUserId={currentUserId}
            currentConversationId={currentConversationId}
            onConversationCreated={onConversationCreated}
          />
        );
      case "quiz":
        return (
          <Quiz
            onQuizComplete={handleQuizComplete}
            onRetakeLesson={handleRetakeLesson}
            quizData={sessionData.quizData}
          />
        );
      case "notes":
        return (
          <Notes
            onRetakeLesson={handleRetakeLesson}
            onEndSession={handleEndSession}
            slides={sessionData.slides}
            notesContent={sessionData.notesData}
          />
        );
      default:
        return null;
    }
  };

  return (
    <>
      {/* Fullscreen Mode - Only for Whiteboard/Slides */}
      {isFullscreen && currentStage === "whiteboard" && (
        <div className="fixed inset-0 z-[9999] bg-slate-900">
          {/* Fullscreen content for whiteboard only */}
          <div className="h-full w-full">{renderStage()}</div>

          {/* Fullscreen Exit Button - Always visible */}
          <button
            onClick={toggleFullscreen}
            className="fixed top-4 right-4 p-3 bg-slate-800/80 hover:bg-slate-700/80 rounded-lg transition-colors z-[10000]"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              className="text-white"
            >
              <path
                d="M8 3v3a2 2 0 0 1-2 2H3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="m3 3 3 3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M21 8h-3a2 2 0 0 1-2-2V3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="m21 3-3 3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M8 21v-3a2 2 0 0 1 2-2h3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="m3 21 3-3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M16 16h3a2 2 0 0 1 2 2v3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="m21 21-3-3"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Normal Mode */}
      <div
        className={`relative overflow-hidden ${
          isFullscreen && currentStage === "whiteboard" ? "hidden" : ""
        }`}
      >
        {/* Progress Indicator */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed top-4 left-1/2 transform -translate-x-1/2 z-40"
        >
          <div className="flex items-center gap-2 bg-slate-800/80 backdrop-blur-sm rounded-full px-4 py-2 border border-slate-700/40">
            <button
              onClick={() => {
                // Exit fullscreen when switching to whiteboard from other sections
                if (isFullscreen && currentStage !== "whiteboard") {
                  setIsFullscreen(false);
                  if (onFullscreenChange) {
                    onFullscreenChange(false);
                  }
                  if (document.exitFullscreen) {
                    document.exitFullscreen();
                  }
                }
                setCurrentStage("whiteboard");
              }}
              className={`flex items-center gap-2 cursor-pointer transition-colors ${
                currentStage === "whiteboard"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${
                  currentStage === "whiteboard" ? "bg-blue-500" : "bg-slate-600"
                }`}
              />
              <span className="text-xs font-medium">Lesson</span>
            </button>

            <div className="w-8 h-px bg-slate-600" />

            <button
              onClick={() => {
                // Exit fullscreen when switching to quiz
                if (isFullscreen) {
                  setIsFullscreen(false);
                  if (onFullscreenChange) {
                    onFullscreenChange(false);
                  }
                  if (document.exitFullscreen) {
                    document.exitFullscreen();
                  }
                }
                setCurrentStage("quiz");
              }}
              className={`flex items-center gap-2 cursor-pointer transition-colors ${
                currentStage === "quiz"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${
                  currentStage === "quiz" ? "bg-blue-500" : "bg-slate-600"
                }`}
              />
              <span className="text-xs font-medium">Quiz</span>
            </button>

            <div className="w-8 h-px bg-slate-600" />

            <button
              onClick={() => {
                // Exit fullscreen when switching to notes
                if (isFullscreen) {
                  setIsFullscreen(false);
                  if (onFullscreenChange) {
                    onFullscreenChange(false);
                  }
                  if (document.exitFullscreen) {
                    document.exitFullscreen();
                  }
                }
                setCurrentStage("notes");
              }}
              className={`flex items-center gap-2 cursor-pointer transition-colors ${
                currentStage === "notes"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${
                  currentStage === "notes" ? "bg-blue-500" : "bg-slate-600"
                }`}
              />
              <span className="text-xs font-medium">Notes</span>
            </button>
          </div>
        </motion.div>

        {/* Stage Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStage}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {renderStage()}
          </motion.div>
        </AnimatePresence>
      </div>
    </>
  );
};

export default SessionManager;
