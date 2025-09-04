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
    const stageRef = useRef();
    const animationTimeoutRef = useRef();

    // Expose methods to parent component
    useImperativeHandle(ref, () => ({
      addDrawingCommand: (command) => {
        const element = createElementFromCommand(command);
        if (element) {
          setDrawnElements((prev) => [...prev, element]);
        }
      },
      clearCanvas: () => {
        setDrawnElements([]);
        setCurrentElementIndex(0);
      },
    }));

    // Clear canvas when new step starts
    useEffect(() => {
      if (teachingStep && teachingStep.step !== undefined) {
        // Force clear canvas and reset state for new step
        setDrawnElements([]);
        setCurrentElementIndex(0);

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
          // Add the new element to drawn elements
          const element = createElementFromCommand(command, commandIndex);
          if (element) {
            setDrawnElements((prev) => [...prev, element]);
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

      switch (command.action) {
        case "draw_text":
          return {
            ...baseProps,
            type: "text",
            x: command.x || 50,
            y: command.y || 50,
            text: command.text || "",
            fontSize: command.fontSize || (command.style === "title" ? 24 : 16),
            fontFamily: command.fontFamily || "Arial",
            fontStyle:
              command.fontStyle ||
              (command.style === "title" ? "bold" : "normal"),
            fill: command.color || "#000000",
          };

        case "draw_rectangle":
          return {
            ...baseProps,
            type: "rect",
            x: command.x || 50,
            y: command.y || 50,
            width: command.width || 100,
            height: command.height || 60,
            fill: command.fill || "transparent",
            stroke: command.color || "#0066cc",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_circle":
          return {
            ...baseProps,
            type: "circle",
            x: command.x || 50,
            y: command.y || 50,
            radius: command.radius || 30,
            fill: command.fill || "transparent",
            stroke: command.color || "#0066cc",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_arrow":
          // Handle both old format (from/to) and new format (points array)
          let points;
          if (command.points && Array.isArray(command.points)) {
            points = command.points;
          } else if (command.from && command.to) {
            points = [
              command.from[0],
              command.from[1],
              command.to[0],
              command.to[1],
            ];
          } else {
            points = [50, 50, 150, 150]; // Default arrow
          }

          return {
            ...baseProps,
            type: "arrow",
            points: points,
            pointerLength: command.pointerLength || 10,
            pointerWidth: command.pointerWidth || 10,
            fill: command.color || "#ff0000",
            stroke: command.color || "#ff0000",
            strokeWidth: command.strokeWidth || 2,
          };

        case "draw_line":
          return {
            ...baseProps,
            type: "line",
            points: command.points || [50, 50, 150, 150],
            stroke: command.color || "#000000",
            strokeWidth: command.strokeWidth || 2,
            lineCap: "round",
            lineJoin: "round",
          };

        case "highlight":
          return {
            ...baseProps,
            type: "rect",
            x: command.x || 50,
            y: command.y || 50,
            width: command.width || 100,
            height: command.height || 30,
            fill: "yellow",
            opacity: 0.3,
            stroke: "orange",
            strokeWidth: 2,
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
