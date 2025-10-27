import React from 'react';
import LessonPlayer from '../../../../../UI/src/components/LessonPlayer';

/**
 * LessonPlayer V2 Integration Component
 * 
 * This component integrates the new V2 Lesson Player with:
 * - gemini-2.0-flash-exp AI model
 * - Subject-specific visualizations
 * - Natural voice narration
 * - PowerPoint-style playback controls
 * - Loading states and progress tracking
 * - History management with delete option
 */
const LessonPlayerV2 = ({ currentUserId }) => {
  return (
    <div className="w-full h-screen bg-slate-900">
      <LessonPlayer userId={currentUserId || 'user_1'} />
    </div>
  );
};

export default LessonPlayerV2;
