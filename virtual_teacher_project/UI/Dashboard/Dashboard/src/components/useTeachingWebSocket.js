import React, { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket Hook for Teaching Service Connection
export const useTeachingWebSocket = () => {
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [lessonCommands, setLessonCommands] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [messages, setMessages] = useState([]);
  
  const reconnectTimeoutRef = useRef();
  const playbackTimeoutRef = useRef();

  // Connect to Teaching Service WebSocket
  const connect = useCallback(() => {
    // Prevent multiple connections
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
      console.log('WebSocket already connecting or connected, skipping');
      return;
    }
    
    try {
      const wsUrl = 'ws://localhost:8004/ws/teaching/';
      console.log('Connecting to Teaching Service:', wsUrl);
      
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = (event) => {
        console.log('🔗 Connected to Teaching Service');
        console.log('🔗 WebSocket ready state:', websocket.readyState);
        setWs(websocket);
        setConnected(true);
        setMessages(prev => [...prev, {
          type: 'system',
          message: 'Connected to AI Teacher',
          timestamp: new Date().toISOString()
        }]);
        
        // Generate a session ID immediately
        const tempSessionId = 'temp_' + Math.random().toString(36).substr(2, 8);
        setSessionId(tempSessionId);
        console.log('🆔 Generated temporary session ID:', tempSessionId);
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received from Teaching Service:', data);
          handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      websocket.onclose = (event) => {
        console.log('Disconnected from Teaching Service');
        setWs(null);
        setConnected(false);
        setMessages(prev => [...prev, {
          type: 'system',
          message: 'Disconnected from AI Teacher. Attempting to reconnect...',
          timestamp: new Date().toISOString()
        }]);
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (!connected) {
            connect();
          }
        }, 3000);
      };
      
      websocket.onerror = (error) => {
        console.error('Teaching Service WebSocket error:', error);
        setMessages(prev => [...prev, {
          type: 'error',
          message: 'Connection error. Please ensure Teaching Service is running on port 8004.',
          timestamp: new Date().toISOString()
        }]);
      };
      
    } catch (error) {
      console.error('Failed to connect to Teaching Service:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        message: 'Failed to connect. Please check if Teaching Service is running.',
        timestamp: new Date().toISOString()
      }]);
    }
  }, [ws]);

  // Execute lesson commands on whiteboard (MOVED BEFORE handleMessage)
  const executeCommands = useCallback((commands, onCommandExecuted) => {
    if (!commands || commands.length === 0) return;
    
    console.log('🎭 Executing teaching commands:', commands);
    
    let stepIndex = 0;
    
    const executeStep = () => {
      if (stepIndex >= commands.length) {
        setIsPlaying(false);
        return;
      }
      
      const command = commands[stepIndex];
      console.log('🎯 Executing command:', command);
      
      // Handle different command types
      switch (command.type) {
        case 'speak':
          if (window.speechSynthesis) {
            const utterance = new SpeechSynthesisUtterance(command.text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            window.speechSynthesis.speak(utterance);
            console.log('🗣️ Speaking:', command.text);
          }
          break;
          
        case 'write':
          // Trigger write command on canvas
          window.dispatchEvent(new CustomEvent('teachingCommand', {
            detail: {
              type: 'write',
              text: command.text,
              x: command.x || 10,
              y: command.y || 10,
              fontSize: command.font_size || 16,
              color: command.color || '#000000'
            }
          }));
          console.log('✍️ Writing:', command.text);
          break;
          
        case 'draw':
          // Trigger draw command on canvas
          window.dispatchEvent(new CustomEvent('teachingCommand', {
            detail: {
              type: 'draw',
              shape: command.shape,
              x: command.x || 10,
              y: command.y || 10,
              width: command.width || 50,
              height: command.height || 30,
              color: command.color || '#e5e7eb',
              stroke: command.stroke || '#9ca3af'
            }
          }));
          console.log('🎨 Drawing:', command.shape);
          break;
          
        default:
          console.log('❓ Unknown command type:', command.type);
      }
      
      // Call the callback to update the whiteboard
      if (onCommandExecuted) {
        onCommandExecuted(command, stepIndex);
      }
      
      stepIndex++;
      setCurrentStep(stepIndex);
      
      // Schedule next command
      const delay = command.duration ? command.duration * 1000 : 3000;
      playbackTimeoutRef.current = setTimeout(executeStep, delay);
    };
    
    setIsPlaying(true);
    executeStep();
  }, []);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((data) => {
    console.log('📨 Received message:', data.type, data);
    
    switch (data.type) {
      case 'connection_established':
        setSessionId(data.session_id);
        console.log('🆔 Session ID set:', data.session_id);
        setMessages(prev => [...prev, {
          type: 'system',
          message: `Teaching session started: ${data.session_id}`,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'lesson_generation_started':
        setMessages(prev => [...prev, {
          type: 'system',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'lesson_ready':
        console.log('🎓 Lesson ready with commands:', data.commands);
        if (data.commands && Array.isArray(data.commands)) {
          setLessonCommands(data.commands);
          setCurrentStep(0);
        }
        setMessages(prev => [...prev, {
          type: 'teacher',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'lesson_playback_started':
        console.log('▶️ Lesson playback started');
        setIsPlaying(true);
        setMessages(prev => [...prev, {
          type: 'system',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'teaching_command':
        console.log('🎯 Teaching command received:', data.command);
        // Execute the teaching command immediately
        executeCommands([data.command]);
        setCurrentStep(data.step - 1);
        break;
        
      case 'lesson_completed':
        console.log('✅ Lesson completed');
        setIsPlaying(false);
        setMessages(prev => [...prev, {
          type: 'system',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'ai_response':
        setMessages(prev => [...prev, {
          type: 'teacher',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      case 'error':
        console.error('❌ Teaching Service error:', data.message);
        setMessages(prev => [...prev, {
          type: 'error',
          message: data.message,
          timestamp: data.timestamp
        }]);
        break;
        
      default:
        console.log('❓ Unknown message type:', data.type);
    }
  }, [executeCommands]);

  // Send PDF document to teaching service
  const sendPDFDocument = useCallback((pdfData) => {
    console.log('📄 === PDF SEND DEBUG START ===');
    console.log('📄 WebSocket state:', ws?.readyState);
    console.log('📄 WebSocket OPEN constant:', WebSocket.OPEN);
    console.log('📄 PDF Data received:', pdfData);
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket not connected - State:', ws?.readyState);
      return;
    }
    
    // Check if PDF text is undefined and try to get it from sessionStorage
    let pdfText = pdfData.pdf_text;
    console.log('📄 Initial PDF text:', pdfText);
    
    if (!pdfText || pdfText === 'undefined' || pdfText === undefined) {
      pdfText = sessionStorage.getItem("pdfText") || "";
      console.log('📄 Retrieved from sessionStorage - length:', pdfText?.length, 'characters');
      console.log('📄 SessionStorage PDF preview:', pdfText?.substring(0, 100) + '...');
    }
    
    // If still no PDF text, don't send the message
    if (!pdfText || pdfText.trim() === '') {
      console.error('❌ No PDF text available, skipping message send');
      console.log('📄 Available sessionStorage keys:', Object.keys(sessionStorage));
      return;
    }
    
    const message = {
      type: 'pdf_document',
      topic: pdfData.topic,
      pdf_filename: pdfData.pdf_filename,
      pdf_text: pdfText,
      conversation_id: pdfData.conversation_id,
      user_id: pdfData.user_id || 'anonymous',
      timestamp: new Date().toISOString()
    };
    
    console.log('📤 Sending PDF to Teaching Service:');
    console.log('📤 Message type:', message.type);
    console.log('📤 Topic:', message.topic);
    console.log('📤 Filename:', message.pdf_filename);
    console.log('📤 Text length:', message.pdf_text.length);
    console.log('📤 Full message:', message);
    
    try {
      ws.send(JSON.stringify(message));
      console.log('✅ PDF message sent successfully');
    } catch (error) {
      console.error('❌ Error sending PDF message:', error);
    }
    
    console.log('📄 === PDF SEND DEBUG END ===');
  }, [ws]);

  // Send user message
  const sendMessage = useCallback((message) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }
    
    const messageData = {
      type: 'user_message',
      message: message,
      user_id: 'student_' + Date.now(),
      session_id: sessionId,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, {
      type: 'user',
      message: message,
      timestamp: new Date().toISOString()
    }]);
    
    ws.send(JSON.stringify(messageData));
  }, [ws, sessionId]);

  // Start lesson playback
  const startLesson = useCallback((onCommandExecuted) => {
    if (lessonCommands.length === 0) {
      console.warn('No lesson commands available');
      return;
    }
    
    setCurrentStep(0);
    executeCommands(lessonCommands, onCommandExecuted);
  }, [lessonCommands, executeCommands]);

  // Stop lesson playback
  const stopLesson = useCallback(() => {
    setIsPlaying(false);
    if (playbackTimeoutRef.current) {
      clearTimeout(playbackTimeoutRef.current);
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }, []);

  // Connect on mount - SINGLE CONNECTION ONLY
  useEffect(() => {
    let mounted = true;
    
    // Only connect if not already connected
    if (!connected && !ws) {
      console.log('🔌 Initiating WebSocket connection...');
      connect();
    }
    
    return () => {
      mounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (playbackTimeoutRef.current) {
        clearTimeout(playbackTimeoutRef.current);
      }
      if (ws) {
        console.log('🔌 Cleaning up WebSocket on unmount');
        ws.close(1000, 'Component unmounting');
      }
    };
  }, []); // Empty dependency array - only run once

  // Test function for debugging
  const sendTestPDF = useCallback(() => {
    console.log('🧪 Sending test PDF for debugging...');
    const testPDFData = {
      topic: 'Test Linear Algebra',
      pdf_filename: 'test_lesson.pdf',
      pdf_text: `Linear Algebra Basics

Vectors and Matrices
- A vector is a quantity with both magnitude and direction
- Vectors can be represented as arrays of numbers
- Example: v = [3, 4] represents a 2D vector

Matrix Operations
- Addition: Add corresponding elements
- Multiplication: Dot product of rows and columns

Applications
- Graphics and animation
- Machine learning algorithms
- Physics simulations`,
      conversation_id: 'test_' + Date.now(),
      user_id: 'test_user'
    };
    
    sendPDFDocument(testPDFData);
  }, [sendPDFDocument]);

  return {
    connected,
    sessionId,
    messages,
    lessonCommands,
    currentStep,
    isPlaying,
    sendPDFDocument,
    sendMessage,
    startLesson,
    stopLesson,
    connect,
    sendTestPDF // Add test function
  };
};

export default useTeachingWebSocket;