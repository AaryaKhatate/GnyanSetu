import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useImperativeHandle,
  forwardRef,
} from "react";
import { Stage, Layer, Text, Rect, Circle, Arrow, Line } from "react-konva";
import { motion } from "framer-motion";

const TeachingCanvas = forwardRef(
  (
    {
      teachingStep,
      isPlaying,
      onStepComplete,
      canvasWidth = 800,
      canvasHeight = 600,
      lessonCommands = [],
      onCommandExecuted,
    },
    ref
  ) => {
    const [drawnElements, setDrawnElements] = useState([]);
    const [currentElementIndex, setCurrentElementIndex] = useState(0);
    const [nextTextY, setNextTextY] = useState(60);
    const [nextShapeY, setNextShapeY] = useState(80);
    const elementCounterRef = useRef(0);
    const stageRef = useRef();
    const animationTimeoutRef = useRef();

    // Expose methods to parent component
    useImperativeHandle(ref, () => ({
      addDrawingCommand: (command) => {
        const element = createElementFromCommand(command, drawnElements.length);
        if (element) {
          setDrawnElements((prev) => {
            const newElements = [...prev, element];

            // Update position trackers
            if (element.type === "text") {
              const textHeight = (element.fontSize || 18) + 20;
              const lines = Math.ceil(element.text.length / 50);
              setNextTextY((prev) => prev + textHeight * lines + 10);
            } else if (element.type === "rect" || element.type === "circle") {
              const elementHeight =
                element.type === "rect" ? element.height : element.radius * 2;
              setNextShapeY((prev) => prev + elementHeight + 30);
            }

            return newElements;
          });
          
          // Trigger callback if provided
          if (onCommandExecuted) {
            onCommandExecuted(command, drawnElements.length);
          }
        }
      },
      clearCanvas: () => {
        setDrawnElements([]);
        setNextTextY(60);
        setNextShapeY(80);
        setCurrentElementIndex(0);
        elementCounterRef.current = 0;
        
        // Force clear the canvas layer
        if (stageRef.current) {
          const layer = stageRef.current.getLayers()[0];
          if (layer) {
            layer.removeChildren();
            layer.batchDraw();
          }
        }
      },
      executeCommand: (command, stepIndex) => {
        // Execute individual lesson command
        console.log('Executing command on canvas:', command);
        const element = createElementFromCommand(command, stepIndex);
        if (element) {
          setDrawnElements((prev) => [...prev, element]);
        }
      }
    }));

    // Create Konva element from lesson command
    const createElementFromCommand = useCallback((command, index) => {
      if (!command) return null;

      // Use counter to ensure unique IDs
      elementCounterRef.current += 1;
      const id = `element_${elementCounterRef.current}`;
      const commonProps = {
        id,
        draggable: false,
      };

      // Handle lesson commands (write, draw) and teaching step commands  
      switch (command.type) {
        case "write":
        case "text":
          return {
            ...commonProps,
            type: "text",
            text: command.text,
            x: command.x || 50,
            y: command.y || nextTextY,
            fontSize: command.fontSize || 18,
            fontStyle: command.fontStyle || "normal",
            fill: command.fill || "#000000",
            animation: command.animation || "typewriter",
            duration: command.duration || 2000,
          };

        case "draw":
          // Handle drawing commands with shape specification
          if (command.shape === "rect") {
            return {
              ...commonProps,
              type: "rect",
              x: command.x || 100,
              y: command.y || nextShapeY,
              width: command.width || 200,
              height: command.height || 100,
              fill: command.fill || "transparent",
              stroke: command.stroke || "#333",
              strokeWidth: command.strokeWidth || 2,
              animation: command.animation || "fadeIn",
              duration: command.duration || 1000,
            };
          } else if (command.shape === "circle") {
            return {
              ...commonProps,
              type: "circle",
              x: command.x || 150,
              y: command.y || nextShapeY,
              radius: command.radius || 50,
              fill: command.fill || "transparent",
              stroke: command.stroke || "#333",
              strokeWidth: command.strokeWidth || 2,
              animation: command.animation || "scale",
              duration: command.duration || 1000,
            };
          } else if (command.shape === "line") {
            return {
              ...commonProps,
              type: "line",
              points: command.points || [0, 0, 100, 100],
              stroke: command.stroke || "#333",
              strokeWidth: command.strokeWidth || 2,
              animation: command.animation || "draw",
              duration: command.duration || 1000,
            };
          }
          break;

        case "rect":
          return {
            ...commonProps,
            type: "rect",
            x: command.x || 100,
            y: command.y || nextShapeY,
            width: command.width || 200,
            height: command.height || 100,
            fill: command.fill || "transparent",
            stroke: command.stroke || "#333",
            strokeWidth: command.strokeWidth || 2,
            animation: command.animation || "fadeIn",
            duration: command.duration || 1000,
          };

        case "circle":
          return {
            ...commonProps,
            type: "circle",
            x: command.x || 150,
            y: command.y || nextShapeY,
            radius: command.radius || 50,
            fill: command.fill || "transparent",
            stroke: command.stroke || "#333",
            strokeWidth: command.strokeWidth || 2,
            animation: command.animation || "scale",
            duration: command.duration || 1000,
          };

        case "arrow":
          return {
            ...commonProps,
            type: "arrow",
            points: command.points || [0, 0, 100, 100],
            stroke: command.stroke || "#333",
            strokeWidth: command.strokeWidth || 3,
            fill: command.fill || "#333",
            animation: command.animation || "draw",
            duration: command.duration || 1000,
          };

        case "line":
          return {
            ...commonProps,
            type: "line",
            points: command.points || [0, 0, 100, 100],
            stroke: command.stroke || "#333",
            strokeWidth: command.strokeWidth || 2,
            animation: command.animation || "draw",
            duration: command.duration || 1000,
          };

        case "speak":
          // Speech commands don't create visual elements
          return null;

        default:
          console.warn("Unknown command type:", command.type);
          return null;
      }
    }, [nextTextY, nextShapeY]);

    // Clear canvas when new step starts
    useEffect(() => {
      if (teachingStep && teachingStep.step !== undefined) {
        // Clear animation timeout
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
          animationTimeoutRef.current = null;
        }

        // Reset all state
        setDrawnElements([]);
        setCurrentElementIndex(0);
        setNextTextY(60);
        setNextShapeY(80);
        elementCounterRef.current = 0;

        // Force clear the canvas
        if (stageRef.current) {
          const layer = stageRef.current.getLayers()[0];
          if (layer) {
            layer.destroyChildren();
            layer.batchDraw();
          }
        }
      }
    }, [teachingStep?.step]);

    // Start drawing animation when playing
    useEffect(() => {
      console.log('🎨🎨 === TEACHING CANVAS USEEFFECT ===');
      console.log('🎨🎨 isPlaying:', isPlaying);
      console.log('🎨🎨 teachingStep:', teachingStep);
      console.log('🎨🎨 teachingStep.drawing_commands:', teachingStep?.drawing_commands);
      console.log('🎨🎨 drawing_commands length:', teachingStep?.drawing_commands?.length);
      
      if (isPlaying && teachingStep && teachingStep.drawing_commands) {
        console.log('✅✅ Starting drawing animation!');
        startDrawingAnimation();
      } else {
        console.log('❌❌ NOT starting drawing animation:');
        console.log('   - isPlaying:', isPlaying);
        console.log('   - has teachingStep:', !!teachingStep);
        console.log('   - has drawing_commands:', !!teachingStep?.drawing_commands);
        
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }
      }

      return () => {
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }
      };
    }, [isPlaying, teachingStep]);

    const startDrawingAnimation = useCallback(() => {
      if (!teachingStep || !teachingStep.drawing_commands) return;

      const commands = teachingStep.drawing_commands;
      let currentIndex = 0;

      const drawNextElement = () => {
        if (currentIndex >= commands.length) {
          if (onStepComplete) {
            onStepComplete();
          }
          return;
        }

        const command = commands[currentIndex];
        const element = createElementFromCommand(command, currentIndex);

        if (element) {
          setDrawnElements((prev) => [...prev, element]);
          
          // Update position trackers
          if (element.type === "text") {
            const textHeight = (element.fontSize || 18) + 20;
            const lines = Math.ceil(element.text.length / 50);
            setNextTextY((prev) => prev + textHeight * lines + 10);
          } else if (element.type === "rect" || element.type === "circle") {
            const elementHeight =
              element.type === "rect" ? element.height : element.radius * 2;
            setNextShapeY((prev) => prev + elementHeight + 30);
          }
        }

        currentIndex++;
        setCurrentElementIndex(currentIndex);

        // Schedule next element
        const delay = command.delay || 1000;
        animationTimeoutRef.current = setTimeout(drawNextElement, delay);
      };

      drawNextElement();
      
      // Cleanup on unmount
      return () => {
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
          animationTimeoutRef.current = null;
        }
      };
    }, [teachingStep, createElementFromCommand, onStepComplete]);

    // Render Konva elements
    const renderElement = (element, index) => {
      const key = element.id || `element_${index}`;

      switch (element.type) {
        case "text":
          return (
            <Text
              key={key}
              {...element}
              listening={false}
            />
          );

        case "rect":
          return (
            <Rect
              key={key}
              {...element}
              listening={false}
            />
          );

        case "circle":
          return (
            <Circle
              key={key}
              {...element}
              listening={false}
            />
          );

        case "arrow":
          return (
            <Arrow
              key={key}
              {...element}
              listening={false}
            />
          );

        case "line":
          return (
            <Line
              key={key}
              {...element}
              listening={false}
            />
          );

        default:
          return null;
      }
    };

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative w-full h-full bg-white rounded-lg shadow-lg overflow-hidden"
      >
        <Stage
          ref={stageRef}
          width={canvasWidth}
          height={canvasHeight}
          className="bg-white"
        >
          <Layer>
            {drawnElements.map((element, index) => renderElement(element, index))}
          </Layer>
        </Stage>

        {/* Progress indicator */}
        {teachingStep && teachingStep.drawing_commands && (
          <div className="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
            {currentElementIndex} / {teachingStep.drawing_commands.length}
          </div>
        )}

        {/* Lesson info */}
        {lessonCommands.length > 0 && (
          <div className="absolute top-4 left-4 bg-blue-500 bg-opacity-90 text-white px-3 py-1 rounded-full text-sm">
            Lesson: {lessonCommands.length} steps
          </div>
        )}
      </motion.div>
    );
  }
);

TeachingCanvas.displayName = "TeachingCanvas";

export default TeachingCanvas;