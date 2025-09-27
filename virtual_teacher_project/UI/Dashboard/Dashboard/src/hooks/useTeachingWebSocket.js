// Teaching WebSocket Hook for Real-Time Teaching Integration
import { useState, useEffect, useRef, useCallback } from 'react';

const TEACHING_WS_URL = 'ws://localhost:8004/ws/teaching/';

export const useTeachingWebSocket = (sessionId, userId) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [teachingSession, setTeachingSession] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [isTeaching, setIsTeaching] = useState(false);
  const [teachingProgress, setTeachingProgress] = useState(0);
  const [error, setError] = useState(null);
  
  // Callbacks for teaching events
  const onTeachingStepRef = useRef();
  const onVoiceMessageRef = useRef();
  const onCanvasUpdateRef = useRef();
  const onQuizQuestionRef = useRef();

  // Connect to WebSocket
  useEffect(() => {
    if (!sessionId || !userId) return;

    const wsUrl = `${TEACHING_WS_URL}${sessionId}/?user_id=${userId}`;
    console.log('🎓 Connecting to Teaching WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ Teaching WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 Teaching message received:', data);

        switch (data.type) {
          case 'teaching_session_started':
            setTeachingSession(data.session);
            setIsTeaching(true);
            setTeachingProgress(0);
            break;

          case 'teaching_step':
            setCurrentStep(data.step);
            setTeachingProgress(data.progress || 0);
            if (onTeachingStepRef.current) {
              onTeachingStepRef.current(data.step);
            }
            break;

          case 'voice_message':
            if (onVoiceMessageRef.current) {
              onVoiceMessageRef.current(data.message, data.audio_url);
            }
            break;

          case 'canvas_update':
            if (onCanvasUpdateRef.current) {
              onCanvasUpdateRef.current(data.canvas_data);
            }
            break;

          case 'quiz_question':
            if (onQuizQuestionRef.current) {
              onQuizQuestionRef.current(data.question);
            }
            break;

          case 'teaching_session_ended':
            setIsTeaching(false);
            setTeachingSession(null);
            setCurrentStep(null);
            setTeachingProgress(0);
            break;

          case 'error':
            setError(data.message);
            console.error('❌ Teaching error:', data.message);
            break;

          default:
            console.log('🔄 Unknown teaching message type:', data.type);
        }
      } catch (err) {
        console.error('❌ Error parsing teaching message:', err);
        setError('Failed to parse teaching message');
      }
    };

    ws.onclose = () => {
      console.log('🔌 Teaching WebSocket disconnected');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('❌ Teaching WebSocket error:', error);
      setError('WebSocket connection error');
      setIsConnected(false);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [sessionId, userId]);

  // Send message to WebSocket
  const sendMessage = useCallback((message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ Teaching WebSocket not connected');
    }
  }, [socket]);

  // Start teaching session
  const startTeaching = useCallback((lessonId, teachingMode = 'interactive') => {
    sendMessage({
      type: 'start_teaching',
      lesson_id: lessonId,
      teaching_mode: teachingMode,
      user_preferences: {
        voice_speed: 0.9,
        voice_pitch: 1.0,
        visualization_level: 'advanced'
      }
    });
  }, [sendMessage]);

  // Pause/Resume teaching
  const pauseTeaching = useCallback(() => {
    sendMessage({ type: 'pause_teaching' });
  }, [sendMessage]);

  const resumeTeaching = useCallback(() => {
    sendMessage({ type: 'resume_teaching' });
  }, [sendMessage]);

  // Skip to next step
  const nextStep = useCallback(() => {
    sendMessage({ type: 'next_step' });
  }, [sendMessage]);

  // Go to previous step
  const previousStep = useCallback(() => {
    sendMessage({ type: 'previous_step' });
  }, [sendMessage]);

  // Answer quiz question
  const answerQuestion = useCallback((answer) => {
    sendMessage({
      type: 'answer_question',
      answer: answer
    });
  }, [sendMessage]);

  // Ask question to AI tutor
  const askQuestion = useCallback((question) => {
    sendMessage({
      type: 'ask_question',
      question: question
    });
  }, [sendMessage]);

  // Stop teaching session
  const stopTeaching = useCallback(() => {
    sendMessage({ type: 'stop_teaching' });
  }, [sendMessage]);

  // Set event callbacks
  const setOnTeachingStep = useCallback((callback) => {
    onTeachingStepRef.current = callback;
  }, []);

  const setOnVoiceMessage = useCallback((callback) => {
    onVoiceMessageRef.current = callback;
  }, []);

  const setOnCanvasUpdate = useCallback((callback) => {
    onCanvasUpdateRef.current = callback;
  }, []);

  const setOnQuizQuestion = useCallback((callback) => {
    onQuizQuestionRef.current = callback;
  }, []);

  return {
    // Connection status
    isConnected,
    error,
    
    // Teaching session state
    teachingSession,
    currentStep,
    isTeaching,
    teachingProgress,
    
    // Teaching controls
    startTeaching,
    pauseTeaching,
    resumeTeaching,
    nextStep,
    previousStep,
    stopTeaching,
    
    // Interaction
    answerQuestion,
    askQuestion,
    
    // Event callbacks
    setOnTeachingStep,
    setOnVoiceMessage,
    setOnCanvasUpdate,
    setOnQuizQuestion,
    
    // Raw socket for advanced usage
    socket,
    sendMessage
  };
};

export default useTeachingWebSocket;