import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, RotateCcw, ArrowRight } from "lucide-react";

const Quiz = ({ onQuizComplete, onRetakeLesson, quizData }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quizId, setQuizId] = useState(null);

  // Fetch quiz data from API
  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        setLoading(true);
        
        // Try multiple ways to get the lesson ID
        const lessonId = 
          sessionStorage.getItem('lessonId') || 
          sessionStorage.getItem('conversationId') ||
          localStorage.getItem('currentConversationId') ||
          sessionStorage.getItem('currentConversationId');
          
        const userId = 
          sessionStorage.getItem('userId') || 
          localStorage.getItem('userId') ||
          sessionStorage.getItem('studentId') || 
          'default_student';
        
        if (!lessonId || lessonId === 'default_lesson') {
          console.warn('⚠️ No lesson ID found. Using fallback data.');
          throw new Error('No active lesson found. Please start a lesson first.');
        }
        
        console.log('📚 Fetching quiz for lesson:', lessonId);
        console.log('👤 User ID:', userId);
        
        // Updated endpoint: /api/quiz/get/ (retrieves pre-generated quiz)
        const response = await fetch(
          `http://localhost:8000/api/quiz/get/${lessonId}?user_id=${userId}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          // If 202 (Accepted), quiz is still being generated
          if (response.status === 202) {
            throw new Error('Quiz is being generated. Please wait a moment...');
          }
          throw new Error('Failed to fetch quiz data');
        }

        const data = await response.json();
        
        // Transform API data to match component format
        const transformedQuestions = data.questions.map((q, index) => ({
          question: q.question,
          options: q.options,
          correct: q.options.indexOf(q.correct_answer),
          feedback: q.explanation || q.feedback || 'No explanation available.',
        }));
        
        setQuestions(transformedQuestions);
        setQuizId(data.quiz_id);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching quiz:', err);
        setError('Failed to load quiz. Please try again.');
        setLoading(false);
        
        // Fallback to mock data on error
        setQuestions([
          {
            question: "What is the main concept discussed in this lesson?",
            options: [
              "Advanced mathematics",
              "Fundamental principles",
              "Historical events",
              "Scientific theories",
            ],
            correct: 1,
            feedback:
              "The lesson focuses on understanding fundamental principles as the foundation for advanced learning.",
          },
          {
            question: "Which of the following best describes the key takeaway?",
            options: [
              "Memorization is key",
              "Understanding fundamentals",
              "Practice makes perfect",
              "Theory over practice",
            ],
            correct: 1,
            feedback:
              "Understanding fundamentals is crucial because it provides the building blocks for more complex concepts.",
          },
          {
            question: "How should you apply this knowledge?",
            options: [
              "Only in exams",
              "In real-world scenarios",
              "Never use it",
              "Share with friends only",
            ],
            correct: 1,
            feedback:
              "Applying knowledge in real-world scenarios helps reinforce learning and demonstrates practical understanding.",
          },
        ]);
      }
    };

    // Only fetch if quizData prop is not provided
    if (!quizData) {
      fetchQuiz();
    } else {
      setQuestions(quizData);
      setLoading(false);
    }
  }, [quizData]);

  // Save quiz results to backend
  useEffect(() => {
    if (showResult) {
      saveQuizResults();
      onQuizComplete(score, questions.length);
    }
  }, [showResult, score, questions.length]);

  const saveQuizResults = async () => {
    try {
      const userId = sessionStorage.getItem('userId') || sessionStorage.getItem('studentId') || 'default_student';
      const lessonId = sessionStorage.getItem('lessonId') || 'default_lesson';
      
      // Create answers array with user selections
      const answers = questions.map((q, index) => ({
        question_index: index,
        selected_option: index <= currentQuestion ? selectedAnswer : null,
      }));

      const submissionData = {
        quiz_id: quizId,
        user_id: userId,
        lesson_id: lessonId,
        answers: answers,
      };

      const response = await fetch("http://localhost:8000/api/quiz/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(submissionData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Quiz results saved:", result);
        // Update score from backend if available
        if (result.score !== undefined) {
          setScore(result.score);
        }
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

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Generating your quiz...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && questions.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-800 rounded-2xl p-8 text-center border border-slate-700/40">
          <p className="text-red-400 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (showResult) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="min-h-screen bg-slate-900 flex items-center justify-center p-4"
      >
        <div className="max-w-md w-full bg-slate-800 rounded-2xl p-8 text-center border border-slate-700/40">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <span className="text-3xl font-bold text-white">{score}</span>
          </motion.div>

          <h2 className="text-2xl font-bold text-white mb-2">Quiz Complete!</h2>

          <p className="text-slate-300 mb-6">
            You scored {score}/{questions.length}
          </p>

          <p className="text-blue-400 mb-8 text-sm">{getFeedback()}</p>

          <div className="space-y-3">
            <button
              onClick={retakeQuiz}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              <RotateCcw size={18} />
              Retake Quiz
            </button>

            <button
              onClick={() => onQuizComplete(score, questions.length)}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Next
              <ArrowRight size={18} />
            </button>
          </div>
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
