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

    // Process whiteboard commands when step changes
    useEffect(() => {
      if (teachingStep && teachingStep.whiteboard_commands) {
        console.log(" TeachingCanvas: Processing step");
        console.log("� Commands received:", teachingStep.whiteboard_commands.length);
        console.log("� First command:", teachingStep.whiteboard_commands[0]);
        
        // Clear canvas
        setDrawnElements([]);
        setCurrentElementIndex(0);
        setNextTextY(60);
        setNextShapeY(80);

        // Clear any pending animations
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }

        // Process all whiteboard commands for this step
        const commands = teachingStep.whiteboard_commands;
        const elements = [];
        
        commands.forEach((command, index) => {
          const element = createElementFromCommand(command, index);
          if (element) {
            elements.push(element);
          }
        });
        
        console.log(" Created elements:", elements.length);
        if (elements.length > 0) {
          console.log(" First element:", elements[0]);
        }
        
        setDrawnElements(elements);
      } else if (!teachingStep) {
        console.log(" No teachingStep provided");
        // Clear canvas if no step
        setDrawnElements([]);
      } else {
        console.log(" teachingStep has no whiteboard_commands");
        console.log("teachingStep:", teachingStep);
      }

      return () => {
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }
      };
    }, [teachingStep]);

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
      // Don't include 'key' in props object - React handles it separately
      const baseProps = {
        id: `element-${index}`,
      };

      // Convert percentage coordinates to pixels
      const percentToPixel = (percent, dimension) => {
        if (percent === null || percent === undefined) return null;
        return (percent / 100) * dimension;
      };

      switch (command.action) {
        case "clear_all":
          // Handled by clearing drawnElements
          return null;

        case "write_text":
          const x = percentToPixel(command.x_percent, canvasWidth) || canvasWidth / 2;
          const y = percentToPixel(command.y_percent, canvasHeight) || 100;
          
          // For center alignment, we need to set offsetX to center the text at the x position
          const textAlign = command.align || "center";
          const textWidth = command.width_percent ? percentToPixel(command.width_percent, canvasWidth) : canvasWidth;
          
          return {
            ...baseProps,
            type: "text",
            x: textAlign === "center" ? 0 : x,
            y: y,
            text: command.text || "",
            fontSize: command.font_size || 24,
            fill: command.color || "#000000",
            align: textAlign,
            width: textWidth,
          };

        case "draw_text_box":
          const boxX = percentToPixel(command.x_percent, canvasWidth) || canvasWidth / 2;
          const boxY = percentToPixel(command.y_percent, canvasHeight) || 100;
          const boxWidth = command.width_percent ? percentToPixel(command.width_percent, canvasWidth) : 200;
          
          return {
            ...baseProps,
            type: "text_box",
            x: boxX - boxWidth/2, // Center the box
            y: boxY,
            width: boxWidth,
            height: command.height || 50,
            text: command.text || "",
            fontSize: 18,
            fill: command.color || "#e0e7ff",
            stroke: command.stroke || "#6366f1",
            strokeWidth: 2,
            textColor: "#000000",
          };

        case "draw_equation":
          const eqX = percentToPixel(command.x_percent, canvasWidth) || canvasWidth / 2;
          const eqY = percentToPixel(command.y_percent, canvasHeight) || 100;
          
          return {
            ...baseProps,
            type: "text", // Render as text for now (LaTeX rendering would require additional library)
            x: eqX,
            y: eqY,
            text: command.latex || command.text || "",
            fontSize: command.font_size || 28,
            fill: "#000000",
            align: "center",
            fontFamily: "monospace", // Use monospace for math
          };

        case "draw_rectangle":
          const rectX = percentToPixel(command.x_percent, canvasWidth) || 100;
          const rectY = percentToPixel(command.y_percent, canvasHeight) || 100;
          
          return {
            ...baseProps,
            type: "rect",
            x: rectX,
            y: rectY,
            width: command.width || 150,
            height: command.height || 80,
            fill: command.fill || "transparent",
            stroke: command.color || command.stroke || "#0066cc",
            strokeWidth: command.stroke_width || 2,
          };

        case "draw_circle":
          const circleX = percentToPixel(command.x_percent, canvasWidth) || canvasWidth / 2;
          const circleY = percentToPixel(command.y_percent, canvasHeight) || canvasHeight / 2;
          
          return {
            ...baseProps,
            type: "circle",
            x: circleX,
            y: circleY,
            radius: command.radius || 40,
            fill: command.fill || "transparent",
            stroke: command.color || "#0066cc",
            strokeWidth: command.stroke_width || 2,
          };

        case "draw_arrow":
          // from_percent and to_percent are arrays: [x, y]
          const fromX = command.from_percent ? percentToPixel(command.from_percent[0], canvasWidth) : 100;
          const fromY = command.from_percent ? percentToPixel(command.from_percent[1], canvasHeight) : 100;
          const toX = command.to_percent ? percentToPixel(command.to_percent[0], canvasWidth) : 200;
          const toY = command.to_percent ? percentToPixel(command.to_percent[1], canvasHeight) : 100;
          
          return {
            ...baseProps,
            type: "arrow",
            points: [fromX, fromY, toX, toY],
            pointerLength: 10,
            pointerWidth: 10,
            fill: command.color || "#059669",
            stroke: command.color || "#059669",
            strokeWidth: command.thickness || 2,
          };

        case "draw_line":
          const linePoints = command.points_percent ? 
            command.points_percent.flatMap(p => [
              percentToPixel(p[0], canvasWidth),
              percentToPixel(p[1], canvasHeight)
            ]) :
            [30, 100, canvasWidth - 30, 100];
          
          return {
            ...baseProps,
            type: "line",
            points: linePoints,
            stroke: command.color || "#000000",
            strokeWidth: command.stroke_width || command.thickness || 2,
            lineCap: "round",
            lineJoin: "round",
          };

        default:
          console.warn("Unknown whiteboard command:", command.action);
          return null;
      }
    };

    const renderElement = (element) => {
      // Don't spread key prop - pass it directly to each component
      switch (element.type) {
        case "text":
          return (
            <Text
              key={element.id}
              id={element.id}
              x={element.x}
              y={element.y}
              text={element.text}
              fontSize={element.fontSize}
              fontFamily={element.fontFamily || "Arial"}
              fill={element.fill}
              fontStyle={element.fontStyle}
              width={element.width}
              align={element.align || "left"}
              verticalAlign="top"
              wrap="word"
            />
          );

        case "text_box":
          return (
            <React.Fragment key={element.id}>
              <Rect
                key={`${element.id}-rect`}
                id={`${element.id}-rect`}
                x={element.x}
                y={element.y}
                width={element.width}
                height={element.height}
                fill={element.fill}
                stroke={element.stroke}
                strokeWidth={element.strokeWidth}
              />
              <Text
                key={`${element.id}-text`}
                id={`${element.id}-text`}
                x={element.x}
                y={element.y + element.height/2 - 10}
                width={element.width}
                text={element.text}
                fontSize={element.fontSize}
                fill={element.textColor}
                align="center"
              />
            </React.Fragment>
          );

        case "rect":
          return (
            <Rect
              key={element.id}
              id={element.id}
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
              key={element.id}
              id={element.id}
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
              key={element.id}
              id={element.id}
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
              key={element.id}
              id={element.id}
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
          {teachingStep ? "Active" : "Ready"}
          {drawnElements.length > 0 && (
            <span className="ml-2 text-green-300">
              {drawnElements.length} elements
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
            �
          </button>
        </div>
      </motion.div>
    );
  }
);

TeachingCanvas.displayName = "TeachingCanvas";

export default TeachingCanvas;
