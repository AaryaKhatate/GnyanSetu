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
    },
    ref
  ) => {
    const [drawnElements, setDrawnElements] = useState([]);
    const [currentElementIndex, setCurrentElementIndex] = useState(0);
    const [nextTextY, setNextTextY] = useState(60); // Track next available Y position for text
    const [nextShapeY, setNextShapeY] = useState(80); // Track next available Y position for shapes
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
        }
      },
      clearCanvas: () => {
        setDrawnElements([]);
        setCurrentElementIndex(0);
        setNextTextY(60);
        setNextShapeY(80);
      },
    }));

    // Clear canvas when new step starts
    useEffect(() => {
      if (teachingStep && teachingStep.step !== undefined) {
        // Force clear canvas and reset state for new step
        setDrawnElements([]);
        setCurrentElementIndex(0);
        // Reset position trackers
        setNextTextY(60);
        setNextShapeY(80);

        // Clear any pending animations
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }

        // If using Konva, you may also want to clear the Layer manually (if needed)
        if (stageRef.current) {
          const layer = stageRef.current.getLayers()[0];
          if (layer) {
            layer.removeChildren();
            layer.draw();
          }
        }
      }
    }, [teachingStep?.step]);

    // Start drawing animation when playing
    useEffect(() => {
      if (isPlaying && teachingStep && teachingStep.drawing_commands) {
        startDrawingAnimation();
      } else {
        // Stop animation if not playing
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
      let commandIndex = 0;

      const executeNextCommand = () => {
        if (commandIndex >= commands.length) {
          // All commands executed
          if (onStepComplete) {
            onStepComplete();
          }
          return;
        }

        const command = commands[commandIndex];
        const delay = command.time || commandIndex * 1000; // Default 1 second between commands

        animationTimeoutRef.current = setTimeout(() => {
          const element = createElementFromCommand(command, commandIndex);
          if (element) {
            setDrawnElements((prev) => {
              const newElements = [...prev, element];

              // Update position trackers based on element type
              if (element.type === "text") {
                const textHeight = (element.fontSize || 18) + 20; // fontSize + padding
                const lines = Math.ceil(element.text.length / 50); // Estimate lines
                setNextTextY((prev) => prev + textHeight * lines + 10);
              } else if (element.type === "rect" || element.type === "circle") {
                const elementHeight =
                  element.type === "rect" ? element.height : element.radius * 2;
                setNextShapeY((prev) => prev + elementHeight + 30);
              }

              return newElements;
            });
            setCurrentElementIndex(commandIndex + 1);
          }
          commandIndex++;
          executeNextCommand();
        }, delay);
      };

      executeNextCommand();
    }, [teachingStep, onStepComplete]);

    const createElementFromCommand = (command, index) => {
      const baseProps = {
        id: `element-${index}`,
        key: `element-${index}`,
      };

      // Use current position trackers to prevent overlapping
      const getNextPosition = (elementType) => {
        const margin = 30;

        switch (elementType) {
          case "text":
            return {
              x: margin,
              y: nextTextY,
            };

          case "shape":
            return {
              x: canvasWidth - 250,
              y: nextShapeY,
            };

          default:
            return {
              x: margin,
              y: nextTextY,
            };
        }
      };

      switch (command.action) {
        case "draw_text":
          const textPos = getNextPosition("text");
          const fontSize = command.fontSize || 18;

          return {
            ...baseProps,
            type: "text",
            x: textPos.x,
            y: textPos.y,
            text: command.text || "",
            fontSize: fontSize,
            fontFamily: command.fontFamily || "Arial",
            fontStyle: command.fontStyle || "normal",
            fill: command.color || "#000000",
            width: canvasWidth - textPos.x - 280, // Leave space for shapes on right
          };

        case "draw_rectangle":
          const rectPos = getNextPosition("shape");
          return {
            ...baseProps,
            type: "rect",
            x: rectPos.x,
            y: rectPos.y,
            width: Math.min(command.width || 150, 200),
            height: Math.min(command.height || 80, 100),
            fill: command.fill || "transparent",
            stroke: command.color || "#0066cc",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_circle":
          const circlePos = getNextPosition("shape");
          return {
            ...baseProps,
            type: "circle",
            x: circlePos.x + 50, // Offset for circle center
            y: circlePos.y + 50,
            radius: Math.min(command.radius || 40, 50),
            fill: command.fill || "transparent",
            stroke: command.color || "#0066cc",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_arrow":
          // Arrows use fixed safe positions to avoid overlap
          const arrowStartY = Math.max(nextTextY + 30, nextShapeY + 30);
          let points;
          if (command.points && Array.isArray(command.points)) {
            points = command.points;
          } else {
            // Default arrow pointing from text area to shape area
            points = [300, arrowStartY, 500, arrowStartY];
          }

          // Update position tracker for arrows
          setNextTextY((prev) => Math.max(prev, arrowStartY + 50));
          setNextShapeY((prev) => Math.max(prev, arrowStartY + 50));

          return {
            ...baseProps,
            type: "arrow",
            points: points,
            pointerLength: command.pointerLength || 10,
            pointerWidth: command.pointerWidth || 10,
            fill: command.color || "#059669",
            stroke: command.color || "#059669",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_line":
          const lineY = Math.max(nextTextY + 20, nextShapeY + 20);
          setNextTextY((prev) => Math.max(prev, lineY + 30));
          setNextShapeY((prev) => Math.max(prev, lineY + 30));

          return {
            ...baseProps,
            type: "line",
            points: command.points || [30, lineY, canvasWidth - 30, lineY],
            stroke: command.color || "#000000",
            strokeWidth: command.strokeWidth || 2,
            lineCap: "round",
            lineJoin: "round",
          };

        case "highlight":
          // Highlight goes behind the most recent text
          const highlightY = Math.max(nextTextY - 40, 60);
          return {
            ...baseProps,
            type: "rect",
            x: 25,
            y: highlightY - 5,
            width: canvasWidth - 310,
            height: 35,
            fill: "yellow",
            opacity: 0.3,
            stroke: "orange",
            strokeWidth: 1,
          };

        default:
          console.warn("Unknown drawing command:", command.action);
          return null;
      }
    };

    const renderElement = (element) => {
      const commonProps = {
        key: element.id,
        id: element.id,
      };

      switch (element.type) {
        case "text":
          return (
            <Text
              {...commonProps}
              x={element.x}
              y={element.y}
              text={element.text}
              fontSize={element.fontSize}
              fontFamily={element.fontFamily}
              fill={element.fill}
              fontStyle={element.fontStyle}
              width={element.width}
              align="left"
              verticalAlign="top"
              wrap="word"
            />
          );

        case "rect":
          return (
            <Rect
              {...commonProps}
              x={element.x}
              y={element.y}
              width={element.width}
              height={element.height}
              fill={element.fill}
              stroke={element.stroke}
              strokeWidth={element.strokeWidth}
              opacity={element.opacity}
            />
          );

        case "circle":
          return (
            <Circle
              {...commonProps}
              x={element.x}
              y={element.y}
              radius={element.radius}
              fill={element.fill}
              stroke={element.stroke}
              strokeWidth={element.strokeWidth}
            />
          );

        case "arrow":
          return (
            <Arrow
              {...commonProps}
              points={element.points}
              pointerLength={element.pointerLength}
              pointerWidth={element.pointerWidth}
              fill={element.fill}
              stroke={element.stroke}
              strokeWidth={element.strokeWidth}
            />
          );

        case "line":
          return (
            <Line
              {...commonProps}
              points={element.points}
              stroke={element.stroke}
              strokeWidth={element.strokeWidth}
              lineCap={element.lineCap}
              lineJoin={element.lineJoin}
            />
          );

        default:
          return null;
      }
    };

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="relative bg-white rounded-lg shadow-lg border border-gray-200"
        style={{ width: canvasWidth, height: canvasHeight }}
      >
        {/* Canvas Header */}
        <div className="absolute top-2 left-2 z-10 bg-black/70 text-white px-3 py-1 rounded text-sm">
          {teachingStep ? `Step ${teachingStep.step}` : "Ready"}
          {drawnElements.length > 0 && (
            <span className="ml-2 text-green-300">
              Drawing... ({drawnElements.length}/
              {teachingStep?.drawing_commands?.length || 0})
            </span>
          )}
        </div>

        {/* Konva Stage */}
        <Stage
          width={canvasWidth}
          height={canvasHeight}
          ref={stageRef}
          className="rounded-lg"
        >
          <Layer>
            {/* Render all drawn elements */}
            {drawnElements.map((element) => renderElement(element))}
          </Layer>
        </Stage>

        {/* Controls overlay */}
        <div className="absolute bottom-2 right-2 flex gap-2">
          <button
            onClick={() => {
              // Clear canvas
              setDrawnElements([]);
              setCurrentElementIndex(0);
            }}
            className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm"
            title="Clear canvas"
          >
            Clear
          </button>

          <button
            onClick={() => {
              // Download canvas as image
              const uri = stageRef.current.toDataURL();
              const link = document.createElement("a");
              link.download = `step-${teachingStep?.step || "canvas"}.png`;
              link.href = uri;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            }}
            className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm"
            title="Download as image"
          >
            💾
          </button>
        </div>
      </motion.div>
    );
  }
);

TeachingCanvas.displayName = "TeachingCanvas";

export default TeachingCanvas;
