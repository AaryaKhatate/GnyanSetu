import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Stage, Layer, Circle, Rect, Line, Arrow, Text, Image as KonvaImage, Group, Path } from 'react-konva';
import { gsap } from 'gsap';
import Konva from 'konva';

/**
 * KonvaTeachingBoard Component
 * 
 * Renders dynamic visualizations with Konva, animates with GSAP,
 * and synchronizes with audio narration for immersive learning.
 * 
 * Props:
 * - scenes: Array of visualization scenes
 * - onSceneComplete: Callback when a scene finishes
 * - autoPlay: Whether to automatically play scenes
 */

const KonvaTeachingBoard = ({ scenes = [], onSceneComplete, autoPlay = true }) => {
  const stageRef = useRef(null);
  const layerRef = useRef(null);
  const [currentSceneIndex, setCurrentSceneIndex] = useState(0);
  const [renderedShapes, setRenderedShapes] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loadedImages, setLoadedImages] = useState({});
  const audioRef = useRef(null);
  
  const CANVAS_WIDTH = 1920;
  const CANVAS_HEIGHT = 1080;

  // Load images
  useEffect(() => {
    if (!scenes || scenes.length === 0) return;

    const currentScene = scenes[currentSceneIndex];
    if (!currentScene || !currentScene.shapes) return;

    // Find all image shapes
    const imageShapes = currentScene.shapes.filter(shape => shape.type === 'image' && shape.src);
    
    if (imageShapes.length === 0) return;

    // Load images
    imageShapes.forEach(shape => {
      if (!loadedImages[shape.src]) {
        const img = new window.Image();
        img.onload = () => {
          setLoadedImages(prev => ({
            ...prev,
            [shape.src]: img
          }));
        };
        img.onerror = () => {
          console.error(`Failed to load image: ${shape.src}`);
        };
        img.src = shape.src;
      }
    });
  }, [currentSceneIndex, scenes, loadedImages]);

  // Play scene
  const playScene = useCallback(async (sceneIndex) => {
    if (!scenes || scenes.length === 0 || sceneIndex >= scenes.length) {
      console.log('No more scenes to play');
      return;
    }

    const scene = scenes[sceneIndex];
    console.log(`▶️ Playing scene: ${scene.scene_id} (${scene.title || 'Untitled'})`);
    
    setIsPlaying(true);
    setRenderedShapes(scene.shapes || []);

    // Wait for layer to render
    await new Promise(resolve => setTimeout(resolve, 100));

    // Execute animations
    if (scene.animations && scene.animations.length > 0) {
      await executeAnimations(scene.animations, scene.shapes);
    }

    // Play audio narration
    if (scene.audio && scene.audio.text) {
      playAudioNarration(scene.audio);
    }

    // Wait for scene duration
    await new Promise(resolve => setTimeout(resolve, scene.duration * 1000));

    setIsPlaying(false);
    
    if (onSceneComplete) {
      onSceneComplete(sceneIndex);
    }

    // Auto-play next scene
    if (autoPlay && sceneIndex < scenes.length - 1) {
      setCurrentSceneIndex(sceneIndex + 1);
    }
  }, [scenes, autoPlay, onSceneComplete]);

  // Execute GSAP animations
  const executeAnimations = async (animations, shapes) => {
    const layer = layerRef.current;
    if (!layer) return;

    const timeline = gsap.timeline();

    animations.forEach(anim => {
      const shapeNode = layer.children[anim.shape_index];
      if (!shapeNode) {
        console.warn(`Shape ${anim.shape_index} not found for animation`);
        return;
      }

      const animConfig = {
        duration: anim.duration || 2,
        delay: anim.delay || 0,
        ease: anim.ease || 'power2.inOut',
        onUpdate: () => layer.batchDraw()
      };

      switch (anim.type) {
        case 'fadeIn':
          timeline.fromTo(
            shapeNode,
            { opacity: 0 },
            { ...animConfig, opacity: 1 },
            anim.delay || 0
          );
          break;

        case 'fadeOut':
          timeline.to(
            shapeNode,
            { ...animConfig, opacity: 0 },
            anim.delay || 0
          );
          break;

        case 'scale':
          const fromScale = anim.from_props || { scaleX: 0, scaleY: 0 };
          const toScale = anim.to_props || { scaleX: 1, scaleY: 1 };
          timeline.fromTo(
            shapeNode,
            fromScale,
            { ...animConfig, ...toScale },
            anim.delay || 0
          );
          break;

        case 'move':
          if (anim.to_props) {
            timeline.to(
              shapeNode,
              { ...animConfig, x: anim.to_props.x, y: anim.to_props.y },
              anim.delay || 0
            );
          }
          break;

        case 'rotate':
          const toRotation = anim.to_props?.rotation || 360;
          timeline.to(
            shapeNode,
            { ...animConfig, rotation: toRotation },
            anim.delay || 0
          );
          break;

        case 'pulse':
          timeline.to(
            shapeNode,
            {
              ...animConfig,
              scaleX: 1.2,
              scaleY: 1.2,
              yoyo: true,
              repeat: anim.repeat || 1
            },
            anim.delay || 0
          );
          break;

        case 'glow':
          timeline.to(
            shapeNode,
            {
              ...animConfig,
              shadowBlur: 20,
              shadowColor: anim.to_props?.glow_color || '#FFD700',
              yoyo: anim.yoyo || false,
              repeat: anim.repeat || 0
            },
            anim.delay || 0
          );
          break;

        case 'draw':
          // Line drawing animation - works for Line, Arrow, and Path
          if (shapeNode.className === 'Line' || shapeNode.className === 'Arrow') {
            const points = shapeNode.points();
            const totalLength = points.length * 2;
            timeline.fromTo(
              shapeNode,
              { dash: [0, totalLength], dashOffset: totalLength },
              { ...animConfig, dash: [totalLength, 0], dashOffset: 0 },
              anim.delay || 0
            );
          } else if (shapeNode.className === 'Path') {
            // For SVG paths, use strokeDashoffset technique
            const pathLength = shapeNode.getLength ? shapeNode.getLength() : 1000;
            shapeNode.dash([pathLength, pathLength]);
            shapeNode.dashOffset(pathLength);
            
            timeline.to(
              shapeNode,
              {
                ...animConfig,
                dashOffset: 0
              },
              anim.delay || 0
            );
          }
          break;

        case 'write':
          // Text writing animation (character by character)
          if (shapeNode.className === 'Text') {
            const fullText = shapeNode.text();
            const charCount = fullText.length;
            const charDuration = animConfig.duration / charCount;

            for (let i = 0; i <= charCount; i++) {
              timeline.to(
                shapeNode,
                {
                  duration: charDuration,
                  onUpdate: () => {
                    shapeNode.text(fullText.substring(0, i));
                    layer.batchDraw();
                  }
                },
                (anim.delay || 0) + i * charDuration
              );
            }
          }
          break;

        case 'orbit':
          if (anim.orbit_center && anim.orbit_radius) {
            const [centerX, centerY] = anim.orbit_center;
            const radius = anim.orbit_radius;
            
            timeline.to(
              shapeNode,
              {
                ...animConfig,
                rotation: 360,
                repeat: anim.repeat || -1,
                ease: 'linear',
                onUpdate: () => {
                  const angle = (shapeNode.rotation() * Math.PI) / 180;
                  shapeNode.x(centerX + radius * Math.cos(angle));
                  shapeNode.y(centerY + radius * Math.sin(angle));
                  layer.batchDraw();
                }
              },
              anim.delay || 0
            );
          }
          break;

        default:
          console.warn(`Unknown animation type: ${anim.type}`);
      }
    });

    return new Promise(resolve => {
      timeline.eventCallback('onComplete', resolve);
    });
  };

  // Play audio narration with TTS
  const playAudioNarration = (audio) => {
    if (!audio || !audio.text) return;

    // Use Web Speech API for TTS
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(audio.text);
      
      if (audio.tts_config) {
        utterance.voice = window.speechSynthesis.getVoices().find(
          voice => voice.name.includes(audio.tts_config.voice || 'Google')
        );
        utterance.rate = audio.tts_config.speaking_rate || 1.0;
        utterance.pitch = audio.tts_config.pitch || 1.0;
      }

      utterance.onstart = () => console.log('🔊 Audio narration started');
      utterance.onend = () => console.log('🔇 Audio narration ended');
      utterance.onerror = (e) => console.error('Audio error:', e);

      window.speechSynthesis.cancel(); // Cancel any ongoing speech
      window.speechSynthesis.speak(utterance);
    } else {
      console.warn('Text-to-Speech not supported in this browser');
    }
  };

  // Start playing scenes
  useEffect(() => {
    if (autoPlay && scenes && scenes.length > 0 && !isPlaying) {
      playScene(currentSceneIndex);
    }
  }, [currentSceneIndex, autoPlay, scenes, isPlaying, playScene]);

  // Icon rendering function - maps icon names to SVG shapes
  const renderIcon = (shape, commonProps) => {
    const iconName = (shape.name || shape.icon || '').toLowerCase();
    const size = shape.size || 60;
    const color = shape.color || shape.fill || '#333333';
    
    // Icon library - SVG paths for common icons
    const iconPaths = {
      'sun': 'M50,20 C35,20 20,35 20,50 C20,65 35,80 50,80 C65,80 80,65 80,50 C80,35 65,20 50,20 M50,0 L50,15 M50,85 L50,100 M0,50 L15,50 M85,50 L100,50 M15,15 L25,25 M75,25 L85,15 M15,85 L25,75 M75,75 L85,85',
      'leaf': 'M50,10 Q30,30 30,60 Q30,90 50,95 Q70,90 70,60 Q70,30 50,10',
      'battery': 'M20,30 L80,30 L80,70 L20,70 Z M35,20 L45,20 L45,30 M55,20 L65,20 L65,30',
      'molecule': 'M50,50 m-40,0 a40,40 0 1,0 80,0 a40,40 0 1,0 -80,0 M30,30 m-10,0 a10,10 0 1,0 20,0 a10,10 0 1,0 -20,0 M70,70 m-10,0 a10,10 0 1,0 20,0 a10,10 0 1,0 -20,0',
      'atom': 'M50,50 m-5,0 a5,5 0 1,0 10,0 a5,5 0 1,0 -10,0 M50,50 Q20,30 50,10 Q80,30 50,50 M50,50 Q20,70 50,90 Q80,70 50,50',
      'beaker': 'M30,20 L30,60 Q30,80 50,80 Q70,80 70,60 L70,20 Z M25,20 L75,20',
      'lightbulb': 'M50,20 Q30,25 30,45 Q30,60 50,70 Q70,60 70,45 Q70,25 50,20 M45,70 L55,70 L55,85 L45,85 Z',
      'cpu': 'M30,30 L70,30 L70,70 L30,70 Z M20,35 L30,35 M20,45 L30,45 M20,55 L30,55 M20,65 L30,65 M70,35 L80,35 M70,45 L80,45 M70,55 L80,55 M70,65 L80,65',
      'heart': 'M50,80 Q30,60 30,40 Q30,20 50,30 Q70,20 70,40 Q70,60 50,80',
      'tree': 'M45,30 L45,80 L55,80 L55,30 M50,10 Q30,20 30,35 Q30,45 50,40 Q70,45 70,35 Q70,20 50,10',
      'cloud': 'M30,50 Q20,40 30,30 Q40,20 50,30 Q60,20 70,30 Q80,40 70,50 Z',
      'water-droplet': 'M50,10 Q30,40 30,60 Q30,80 50,90 Q70,80 70,60 Q70,40 50,10',
      'lightning': 'M60,10 L40,50 L55,50 L35,90 L65,45 L50,45 Z',
      'flask': 'M40,10 L40,30 L30,60 Q30,80 50,85 Q70,80 70,60 L60,30 L60,10 Z M35,10 L65,10'
    };
    
    const pathData = iconPaths[iconName] || iconPaths['lightbulb'];
    
    return (
      <Group {...commonProps}>
        <Path
          data={pathData}
          scaleX={size / 100}
          scaleY={size / 100}
          offsetX={50}
          offsetY={50}
          fill={color}
          stroke={shape.stroke || color}
          strokeWidth={shape.strokeWidth || 2}
        />
      </Group>
    );
  };

  // Render shape based on type
  const renderShape = (shape, index) => {
    // Separate key from other common props to avoid React warning
    const shapeKey = `shape-${index}`;
    const commonProps = {
      x: shape.x || 0,
      y: shape.y || 0,
      rotation: shape.rotation || 0,
      opacity: shape.opacity !== undefined ? shape.opacity : 1,
      shadowBlur: 0,
      shadowColor: 'transparent'
    };

    switch (shape.type) {
      case 'circle':
        // Ensure lineDash is a proper array if present
        const circleProps = {
          ...commonProps,
          radius: shape.radius || 50,
          fill: shape.fill || 'transparent',
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          circleProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          circleProps.dash = shape.dash;
        }
        
        return <Circle key={shapeKey} {...circleProps} />;

      case 'rectangle':
        // Ensure lineDash is a proper array if present
        const rectProps = {
          ...commonProps,
          width: shape.width || 100,
          height: shape.height || 100,
          fill: shape.fill || 'transparent',
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2,
          cornerRadius: shape.cornerRadius || 0
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          rectProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          rectProps.dash = shape.dash;
        }
        
        return <Rect key={shapeKey} {...rectProps} />;

      case 'line':
        // Ensure lineDash is a proper array if present
        const lineProps = {
          ...commonProps,
          points: shape.points || [0, 0, 100, 100],
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2,
          lineCap: 'round',
          lineJoin: 'round'
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          lineProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          lineProps.dash = shape.dash;
        }
        
        return <Line key={shapeKey} {...lineProps} />;

      case 'arrow':
        // Build arrow props without undefined values
        const arrowProps = {
          ...commonProps,
          points: shape.points || [0, 0, 100, 100],
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2,
          pointerLength: shape.pointerLength || 10,
          pointerWidth: shape.pointerWidth || 10,
          fill: shape.stroke || '#000000',
          lineCap: 'round',
          lineJoin: 'round'
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          arrowProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          arrowProps.dash = shape.dash;
        }
        // Never pass undefined or invalid dash values
        
        return <Arrow key={shapeKey} {...arrowProps} />;

      case 'text':
        return (
          <Text
            key={shapeKey}
            {...commonProps}
            text={shape.text || shape.label || ''}
            fontSize={shape.fontSize || 16}
            fontFamily={shape.fontFamily || 'Arial'}
            fill={shape.fill || '#000000'}
            align={shape.align || 'left'}
            verticalAlign={shape.verticalAlign || 'top'}
          />
        );

      case 'image':
        // Enhanced image loading with fallback and error handling
        if (loadedImages[shape.src]) {
          return (
            <KonvaImage
              key={shapeKey}
              {...commonProps}
              image={loadedImages[shape.src]}
              width={shape.width || 150}
              height={shape.height || 150}
            />
          );
        }
        // Loading placeholder
        return (
          <Group key={shapeKey} {...commonProps}>
            <Rect
              x={-((shape.width || 150) / 2)}
              y={-((shape.height || 150) / 2)}
              width={shape.width || 150}
              height={shape.height || 150}
              fill="#F5F5F5"
              stroke="#CCCCCC"
              strokeWidth={2}
              cornerRadius={5}
            />
            <Text
              x={-((shape.width || 150) / 2)}
              y={-10}
              width={shape.width || 150}
              text="Loading..."
              fontSize={14}
              fill="#999999"
              align="center"
            />
          </Group>
        );

      case 'icon':
        // Render icons using SVG paths or simple shapes
        return renderIcon(shape, { ...commonProps, key: shapeKey });

      case 'polygon':
        const polygonProps = {
          key: shapeKey,
          ...commonProps,
          points: shape.points || [],
          closed: true,
          fill: shape.fill || 'transparent',
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2,
          lineCap: 'round',
          lineJoin: 'round'
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          polygonProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          polygonProps.dash = shape.dash;
        }
        
        return <Line {...polygonProps} />;

      case 'path':
        // SVG path rendering with Konva Path component
        const pathProps = {
          key: shapeKey,
          ...commonProps,
          data: shape.d || shape.data || '',
          fill: shape.fill || 'none',
          stroke: shape.stroke || '#000000',
          strokeWidth: shape.strokeWidth || 2,
          lineCap: 'round',
          lineJoin: 'round'
        };
        
        // CRITICAL: Only add dash if it's a valid array with numeric values
        if (shape.lineDash && Array.isArray(shape.lineDash) && shape.lineDash.length > 0 && shape.lineDash.every(v => typeof v === 'number')) {
          pathProps.dash = shape.lineDash;
        } else if (shape.dash && Array.isArray(shape.dash) && shape.dash.length > 0 && shape.dash.every(v => typeof v === 'number')) {
          pathProps.dash = shape.dash;
        }
        
        return <Path {...pathProps} />;

      default:
        console.warn(`Unknown shape type: ${shape.type}`);
        return null;
    }
  };

  // Controls
  const handleNext = () => {
    if (currentSceneIndex < scenes.length - 1) {
      setCurrentSceneIndex(currentSceneIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentSceneIndex > 0) {
      setCurrentSceneIndex(currentSceneIndex - 1);
    }
  };

  const handleReset = () => {
    setCurrentSceneIndex(0);
    setIsPlaying(false);
  };

  if (!scenes || scenes.length === 0) {
    return (
      <div style={{ width: '100%', height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
        <p>No visualization scenes available</p>
      </div>
    );
  }

  const currentScene = scenes[currentSceneIndex];

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      {/* Canvas */}
      <div style={{ 
        width: '100%', 
        maxWidth: '1920px', 
        margin: '0 auto',
        border: '2px solid #ddd',
        borderRadius: '8px',
        overflow: 'hidden',
        background: currentScene?.effects?.background || 'white'
      }}>
        <Stage
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          ref={stageRef}
          style={{ width: '100%', height: 'auto' }}
        >
          <Layer ref={layerRef}>
            {renderedShapes.map((shape, index) => renderShape(shape, index))}
          </Layer>
        </Stage>
      </div>

      {/* Controls */}
      <div style={{
        marginTop: '20px',
        display: 'flex',
        gap: '10px',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <button
          onClick={handlePrevious}
          disabled={currentSceneIndex === 0}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            cursor: currentSceneIndex === 0 ? 'not-allowed' : 'pointer',
            opacity: currentSceneIndex === 0 ? 0.5 : 1
          }}
        >
          ⏮️ Previous
        </button>

        <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
          Scene {currentSceneIndex + 1} / {scenes.length}
          {currentScene?.title && ` - ${currentScene.title}`}
        </span>

        <button
          onClick={handleNext}
          disabled={currentSceneIndex === scenes.length - 1}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            cursor: currentSceneIndex === scenes.length - 1 ? 'not-allowed' : 'pointer',
            opacity: currentSceneIndex === scenes.length - 1 ? 0.5 : 1
          }}
        >
          Next ⏭️
        </button>

        <button
          onClick={handleReset}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          🔄 Reset
        </button>
      </div>

      {/* Scene Info */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        background: '#f9f9f9',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>{currentScene?.title || 'Scene'}</h3>
        <p style={{ margin: 0, color: '#666' }}>
          Duration: {currentScene?.duration}s | 
          Shapes: {currentScene?.shapes?.length || 0} | 
          Animations: {currentScene?.animations?.length || 0}
        </p>
        {currentScene?.audio?.text && (
          <p style={{ marginTop: '10px', fontStyle: 'italic', color: '#444' }}>
            🔊 "{currentScene.audio.text}"
          </p>
        )}
      </div>
    </div>
  );
};

export default KonvaTeachingBoard;
