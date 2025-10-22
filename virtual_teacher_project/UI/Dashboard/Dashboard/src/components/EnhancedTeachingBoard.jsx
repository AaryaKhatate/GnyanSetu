import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Stage, Layer, Circle, Rect, Line, Arrow, Text, Image as KonvaImage, Group, Path } from 'react-konva';
import { gsap } from 'gsap';
import './EnhancedTeachingBoard.css';

/**
 * Enhanced Teaching Board Component V2
 * 
 * Features:
 * - Play/Pause/Resume controls
 * - Forward/Backward navigation
 * - PowerPoint-style control bar
 * - High-quality visualizations
 * - Natural audio narration
 * - Image support from PDFs
 */

const EnhancedTeachingBoard = ({ 
  scenes = [], 
  onComplete,
  lessonId 
}) => {
  const stageRef = useRef(null);
  const layerRef = useRef(null);
  const audioRef = useRef(null);
  const timelineRef = useRef(null);
  
  const [currentSceneIndex, setCurrentSceneIndex] = useState(0);
  const [renderedShapes, setRenderedShapes] = useState([]);
  const [loadedImages, setLoadedImages] = useState({});
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);
  const [progress, setProgress] = useState(0);
  
  const CANVAS_WIDTH = 1920;
  const CANVAS_HEIGHT = 1080;

  // Load images
  useEffect(() => {
    if (!scenes || scenes.length === 0) return;

    const currentScene = scenes[currentSceneIndex];
    if (!currentScene || !currentScene.shapes) return;

    const imageShapes = currentScene.shapes.filter(shape => 
      shape.type === 'image' && shape.src
    );
    
    imageShapes.forEach(shape => {
      if (!loadedImages[shape.src]) {
        const img = new window.Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
          setLoadedImages(prev => ({ ...prev, [shape.src]: img }));
        };
        
        img.onerror = () => {
          console.error(`Failed to load image: ${shape.src}`);
          const canvas = document.createElement('canvas');
          canvas.width = shape.width || 200;
          canvas.height = shape.height || 200;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#F5F5F5';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.strokeStyle = '#CCCCCC';
          ctx.strokeRect(0, 0, canvas.width, canvas.height);
          ctx.fillStyle = '#999999';
          ctx.font = '16px Arial';
          ctx.textAlign = 'center';
          ctx.fillText('Image unavailable', canvas.width / 2, canvas.height / 2);
          
          const fallbackImg = new window.Image();
          fallbackImg.src = canvas.toDataURL();
          setLoadedImages(prev => ({ ...prev, [shape.src]: fallbackImg }));
        };
        
        img.src = shape.src;
      }
    });
  }, [currentSceneIndex, scenes]);

  // Play scene
  const playScene = useCallback(async (sceneIndex, fromStart = true) => {
    if (!scenes || scenes.length === 0 || sceneIndex >= scenes.length) {
      if (onComplete) onComplete();
      return;
    }

    const scene = scenes[sceneIndex];
    setCurrentSceneIndex(sceneIndex);
    setIsPlaying(true);
    setIsPaused(false);
    setRenderedShapes(scene.shapes || []);

    // Wait for layer to render
    await new Promise(resolve => setTimeout(resolve, 100));

    // Create GSAP timeline
    if (timelineRef.current) {
      timelineRef.current.kill();
    }
    
    const timeline = gsap.timeline({
      onUpdate: () => {
        const progress = (timeline.time() / scene.duration) * 100;
        setProgress(Math.min(progress, 100));
      },
      onComplete: () => {
        setIsPlaying(false);
        // Auto-advance to next scene
        if (sceneIndex < scenes.length - 1) {
          setTimeout(() => playScene(sceneIndex + 1), 1000);
        } else if (onComplete) {
          onComplete();
        }
      }
    });
    
    timelineRef.current = timeline;

    // Execute animations
    const layer = layerRef.current;
    if (layer && scene.animations) {
      scene.animations.forEach(anim => {
        const shapeNode = layer.children[anim.shape_index];
        if (!shapeNode) return;

        const animConfig = {
          duration: anim.duration || 2,
          ease: anim.ease || 'power2.inOut',
          onUpdate: () => layer.batchDraw()
        };

        switch (anim.type) {
          case 'fadeIn':
            shapeNode.opacity(0);
            timeline.to(shapeNode, { opacity: 1, ...animConfig }, anim.start || 0);
            break;
          
          case 'fadeOut':
            timeline.to(shapeNode, { opacity: 0, ...animConfig }, anim.start || 0);
            break;
          
          case 'move':
            if (anim.to) {
              timeline.to(shapeNode, { 
                x: anim.to.x || shapeNode.x(), 
                y: anim.to.y || shapeNode.y(), 
                ...animConfig 
              }, anim.start || 0);
            }
            break;
          
          case 'scale':
            if (anim.from) {
              shapeNode.scale({ x: anim.from.scale || 0, y: anim.from.scale || 0 });
            }
            timeline.to(shapeNode, { 
              scaleX: anim.to?.scale || 1, 
              scaleY: anim.to?.scale || 1, 
              ...animConfig 
            }, anim.start || 0);
            break;
          
          case 'rotate':
            timeline.to(shapeNode, { rotation: anim.rotation || 360, ...animConfig }, anim.start || 0);
            break;
          
          case 'pulse':
            const repeat = anim.repeat !== undefined ? anim.repeat : 2;
            timeline.to(shapeNode, {
              scaleX: 1.2,
              scaleY: 1.2,
              duration: animConfig.duration / 2,
              repeat: repeat * 2 - 1,
              yoyo: true,
              ease: 'power2.inOut',
              onUpdate: () => layer.batchDraw()
            }, anim.start || 0);
            break;
          
          case 'glow':
            timeline.to(shapeNode, {
              shadowColor: '#FFD700',
              shadowBlur: 20,
              shadowOpacity: 0.8,
              duration: animConfig.duration / 2,
              repeat: 1,
              yoyo: true,
              ease: 'power2.inOut',
              onUpdate: () => layer.batchDraw()
            }, anim.start || 0);
            break;
          
          case 'draw':
            // For lines and arrows, animate dashOffset
            if (shapeNode.dash) {
              const length = shapeNode.getSelfRect().width + shapeNode.getSelfRect().height;
              shapeNode.dashOffset(length);
              timeline.to(shapeNode, {
                dashOffset: 0,
                ...animConfig,
                ease: 'none'
              }, anim.start || 0);
            }
            break;
        }
      });
    }

    // Play audio narration
    if (scene.audio && scene.audio.text && fromStart) {
      playAudioNarration(scene.audio);
    }

    // Start timeline
    if (fromStart) {
      timeline.play();
    }
  }, [scenes, onComplete]);

  // Audio narration with Web Speech API
  const playAudioNarration = useCallback((audio) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(audio.text);
      utterance.rate = 0.9; // Slightly slower for clarity
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // Try to use a natural-sounding voice
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.name.includes('Natural') || 
        voice.name.includes('Enhanced') ||
        voice.name.includes('Premium')
      ) || voices.find(voice => voice.lang.startsWith('en'));
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  // Start first scene on mount
  useEffect(() => {
    if (scenes && scenes.length > 0 && !isPlaying) {
      playScene(0);
    }
  }, [scenes]);

  // Control handlers
  const handlePlayPause = useCallback(() => {
    if (isPaused) {
      // Resume
      if (timelineRef.current) {
        timelineRef.current.play();
        window.speechSynthesis.resume();
      }
      setIsPaused(false);
      setIsPlaying(true);
    } else if (isPlaying) {
      // Pause
      if (timelineRef.current) {
        timelineRef.current.pause();
        window.speechSynthesis.pause();
      }
      setIsPaused(true);
      setIsPlaying(false);
    } else {
      // Start/Restart
      playScene(currentSceneIndex);
    }
  }, [isPaused, isPlaying, currentSceneIndex, playScene]);

  const handleNext = useCallback(() => {
    if (currentSceneIndex < scenes.length - 1) {
      if (timelineRef.current) {
        timelineRef.current.kill();
      }
      window.speechSynthesis.cancel();
      playScene(currentSceneIndex + 1);
    }
  }, [currentSceneIndex, scenes.length, playScene]);

  const handlePrevious = useCallback(() => {
    if (currentSceneIndex > 0) {
      if (timelineRef.current) {
        timelineRef.current.kill();
      }
      window.speechSynthesis.cancel();
      playScene(currentSceneIndex - 1);
    }
  }, [currentSceneIndex, playScene]);

  // Render shape components
  const renderShape = useCallback((shape, index) => {
    const commonProps = {
      key: shape.shape_id || index,
      x: shape.x || 0,
      y: shape.y || 0,
      opacity: shape.opacity || 1,
    };

    switch (shape.type) {
      case 'circle':
        return (
          <Circle
            {...commonProps}
            radius={shape.radius || 50}
            fill={shape.fill || '#1976D2'}
            stroke={shape.stroke}
            strokeWidth={shape.strokeWidth || 0}
          />
        );
      
      case 'rectangle':
        return (
          <Rect
            {...commonProps}
            width={shape.width || 100}
            height={shape.height || 100}
            fill={shape.fill || '#1976D2'}
            stroke={shape.stroke}
            strokeWidth={shape.strokeWidth || 0}
          />
        );
      
      case 'line':
        return (
          <Line
            {...commonProps}
            points={shape.points?.flat() || [0, 0, 100, 100]}
            stroke={shape.stroke || '#000000'}
            strokeWidth={shape.strokeWidth || 2}
          />
        );
      
      case 'arrow':
        return (
          <Arrow
            {...commonProps}
            points={shape.points?.flat() || [0, 0, 100, 100]}
            stroke={shape.stroke || '#000000'}
            strokeWidth={shape.strokeWidth || 2}
            fill={shape.stroke || '#000000'}
            pointerLength={10}
            pointerWidth={10}
          />
        );
      
      case 'text':
        return (
          <Text
            {...commonProps}
            text={shape.text || ''}
            fontSize={shape.fontSize || 24}
            fontFamily={shape.fontFamily || 'Arial'}
            fill={shape.fill || '#000000'}
            align="center"
            width={shape.width}
          />
        );
      
      case 'image':
        const image = loadedImages[shape.src];
        if (!image) return null;
        return (
          <KonvaImage
            {...commonProps}
            image={image}
            width={shape.width || image.width}
            height={shape.height || image.height}
          />
        );
      
      case 'path':
        if (!shape.points) return null;
        const pathData = shape.points.map((point, idx) => 
          idx === 0 ? `M ${point[0]} ${point[1]}` : `L ${point[0]} ${point[1]}`
        ).join(' ');
        return (
          <Path
            {...commonProps}
            data={pathData}
            stroke={shape.stroke || '#000000'}
            strokeWidth={shape.strokeWidth || 2}
            fill={shape.fill}
          />
        );
      
      default:
        return null;
    }
  }, [loadedImages]);

  return (
    <div className="enhanced-teaching-board">
      <Stage width={CANVAS_WIDTH} height={CANVAS_HEIGHT} ref={stageRef}>
        <Layer ref={layerRef}>
          {renderedShapes.map((shape, index) => renderShape(shape, index))}
        </Layer>
      </Stage>

      {/* Control Bar (PowerPoint Style) */}
      <div 
        className={`control-bar ${controlsVisible ? 'visible' : 'hidden'}`}
        onMouseEnter={() => setControlsVisible(true)}
        onMouseLeave={() => setControlsVisible(true)}
      >
        <button 
          className="control-button" 
          onClick={handlePrevious}
          disabled={currentSceneIndex === 0}
          title="Previous Scene"
        >
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z" />
          </svg>
        </button>

        <button 
          className="control-button play-pause" 
          onClick={handlePlayPause}
          title={isPaused ? "Resume" : isPlaying ? "Pause" : "Play"}
        >
          {isPaused || !isPlaying ? (
            <svg viewBox="0 0 24 24" width="32" height="32">
              <path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="32" height="32">
              <path fill="currentColor" d="M14,19H18V5H14M6,19H10V5H6V19Z" />
            </svg>
          )}
        </button>

        <button 
          className="control-button" 
          onClick={handleNext}
          disabled={currentSceneIndex === scenes.length - 1}
          title="Next Scene"
        >
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
          </svg>
        </button>

        <div className="progress-info">
          <span className="scene-number">{currentSceneIndex + 1} / {scenes.length}</span>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedTeachingBoard;
