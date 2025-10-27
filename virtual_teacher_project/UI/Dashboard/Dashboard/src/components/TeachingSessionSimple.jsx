import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import TeachingCanvas from './TeachingCanvas';
import Notes from './Notes';
import { speak, stopSpeaking } from '../utils/ttsController';
import axios from 'axios';
import './TeachingSession.css';

/**
 * TeachingSession Component - Simplified and Working Version
 * Main interactive teaching interface with Konva.js whiteboard
 */
export default function TeachingSession() {
    const { lessonId } = useParams(); // Get lessonId from URL parameter
    const [teachingData, setTeachingData] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [lessonStarted, setLessonStarted] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [showNotes, setShowNotes] = useState(false);
    const [lessonCompleted, setLessonCompleted] = useState(false);
    
    // Load teaching data from visualization service or sessionStorage
    useEffect(() => {
        loadTeachingData();
    }, [lessonId]);
    
    const loadTeachingData = async () => {
        // First try sessionStorage (for lessons generated in current session)
        const sessionData = sessionStorage.getItem('lessonData');
        if (sessionData) {
            try {
                const parsedData = JSON.parse(sessionData);
                
                // Check if it has v2 visualization format
                if (parsedData.teaching_sequence) {
                    setTeachingData(parsedData);
                    setLoading(false);
                    console.log('✅ Loaded teaching data from sessionStorage');
                    return;
                }
                
                // Check if it has teaching_steps (old format) - convert to v2
                if (parsedData.teaching_steps) {
                    const converted = {
                        teaching_sequence: parsedData.teaching_steps.map(step => ({
                            type: "explanation",
                            text_explanation: step.text_explanation || step.title,
                            tts_text: step.speech_text || step.title,
                            whiteboard_commands: step.drawing_commands || []
                        })),
                        images: parsedData.images || [],
                        notes_content: parsedData.notes_content || "",
                        quiz: parsedData.quiz || []
                    };
                    setTeachingData(converted);
                    setLoading(false);
                    console.log('✅ Converted and loaded old format from sessionStorage');
                    return;
                }
            } catch (err) {
                console.warn('Failed to parse sessionStorage data:', err);
            }
        }
        
        // If no sessionStorage data or parsing failed, try API
        if (!lessonId) {
            setError('No lesson ID provided and no session data available');
            setLoading(false);
            return;
        }
        
        try {
            setLoading(true);
            const response = await axios.get(`http://localhost:8006/visualization/v2/${lessonId}`);
            
            if (response.data && response.data.teaching_sequence) {
                setTeachingData(response.data);
                console.log('✅ Loaded teaching data from API:', response.data);
            } else {
                throw new Error('Invalid teaching data format');
            }
            
            setLoading(false);
        } catch (err) {
            console.error('Failed to load teaching data:', err);
            setError(err.message || 'Failed to load lesson data');
            setLoading(false);
        }
    };
    
    const handleStartLesson = () => {
        console.log("🎬 START LESSON CLICKED");
        console.log("📚 Teaching data exists:", !!teachingData);
        console.log("📊 Number of steps:", teachingData?.teaching_sequence?.length);
        if (teachingData && teachingData.teaching_sequence && teachingData.teaching_sequence[0]) {
            console.log("📝 First step data:", teachingData.teaching_sequence[0]);
        }
        
        setLessonStarted(true);
        presentStep(0);
    };
    
    const presentStep = (stepIndex) => {
        console.log(`🎯 PRESENT STEP ${stepIndex}`);
        
        if (!teachingData || stepIndex >= teachingData.teaching_sequence.length) {
            console.log('❌ No more steps or no teaching data');
            return;
        }
        
        const step = teachingData.teaching_sequence[stepIndex];
        console.log(`📋 Step ${stepIndex} data:`, step);
        console.log(`🎨 Whiteboard commands:`, step.whiteboard_commands);
        
        // Stop any current speech
        stopSpeaking();
        
        // Check if this is the last step
        const isLastStep = stepIndex === teachingData.teaching_sequence.length - 1;
        
        // Speak narration with auto-advance
        setIsSpeaking(true);
        speak(step.tts_text || step.text_explanation || 'No narration available', () => {
            setIsSpeaking(false);
            // Auto-advance after 1 second pause (if not last step)
            if (!isLastStep) {
                setTimeout(() => {
                    if (currentStep === stepIndex) {
                        handleNext();
                    }
                }, 1000);
            } else {
                // Lesson completed
                setLessonCompleted(true);
            }
        });
        
        setCurrentStep(stepIndex);
    };
    
    const handleNext = () => {
        if (currentStep < teachingData.teaching_sequence.length - 1) {
            stopSpeaking();
            presentStep(currentStep + 1);
        }
    };
    
    const handleRepeat = () => {
        stopSpeaking();
        presentStep(currentStep);
    };
    
    const handlePause = () => {
        stopSpeaking();
        setIsSpeaking(false);
    };
    
    const handleViewNotes = () => {
        stopSpeaking();
        setShowNotes(true);
    };
    
    const handleRetakeLesson = () => {
        setShowNotes(false);
        setLessonStarted(false);
        setLessonCompleted(false);
        setCurrentStep(0);
        stopSpeaking();
    };
    
    const handleEndSession = () => {
        // This would typically navigate to dashboard or quiz
        console.log('End session clicked');
        setShowNotes(false);
    };
    
    // If showing notes, render Notes component
    if (showNotes) {
        return (
            <Notes 
                onRetakeLesson={handleRetakeLesson}
                onEndSession={handleEndSession}
                notesContent={teachingData?.notes_content}
            />
        );
    }
    
    // Loading state
    if (loading) {
        return (
            <div className="teaching-session-container">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Loading interactive lesson...</p>
                </div>
            </div>
        );
    }
    
    // Error state
    if (error) {
        return (
            <div className="teaching-session-container">
                <div className="error-container">
                    <h2>⚠️ Error Loading Lesson</h2>
                    <p>{error}</p>
                    <button onClick={loadTeachingData} className="retry-button">
                        Retry
                    </button>
                </div>
            </div>
        );
    }
    
    // No data state
    if (!teachingData) {
        return (
            <div className="teaching-session-container">
                <div className="error-container">
                    <h2>No Teaching Data Available</h2>
                    <p>Please upload a PDF and generate a lesson first.</p>
                </div>
            </div>
        );
    }
    
    const currentStepData = teachingData.teaching_sequence[currentStep];
    const isLastStep = currentStep >= teachingData.teaching_sequence.length - 1;
    
    return (
        <div className="teaching-session-container">
            {/* Header */}
            <div className="teaching-header">
                <h1>🎓 GnyanSetu Interactive Lesson</h1>
                <div className="progress-indicator">
                    Step {currentStep + 1} of {teachingData.teaching_sequence.length}
                    <div className="progress-bar">
                        <div 
                            className="progress-fill" 
                            style={{ width: `${((currentStep + 1) / teachingData.teaching_sequence.length) * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>
            
            {/* Main Content */}
            <div className="teaching-content">
                {/* Whiteboard Section */}
                <div className="whiteboard-section">
                    <div className="whiteboard-container">
                        <TeachingCanvas
                            teachingStep={lessonStarted ? teachingData.teaching_sequence[currentStep] : null}
                            isPlaying={isSpeaking}
                            canvasWidth={800}
                            canvasHeight={600}
                        />
                    </div>
                </div>
                
                {/* Explanation Panel */}
                <div className="explanation-panel">
                    <div className="panel-header">
                        <h2>📝 Current Explanation</h2>
                        {isSpeaking && <div className="speaking-indicator">🔊 Speaking...</div>}
                    </div>
                    
                    <div className="panel-content">
                        {lessonStarted ? (
                            <div className="explanation-text">
                                <p>{currentStepData?.text_explanation}</p>
                            </div>
                        ) : (
                            <div className="start-prompt">
                                <p>Click "Start Lesson" to begin the interactive learning experience!</p>
                            </div>
                        )}
                    </div>
                    
                    {/* Controls */}
                    <div className="controls-section">
                        {!lessonStarted ? (
                            <button
                                onClick={handleStartLesson}
                                className="control-button start-button"
                            >
                                ▶️ Start Lesson
                            </button>
                        ) : lessonCompleted ? (
                            <button
                                onClick={handleViewNotes}
                                className="control-button start-button"
                            >
                                📚 View Notes
                            </button>
                        ) : (
                            <>
                                <button
                                    onClick={handleNext}
                                    disabled={isLastStep}
                                    className="control-button next-button"
                                >
                                    ⏭️ Next Step
                                </button>
                                <button
                                    onClick={handleRepeat}
                                    className="control-button repeat-button"
                                >
                                    🔄 Repeat
                                </button>
                                {isSpeaking && (
                                    <button
                                        onClick={handlePause}
                                        className="control-button pause-button"
                                    >
                                        ⏸️ Pause
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                    
                    {/* Navigation hint */}
                    {lessonStarted && (
                        <div className="navigation-hint">
                            {lessonCompleted ? (
                                <p>🎉 Lesson complete! Click "View Notes" to review.</p>
                            ) : isLastStep ? (
                                <p>✅ You've reached the final step!</p>
                            ) : (
                                <p>💡 Lesson will auto-advance after narration</p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
