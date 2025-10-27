import React, { useRef, useEffect, useState } from 'react';
import { Stage, Layer, Text, Rect, Circle, Arrow, Line, Image as KonvaImage } from 'react-konva';
import useImage from 'use-image';

/**
 * WhiteboardImage Component
 * Renders images from base64 data
 */
function WhiteboardImage({ imageData, x, y, scale = 1.0 }) {
    const [image] = useImage(imageData?.base64_data || '');
    
    if (!image) return null;
    
    return (
        <KonvaImage
            image={image}
            x={x}
            y={y}
            scaleX={scale}
            scaleY={scale}
        />
    );
}

/**
 * TeachingCanvas Component
 * Renders whiteboard commands using Konva.js
 * 
 * Props:
 * - teachingData: Object with teaching_sequence and images
 * - currentStepIndex: Current step being displayed
 * - containerWidth: Canvas width
 * - containerHeight: Canvas height
 */
export default function TeachingCanvas({ 
    teachingData, 
    currentStepIndex, 
    containerWidth = 800, 
    containerHeight = 600 
}) {
    const [elements, setElements] = useState([]);
    const [nextId, setNextId] = useState(0);
    const layerRef = useRef();
    
    useEffect(() => {
        if (!teachingData || currentStepIndex < 0) return;
        
        const currentStep = teachingData.teaching_sequence[currentStepIndex];
        if (!currentStep) return;
        
        executeWhiteboardCommands(currentStep.whiteboard_commands);
    }, [currentStepIndex, teachingData]);
    
    const executeWhiteboardCommands = (commands) => {
        if (!commands || commands.length === 0) return;
        
        const newElements = [];
        let idCounter = nextId;
        const W = containerWidth;
        const H = containerHeight;
        
        for (const cmd of commands) {
            // Clear all elements
            if (cmd.action === "clear_all") {
                setElements([]);
                setNextId(0);
                return;
            }
            
            // Write text
            else if (cmd.action === "write_text") {
                const x = (cmd.x_percent / 100) * W;
                const y = (cmd.y_percent / 100) * H;
                const textWidth = (cmd.text.length * (cmd.font_size || 20)) / 2;
                
                newElements.push(
                    <Text
                        key={`text_${idCounter++}`}
                        text={cmd.text}
                        x={cmd.align === 'center' ? x - textWidth / 2 : cmd.align === 'right' ? x - textWidth : x}
                        y={y - (cmd.font_size || 20) / 2}
                        fontSize={cmd.font_size || 20}
                        fill={cmd.color || 'black'}
                        fontFamily="Segoe UI, Arial, sans-serif"
                    />
                );
            }
            
            // Draw text box
            else if (cmd.action === "draw_text_box") {
                const boxWidth = (cmd.width_percent / 100) * W;
                const boxHeight = cmd.height || 60;
                const x = (cmd.x_percent / 100) * W - boxWidth / 2;
                const y = (cmd.y_percent / 100) * H - boxHeight / 2;
                
                newElements.push(
                    <Rect
                        key={`rect_${idCounter++}`}
                        x={x}
                        y={y}
                        width={boxWidth}
                        height={boxHeight}
                        fill={cmd.color || '#f0f0f0'}
                        stroke={cmd.stroke || '#000'}
                        strokeWidth={2}
                        cornerRadius={8}
                    />
                );
                
                newElements.push(
                    <Text
                        key={`boxtext_${idCounter++}`}
                        text={cmd.text}
                        x={x}
                        y={y}
                        width={boxWidth}
                        height={boxHeight}
                        fontSize={20}
                        fill="#1f2937"
                        align="center"
                        verticalAlign="middle"
                        fontFamily="Segoe UI, Arial, sans-serif"
                    />
                );
            }
            
            // Draw circle
            else if (cmd.action === "draw_circle") {
                const x = (cmd.x_percent / 100) * W;
                const y = (cmd.y_percent / 100) * H;
                
                newElements.push(
                    <Circle
                        key={`circle_${idCounter++}`}
                        x={x}
                        y={y}
                        radius={cmd.radius || 30}
                        fill={cmd.fill || 'transparent'}
                        stroke={cmd.stroke || '#000'}
                        strokeWidth={cmd.stroke_width || 2}
                    />
                );
            }
            
            // Draw rectangle
            else if (cmd.action === "draw_rectangle") {
                const width = cmd.width_percent ? (cmd.width_percent / 100) * W : 100;
                const height = cmd.height || 60;
                const x = (cmd.x_percent / 100) * W - width / 2;
                const y = (cmd.y_percent / 100) * H - height / 2;
                
                newElements.push(
                    <Rect
                        key={`rect2_${idCounter++}`}
                        x={x}
                        y={y}
                        width={width}
                        height={height}
                        fill={cmd.fill || 'transparent'}
                        stroke={cmd.stroke || '#000'}
                        strokeWidth={cmd.stroke_width || 2}
                    />
                );
            }
            
            // Draw arrow
            else if (cmd.action === "draw_arrow") {
                const [fromX, fromY] = cmd.from_percent;
                const [toX, toY] = cmd.to_percent;
                
                newElements.push(
                    <Arrow
                        key={`arrow_${idCounter++}`}
                        points={[
                            (fromX / 100) * W,
                            (fromY / 100) * H,
                            (toX / 100) * W,
                            (toY / 100) * H
                        ]}
                        stroke={cmd.color || '#000'}
                        fill={cmd.color || '#000'}
                        strokeWidth={cmd.thickness || 2}
                        pointerLength={10}
                        pointerWidth={10}
                    />
                );
            }
            
            // Draw line
            else if (cmd.action === "draw_line") {
                const points = [];
                for (const [px, py] of cmd.points_percent) {
                    points.push((px / 100) * W);
                    points.push((py / 100) * H);
                }
                
                newElements.push(
                    <Line
                        key={`line_${idCounter++}`}
                        points={points}
                        stroke={cmd.stroke || '#000'}
                        strokeWidth={cmd.stroke_width || 2}
                    />
                );
            }
            
            // Draw image
            else if (cmd.action === "draw_image") {
                const imageData = teachingData?.images?.find(img => img.id === cmd.image_id);
                if (imageData) {
                    const x = (cmd.x_percent / 100) * W;
                    const y = (cmd.y_percent / 100) * H;
                    
                    newElements.push(
                        <WhiteboardImage
                            key={`img_${idCounter++}`}
                            imageData={imageData}
                            x={x}
                            y={y}
                            scale={cmd.scale || 1.0}
                        />
                    );
                }
            }
            
            // Draw equation (placeholder - would need KaTeX or similar)
            else if (cmd.action === "draw_equation") {
                const x = (cmd.x_percent / 100) * W;
                const y = (cmd.y_percent / 100) * H;
                
                newElements.push(
                    <Text
                        key={`equation_${idCounter++}`}
                        text={cmd.latex} // For now, show as text (could integrate KaTeX later)
                        x={x - 100}
                        y={y}
                        fontSize={cmd.font_size || 24}
                        fill="#1f2937"
                        fontFamily="Courier New, monospace"
                        align="center"
                    />
                );
            }
            
            // Highlight object (would need animation - simplified for now)
            else if (cmd.action === "highlight_object") {
                // Note: Full implementation would use Konva animations
                // This is a placeholder
                console.log(`Highlight: ${cmd.target_text || cmd.target_id}`);
            }
        }
        
        setElements(prev => [...prev, ...newElements]);
        setNextId(idCounter);
    };
    
    return (
        <Stage width={containerWidth} height={containerHeight}>
            <Layer ref={layerRef}>
                {elements}
            </Layer>
        </Stage>
    );
}
