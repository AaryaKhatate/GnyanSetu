import React, { useState, useEffect, useCallback } from 'react';
import EnhancedTeachingBoard from './EnhancedTeachingBoard';
import './LessonPlayer.css';

/**
 * Lesson Player Component
 * 
 * Integrates lesson service V2 and visualization service V2
 * Features:
 * - PDF upload with loading indicator and stop button
 * - Real-time progress tracking
 * - Lesson history with delete functionality
 * - Enhanced teaching board with playback controls
 */

const LESSON_SERVICE_URL = 'http://localhost:8003';
const VISUALIZATION_SERVICE_URL = 'http://localhost:8006';

const LessonPlayer = ({ userId = 'default_user' }) => {
  const [view, setView] = useState('dashboard'); // dashboard, upload, teaching
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(''); // idle, uploading, processing, completed, failed
  const [currentLessonId, setCurrentLessonId] = useState(null);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [visualization, setVisualization] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingStatusInterval, setProcessingStatusInterval] = useState(null);

  // Load user history
  useEffect(() => {
    loadHistory();
  }, [userId]);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${LESSON_SERVICE_URL}/api/lessons/user/${userId}/history`);
      const data = await response.json();
      setHistory(data.lessons || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setSelectedFile(null);
    }
  };

  // Upload and process PDF
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setView('upload');
    setUploadStatus('uploading');
    setUploadProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('user_id', userId);

      // Upload PDF
      const uploadResponse = await fetch(`${LESSON_SERVICE_URL}/api/lessons/upload`, {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      const uploadData = await uploadResponse.json();
      const lessonId = uploadData.lesson_id;
      setCurrentLessonId(lessonId);
      setUploadStatus('processing');
      setUploadProgress(10);

      // Poll for processing status
      const interval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${LESSON_SERVICE_URL}/api/lessons/${lessonId}/status`);
          const statusData = await statusResponse.json();

          setUploadProgress(statusData.progress || 0);
          setUploadStatus(statusData.status);

          if (statusData.status === 'completed') {
            clearInterval(interval);
            await loadLessonAndVisualization(lessonId);
          } else if (statusData.status === 'failed' || statusData.status === 'cancelled') {
            clearInterval(interval);
            setError(`Processing ${statusData.status}`);
            setUploadStatus('failed');
          }
        } catch (error) {
          console.error('Status check failed:', error);
        }
      }, 2000);

      setProcessingStatusInterval(interval);

    } catch (error) {
      console.error('Upload failed:', error);
      setError(error.message);
      setUploadStatus('failed');
    }
  };

  // Load lesson and generate visualization
  const loadLessonAndVisualization = async (lessonId) => {
    try {
      setIsLoading(true);

      // Get lesson content
      const lessonResponse = await fetch(`${LESSON_SERVICE_URL}/api/lessons/${lessonId}`);
      const lessonData = await lessonResponse.json();
      setCurrentLesson(lessonData);

      // Generate visualization
      const vizResponse = await fetch(`${VISUALIZATION_SERVICE_URL}/api/visualizations/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lesson_id: lessonId,
          content: {
            sections: lessonData.content.sections,
            images: lessonData.images,
            subject: lessonData.subject
          }
        })
      });

      if (!vizResponse.ok) {
        throw new Error('Visualization generation failed');
      }

      const vizData = await vizResponse.json();
      setVisualization(vizData);

      // Switch to teaching view
      setView('teaching');
      setUploadStatus('completed');
      
      // Reload history
      await loadHistory();

    } catch (error) {
      console.error('Failed to load lesson:', error);
      setError('Failed to prepare lesson for teaching');
    } finally {
      setIsLoading(false);
    }
  };

  // Stop processing
  const handleStopProcessing = async () => {
    if (processingStatusInterval) {
      clearInterval(processingStatusInterval);
      setProcessingStatusInterval(null);
    }

    if (currentLessonId) {
      try {
        await fetch(`${LESSON_SERVICE_URL}/api/lessons/${currentLessonId}/stop`, {
          method: 'POST'
        });
      } catch (error) {
        console.error('Failed to stop processing:', error);
      }
    }

    setView('dashboard');
    setUploadStatus('idle');
    setCurrentLessonId(null);
    setSelectedFile(null);
  };

  // Play lesson from history
  const handlePlayLesson = async (lessonId) => {
    try {
      setIsLoading(true);
      await loadLessonAndVisualization(lessonId);
    } catch (error) {
      console.error('Failed to play lesson:', error);
      setError('Failed to load lesson');
    } finally {
      setIsLoading(false);
    }
  };

  // Delete lesson from history
  const handleDeleteLesson = async (lessonId, event) => {
    event.stopPropagation(); // Prevent triggering play

    if (!window.confirm('Are you sure you want to delete this lesson?')) {
      return;
    }

    try {
      const response = await fetch(`${LESSON_SERVICE_URL}/api/lessons/${lessonId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Remove from history
        setHistory(history.filter(item => item.lesson_id !== lessonId));
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      console.error('Failed to delete lesson:', error);
      setError('Failed to delete lesson');
    }
  };

  // Complete teaching session
  const handleTeachingComplete = () => {
    setView('dashboard');
    setCurrentLesson(null);
    setVisualization(null);
    setCurrentLessonId(null);
  };

  // Render views
  const renderDashboard = () => (
    <div className="dashboard-view">
      <div className="upload-section">
        <h2>Start New Lesson</h2>
        <div className="file-upload">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            id="pdf-upload"
            className="file-input"
          />
          <label htmlFor="pdf-upload" className="file-label">
            <svg viewBox="0 0 24 24" width="48" height="48">
              <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>
            <span>{selectedFile ? selectedFile.name : 'Choose PDF File'}</span>
          </label>
          <button 
            className="upload-button" 
            onClick={handleUpload}
            disabled={!selectedFile}
          >
            Start Learning
          </button>
        </div>
        {error && <div className="error-message">{error}</div>}
      </div>

      <div className="history-section">
        <h2>Your Learning History</h2>
        <div className="history-list">
          {history.length === 0 ? (
            <div className="empty-history">
              <p>No lessons yet. Upload a PDF to get started!</p>
            </div>
          ) : (
            history.map(lesson => (
              <div 
                key={lesson.lesson_id} 
                className="history-item"
                onClick={() => handlePlayLesson(lesson.lesson_id)}
              >
                <div className="history-item-icon">
                  <svg viewBox="0 0 24 24" width="32" height="32">
                    <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2Z" />
                  </svg>
                </div>
                <div className="history-item-info">
                  <h3>{lesson.title}</h3>
                  <p className="history-item-subject">{lesson.subject}</p>
                  <p className="history-item-date">
                    {new Date(lesson.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="history-item-actions">
                  <button 
                    className="history-action-button delete"
                    onClick={(e) => handleDeleteLesson(lesson.lesson_id, e)}
                    title="Delete lesson"
                  >
                    <svg viewBox="0 0 24 24" width="20" height="20">
                      <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const renderUploadProgress = () => (
    <div className="upload-progress-view">
      <div className="progress-container">
        <div className="progress-spinner">
          <svg className="circular" viewBox="25 25 50 50">
            <circle
              className="path"
              cx="50"
              cy="50"
              r="20"
              fill="none"
              strokeWidth="4"
              strokeMiterlimit="10"
            />
          </svg>
        </div>
        <h2>Processing Your Lesson</h2>
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <span className="progress-percentage">{uploadProgress}%</span>
        </div>
        <p className="progress-status">
          {uploadStatus === 'uploading' && 'Uploading PDF...'}
          {uploadStatus === 'processing' && uploadProgress < 30 && 'Extracting content...'}
          {uploadStatus === 'processing' && uploadProgress >= 30 && uploadProgress < 50 && 'Analyzing images...'}
          {uploadStatus === 'processing' && uploadProgress >= 50 && 'Generating lesson content...'}
        </p>
        <button className="stop-button" onClick={handleStopProcessing}>
          Stop Processing
        </button>
      </div>
    </div>
  );

  const renderTeaching = () => (
    <div className="teaching-view">
      {visualization && visualization.scenes ? (
        <EnhancedTeachingBoard 
          scenes={visualization.scenes}
          onComplete={handleTeachingComplete}
          lessonId={currentLessonId}
        />
      ) : (
        <div className="teaching-loader">
          <div className="loader-spinner" />
          <p>Preparing visualization...</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="lesson-player">
      {view === 'dashboard' && renderDashboard()}
      {view === 'upload' && renderUploadProgress()}
      {view === 'teaching' && renderTeaching()}
      
      {isLoading && (
        <div className="global-loader">
          <div className="loader-spinner" />
        </div>
      )}
    </div>
  );
};

export default LessonPlayer;
