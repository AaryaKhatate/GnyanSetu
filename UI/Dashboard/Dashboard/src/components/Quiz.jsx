import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, RotateCcw, ArrowRight, Loader2, Award, TrendingUp } from "lucide-react";
import confetti from "canvas-confetti";

const Quiz = ({ onQuizComplete, onRetakeLesson, quizData }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);

  // Fetch quiz from quiz-notes-service
  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const lessonId = sessionStorage.getItem("lessonId");
        const userId =
          sessionStorage.getItem("studentId") ||
          sessionStorage.getItem("userId") ||
          "default_student";

        if (!lessonId) {
          throw new Error(
            "No lesson ID found. Please complete a lesson first."
          );
        }

        setLoading(true);
        const response = await fetch(
          `http://localhost:8005/api/quiz/get/${lessonId}?user_id=${userId}`
        );

        if (response.status === 202) {
          // Quiz still generating
          const data = await response.json();
          setError(
            "Quiz is still being generated. Please wait a moment and try again."
          );
          setTimeout(fetchQuiz, 3000); // Retry after 3 seconds
          return;
        }

        if (!response.ok) {
          throw new Error("Failed to fetch quiz from database");
        }

        const data = await response.json();

        // Transform quiz data to component format
        if (data.questions && data.questions.length > 0) {
          const transformedQuestions = data.questions.map((q, index) => {
            // Extract options - handle both string array and object array formats
            let options = [];
            let correctIndex = 0;

            if (Array.isArray(q.options)) {
              if (q.options.length > 0 && typeof q.options[0] === "object") {
                // Options are objects like {key: "A", text: "..."}
                options = q.options.map(
                  (opt) => opt.text || opt.key || String(opt)
                );
                // Find correct answer index
                correctIndex = q.options.findIndex(
                  (opt) =>
                    opt.text === q.correct_answer ||
                    opt.key === q.correct_answer
                );
                if (correctIndex === -1) correctIndex = 0;
              } else {
                // Options are already strings
                options = q.options;
                correctIndex = q.options.indexOf(q.correct_answer);
                if (correctIndex === -1) correctIndex = 0;
              }
            }

            return {
              question: q.question,
              options: options,
              correct: correctIndex,
              correct_answer: q.correct_answer,
              feedback: q.explanation || "No explanation available",
              explanation: q.explanation || "No explanation available",
              difficulty: q.difficulty || "medium",
            };
          });
          setQuestions(transformedQuestions);
          setLoading(false);
        } else {
          throw new Error("No quiz questions found");
        }
      } catch (err) {
        console.error("Error fetching quiz:", err);
        setError(err.message);
        setLoading(false);
        // Fallback to mock data if provided
        if (quizData && quizData.length > 0) {
          setQuestions(quizData);
        }
      }
    };

    fetchQuiz();
  }, [quizData]);

  // Submit quiz results to backend (but don't exit session)
  useEffect(() => {
    if (showResult) {
      submitQuizResults();
      // Note: onQuizComplete is called when user clicks "Finish" button, not here
    }
  }, [showResult]);

  // Trigger confetti animation for scores above 75%
  useEffect(() => {
    if (showResult) {
      const percentage = (score / questions.length) * 100;
      if (percentage > 75) {
        // Fire confetti
        const duration = 3000;
        const animationEnd = Date.now() + duration;
        const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };

        const randomInRange = (min, max) => Math.random() * (max - min) + min;

        const interval = setInterval(() => {
          const timeLeft = animationEnd - Date.now();

          if (timeLeft <= 0) {
            return clearInterval(interval);
          }

          const particleCount = 50 * (timeLeft / duration);

          confetti({
            ...defaults,
            particleCount,
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
          });
          confetti({
            ...defaults,
            particleCount,
            origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
          });
        }, 250);

        return () => clearInterval(interval);
      }
    }
  }, [showResult, score, questions.length]);

  const submitQuizResults = async () => {
    try {
      const lessonId = sessionStorage.getItem("lessonId");
      const userId =
        sessionStorage.getItem("studentId") ||
        sessionStorage.getItem("userId") ||
        "default_student";

      const submissionData = {
        lesson_id: lessonId,
        user_id: userId,
        answers: userAnswers,
      };

      const response = await fetch("http://localhost:8005/api/quiz/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(submissionData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Quiz results saved:", result);
      } else {
        console.error("Failed to save quiz results");
      }
    } catch (error) {
      console.error("Error saving quiz results:", error);
    }
  };

  const handleAnswerSelect = (answerIndex) => {
    if (answered) return;

    setSelectedAnswer(answerIndex);
    setAnswered(true);

    // Track user answer
    const answerData = {
      question_index: currentQuestion,
      selected_option: questions[currentQuestion].options[answerIndex],
    };
    setUserAnswers((prev) => [...prev, answerData]);

    if (answerIndex === questions[currentQuestion].correct) {
      setScore((prev) => prev + 1);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setShowResult(true);
    }
  };

  const retakeQuiz = () => {
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setAnswered(false);
    setScore(0);
    setShowResult(false);
    setUserAnswers([]);
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading quiz questions...</p>
          <p className="text-slate-400 text-sm mt-2">Please wait a moment</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && questions.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-800 rounded-2xl p-8 text-center border border-slate-700/40">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <X size={32} className="text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">
            Quiz Not Available
          </h2>
          <p className="text-slate-300 mb-6">{error}</p>
          <button
            onClick={onRetakeLesson}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // No questions
  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-800 rounded-2xl p-8 text-center border border-slate-700/40">
          <p className="text-slate-300">No quiz questions available</p>
        </div>
      </div>
    );
  }

  const getPerformanceColor = (percentage) => {
    if (percentage >= 80) return "text-green-400";
    if (percentage >= 60) return "text-blue-400";
    if (percentage >= 40) return "text-yellow-400";
    return "text-red-400";
  };

  const getPerformanceGradient = (percentage) => {
    if (percentage >= 80) return "from-green-500 to-emerald-600";
    if (percentage >= 60) return "from-blue-500 to-indigo-600";
    if (percentage >= 40) return "from-yellow-500 to-orange-600";
    return "from-red-500 to-rose-600";
  };

  const getFeedback = () => {
    const percentage = (score / questions.length) * 100;
    if (percentage >= 80) return "Excellent! You've mastered the concepts.";
    if (percentage >= 60)
      return "Good job! You understand most of the material.";
    if (percentage >= 40)
      return "Not bad! Review the concepts for better understanding.";
    return "Keep practicing! Review the lesson and try again.";
  };

  if (showResult) {
    const totalQuestions = questions.length;
    const correctAnswers = score;
    const wrongAnswers = totalQuestions - score;
    const percentage = Math.round((score / totalQuestions) * 100);
    const isExcellent = percentage > 75;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4"
      >
        <div className="max-w-2xl w-full">
          {/* Header Card */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-8 mb-6 border border-slate-700/50 shadow-2xl"
          >
            <div className="text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                className={`w-32 h-32 bg-gradient-to-br ${getPerformanceGradient(percentage)} rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg relative`}
              >
                {isExcellent && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1, rotate: 360 }}
                    transition={{ delay: 0.3, duration: 0.6 }}
                    className="absolute -top-3 -right-3"
                  >
                    <Award className="text-yellow-400" size={40} />
                  </motion.div>
                )}
                <div className="text-center">
                  <span className="text-5xl font-bold text-white block">{percentage}%</span>
                </div>
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-3xl font-bold text-white mb-2"
              >
                {isExcellent ? " Outstanding Performance!" : "Quiz Complete!"}
              </motion.h2>

              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className={`text-lg mb-4 ${getPerformanceColor(percentage)}`}
              >
                {getFeedback()}
              </motion.p>
            </div>
          </motion.div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-br from-green-500/20 to-green-600/10 border border-green-500/30 rounded-2xl p-6 text-center backdrop-blur-sm"
            >
              <div className="flex items-center justify-center mb-2">
                <Check className="text-green-400 mr-2" size={24} />
              </div>
              <p className="text-3xl font-bold text-green-400">{correctAnswers}</p>
              <p className="text-slate-300 text-sm mt-1">Correct</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-gradient-to-br from-red-500/20 to-red-600/10 border border-red-500/30 rounded-2xl p-6 text-center backdrop-blur-sm"
            >
              <div className="flex items-center justify-center mb-2">
                <X className="text-red-400 mr-2" size={24} />
              </div>
              <p className="text-3xl font-bold text-red-400">{wrongAnswers}</p>
              <p className="text-slate-300 text-sm mt-1">Wrong</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
              className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-2xl p-6 text-center backdrop-blur-sm"
            >
              <div className="flex items-center justify-center mb-2">
                <TrendingUp className="text-blue-400 mr-2" size={24} />
              </div>
              <p className="text-3xl font-bold text-blue-400">{totalQuestions}</p>
              <p className="text-slate-300 text-sm mt-1">Total Questions</p>
            </motion.div>
          </div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={retakeQuiz}
                className="group relative overflow-hidden px-6 py-4 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-all duration-300 flex items-center justify-center gap-2 font-semibold shadow-lg hover:shadow-xl hover:scale-105"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-slate-600 to-slate-700 opacity-0 group-hover:opacity-100 transition-opacity" />
                <RotateCcw size={20} className="relative z-10" />
                <span className="relative z-10">Retake Quiz</span>
              </button>

              <button
                onClick={() => onQuizComplete(score, questions.length)}
                className="group relative overflow-hidden px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl transition-all duration-300 flex items-center justify-center gap-2 font-semibold shadow-lg hover:shadow-xl hover:scale-105"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                <span className="relative z-10">Finish</span>
                <ArrowRight size={20} className="relative z-10" />
              </button>
            </div>
          </motion.div>
        </div>
      </motion.div>
    );
  }

  const currentQ = questions[currentQuestion];

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-white mb-2">
            <span className="text-sm">
              Question {currentQuestion + 1} of {questions.length}
            </span>
            <span className="text-sm">
              {Math.round(((currentQuestion + 1) / questions.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{
                width: `${((currentQuestion + 1) / questions.length) * 100}%`,
              }}
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
            />
          </div>
        </div>

        {/* Question Card */}
        <motion.div
          key={currentQuestion}
          initial={{ x: 300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -300, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="bg-slate-800 rounded-2xl p-8 border border-slate-700/40"
        >
          <h2 className="text-2xl font-bold text-white mb-8 leading-relaxed">
            {currentQ.question}
          </h2>

          <div className="space-y-4">
            {currentQ.options.map((option, index) => (
              <motion.button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                disabled={answered}
                className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 ${
                  selectedAnswer === index
                    ? index === currentQ.correct
                      ? "border-green-500 bg-green-500/20 text-green-100"
                      : "border-red-500 bg-red-500/20 text-red-100"
                    : answered && index === currentQ.correct
                    ? "border-green-500 bg-green-500/20 text-green-100"
                    : "border-slate-600 hover:border-slate-500 bg-slate-700/50 hover:bg-slate-600/50 text-white"
                }`}
                whileHover={!answered ? { scale: 1.02 } : {}}
                whileTap={!answered ? { scale: 0.98 } : {}}
              >
                <div className="flex items-center justify-between">
                  <span className="text-lg">{option}</span>
                  {answered && selectedAnswer === index && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className={`p-1 rounded-full ${
                        index === currentQ.correct
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    >
                      {index === currentQ.correct ? (
                        <Check size={16} className="text-white" />
                      ) : (
                        <X size={16} className="text-white" />
                      )}
                    </motion.div>
                  )}
                  {answered &&
                    index === currentQ.correct &&
                    selectedAnswer !== index && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="p-1 rounded-full bg-green-500"
                      >
                        <Check size={16} className="text-white" />
                      </motion.div>
                    )}
                </div>
              </motion.button>
            ))}
          </div>

          {answered && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg"
            >
              <h4 className="text-blue-400 font-semibold mb-2">Explanation:</h4>
              <p className="text-slate-200 text-sm leading-relaxed">
                {currentQ.feedback ||
                  currentQ.explanation ||
                  "No explanation available."}
              </p>
            </motion.div>
          )}

          {answered && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 flex justify-center"
            >
              <button
                onClick={nextQuestion}
                className="flex items-center gap-2 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                {currentQuestion < questions.length - 1
                  ? "Next Question"
                  : "See Results"}
                <ArrowRight size={18} />
              </button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Quiz;