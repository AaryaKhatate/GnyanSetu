import React from "react";
import { motion } from "framer-motion";
import {
  Download,
  FileText,
  Image,
  RotateCcw,
  CheckCircle,
} from "lucide-react";
import jsPDF from "jspdf";

const Notes = ({ onRetakeLesson, onEndSession, slides = [], notesContent }) => {
  // Use provided notes content or fallback to mock data
  const lessonNotes = notesContent
    ? // If notesContent is HTML, extract text content or parse it
      typeof notesContent === "string" && notesContent.includes("<")
      ? // Simple HTML to text conversion for display
        notesContent
          .replace(/<[^>]*>/g, " ")
          .split(/\s+/)
          .filter((word) => word.length > 0)
          .join(" ")
          .split(/[.!?]+/)
          .filter((sentence) => sentence.trim().length > 10)
          .map((sentence) => sentence.trim())
      : [notesContent]
    : [
        "Understanding fundamental principles is crucial for advanced learning",
        "Active engagement leads to better retention and comprehension",
        "Real-world application reinforces theoretical knowledge",
        "Regular practice and review improve long-term memory",
        "Breaking complex concepts into smaller parts aids understanding",
        "Visual and interactive learning methods enhance engagement",
        "Consistent study habits lead to better academic performance",
        "Collaborative learning can provide new perspectives and insights",
      ];

  const handleDownloadNotes = async () => {
    try {
      // Create a proper PDF using jsPDF
      const doc = new jsPDF();

      // Add title
      doc.setFontSize(20);
      doc.setFont("helvetica", "bold");
      doc.text("Lesson Summary", 20, 30);

      // Add notes
      doc.setFontSize(12);
      doc.setFont("helvetica", "normal");
      let yPosition = 50;

      lessonNotes.forEach((note, index) => {
        if (yPosition > 270) {
          doc.addPage();
          yPosition = 20;
        }
        doc.text(`• ${note}`, 20, yPosition);
        yPosition += 10;
      });

      // Save the PDF
      doc.save("lesson-notes.pdf");
    } catch (error) {
      console.error("Error downloading notes:", error);
      alert("Error downloading notes. Please try again.");
    }
  };

  const handleDownloadSlides = async () => {
    if (slides.length === 0) {
      alert("No slides available to download");
      return;
    }

    try {
      // Create a proper PDF with all slides using jsPDF
      const doc = new jsPDF();

      slides.forEach((slide, index) => {
        if (index > 0) {
          doc.addPage();
        }

        // Add slide title
        doc.setFontSize(18);
        doc.setFont("helvetica", "bold");
        doc.text(`Slide ${index + 1}: ${slide.title}`, 20, 30);

        // Add slide content
        doc.setFontSize(12);
        doc.setFont("helvetica", "normal");
        doc.text(slide.content || "No content available", 20, 50);

        // Add slide number
        doc.setFontSize(10);
        doc.text(`Page ${index + 1} of ${slides.length}`, 20, 280);
      });

      // Save the PDF
      doc.save("lesson-slides.pdf");

      // Show success message
      alert(`Downloaded ${slides.length} slides as PDF successfully!`);
    } catch (error) {
      console.error("Error downloading slides:", error);
      alert("Error downloading slides. Please try again.");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-slate-900 p-4 min-h-screen"
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            Lesson Complete! 🎉
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Great job! Here's a summary of what you've learned and resources to
            help you review.
          </p>
        </motion.div>

        {/* Notes Section */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800 rounded-2xl p-8 mb-8 border border-slate-700/40"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
              <FileText size={20} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white">Lesson Summary</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {lessonNotes.map((note, index) => (
              <motion.div
                key={index}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.1 * index }}
                className="flex items-start gap-3 p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700/70 transition-colors"
              >
                <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-slate-200 leading-relaxed">{note}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Download Options */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="grid md:grid-cols-2 gap-6 mb-8"
        >
          {/* Notes Download */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-slate-800 rounded-2xl p-6 border border-slate-700/40 hover:border-blue-500/40 transition-all duration-200 cursor-pointer"
            onClick={handleDownloadNotes}
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-500 rounded-xl flex items-center justify-center">
                <FileText size={32} className="text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-white mb-2">
                  Download Notes
                </h3>
                <p className="text-slate-300 text-sm">
                  Get a comprehensive summary of the lesson in text format
                </p>
              </div>
              <Download size={24} className="text-slate-400" />
            </div>
          </motion.div>

          {/* Slides Download */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-slate-800 rounded-2xl p-6 border border-slate-700/40 hover:border-blue-500/40 transition-all duration-200 cursor-pointer"
            onClick={handleDownloadSlides}
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-green-500 rounded-xl flex items-center justify-center">
                <Image size={32} className="text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-white mb-2">
                  Download Slides
                </h3>
                <p className="text-slate-300 text-sm">
                  Save all whiteboard slides for offline review
                </p>
              </div>
              <Download size={24} className="text-slate-400" />
            </div>
          </motion.div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <button
            onClick={onRetakeLesson}
            className="flex items-center justify-center gap-3 px-8 py-4 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors font-medium text-lg"
          >
            <RotateCcw size={20} />
            Retake Lesson
          </button>

          <button
            onClick={onEndSession}
            className="flex items-center justify-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium text-lg"
          >
            <CheckCircle size={20} />
            End Session
          </button>
        </motion.div>

        {/* Success Message */}
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.8, type: "spring" }}
          className="text-center mt-12"
        >
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-green-500/20 border border-green-500/40 rounded-full">
            <CheckCircle size={20} className="text-green-400" />
            <span className="text-green-400 font-medium">
              Session completed successfully!
            </span>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default Notes;
