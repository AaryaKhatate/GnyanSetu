import React, { useState, useEffect } from 'react';
import TeachingCanvas from './TeachingCanvas';
import { speak, stopSpeaking } from '../utils/ttsController';
import axios from 'axios';
import './TeachingSession.css';

/**
 * TeachingSession Component
 * Main interactive teaching interface with Konva.js whiteboard
 * 
 * Features:
 * - Step-by-step teaching progression
 * - Synchronized TTS narration
 * - Interactive whiteboard with visual aids
 * - Navigation controls (Start, Next, Repeat)
 * 
 * Props:
 * - lessonId: ID of the lesson to display
 */
export default function TeachingSession({ lessonId }) {
    const [teachingData, setTeachingData] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [lessonStarted, setLessonStarted] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    
    // Load teaching data from visualization service
    useEffect(() => {
        loadTeachingData();
    }, [lessonId]);
    
    const loadTeachingData = async () => {
        if (!lessonId) {
            setError('No lesson ID provided');
            setLoading(false);
            return;
        }
        
        try {
            setLoading(true);
            // Try to get visualization data (new v2 format)
            const response = await axios.get(`http://localhost:8006/visualization/v2/${lessonId}`);
            
            if (response.data && response.data.teaching_sequence) {
                setTeachingData(response.data);
                console.log('✅ Loaded teaching data:', response.data);
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
        setLessonStarted(true);
        presentStep(0);
    };
    
    const presentStep = (stepIndex) => {
        if (!teachingData || stepIndex >= teachingData.teaching_sequence.length) {
            console.log('No more steps');
            return;
        }
        
        const step = teachingData.teaching_sequence[stepIndex];
        
        // Stop any current speech
        stopSpeaking();
        
        // Speak narration with auto-advance
        setIsSpeaking(true);
        speak(step.tts_text, () => {
            setIsSpeaking(false);
            // Auto-advance after 1 second pause (if not last step)
            if (stepIndex < teachingData.teaching_sequence.length - 1) {
                setTimeout(() => {
                    if (currentStep === stepIndex) { // Only advance if still on same step
                        handleNext();
                    }
                }, 1000);
            }
        });
        
        setCurrentStep(stepIndex);
    };
    
    const handleNext = () => {
        if (currentStep < teachingData.teaching_sequence.length - 1) {
            stopSpeaking();
            presentStep(currentStep + 1);
        } else {
            console.log('Reached end of lesson');
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
                            teachingData={teachingData}
                            currentStepIndex={lessonStarted ? currentStep : -1}
                            containerWidth={800}
                            containerHeight={600}
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
                            {isLastStep ? (
                                <p>✅ You've completed the lesson!</p>
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
