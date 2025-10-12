import React, { useCallback, useRef, useState } from "react";

export default function UploadBox({ onStartSession }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef(null);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  }, []);

  const onChange = useCallback((e) => {
    const file = e.target.files?.[0];
    handleFile(file);
  }, []);

  const handleFile = (file) => {
    if (!file) return;
    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");
    const isUnder50mb = file.size <= 50 * 1024 * 1024;
    if (!isPdf) {
      alert("Please upload a PDF file.");
      return;
    }
    if (!isUnder50mb) {
      alert("File size should be 50MB or less.");
      return;
    }
    setSelectedFile(file);
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      setIsLoading(true);
      try {
        console.log("📤 Starting PDF upload...", selectedFile);

        // Get user ID from session storage (set during login)
        const userId =
          sessionStorage.getItem("userId") ||
          sessionStorage.getItem("studentId") ||
          localStorage.getItem("userId") ||
          localStorage.getItem("studentId");

        console.log("🔍 Checking for userId in storage...");
        console.log(
          "- sessionStorage.userId:",
          sessionStorage.getItem("userId")
        );
        console.log("- localStorage.userId:", localStorage.getItem("userId"));

        if (!userId) {
          console.error("❌ No user ID found in storage!");
          console.log("📦 All localStorage keys:", Object.keys(localStorage));
          console.log(
            "📦 All sessionStorage keys:",
            Object.keys(sessionStorage)
          );
          alert(
            "Please login first to upload a PDF.\n\nDebug info:\n- localStorage.userId: " +
              localStorage.getItem("userId") +
              "\n- sessionStorage.userId: " +
              sessionStorage.getItem("userId")
          );
          return;
        }

        console.log("✅ User ID found:", userId);

        // Upload PDF to Django backend
        const formData = new FormData();
        formData.append("pdf_file", selectedFile);
        formData.append("user_id", userId); // Use actual user ID
        formData.append("lesson_type", "interactive");

        console.log("Sending request to backend...");
        console.log("URL:", "http://localhost:8000/api/generate-lesson/");
        console.log("User ID:", userId);
        console.log("File:", selectedFile.name);

        const response = await fetch(
          "http://localhost:8000/api/generate-lesson/",
          {
            method: "POST",
            body: formData,
            headers: {
              // Don't set Content-Type, let browser set it for FormData
            },
          }
        );

        console.log("Response received:", response.status, response.statusText);
        console.log("Response headers:", response.headers);

        if (!response.ok) {
          const errorText = await response.text();
          console.error("Server error:", errorText);
          throw new Error(
            `HTTP error! status: ${response.status} - ${errorText}`
          );
        }

        const result = await response.json();
        console.log("Upload result:", result);

        if (result.error) {
          alert(`Error: ${result.error}`);
          return;
        }

        console.log("PDF uploaded successfully:", result);
        console.log("PDF text length:", result.text?.length);
        console.log(
          "PDF text preview:",
          result.text?.substring(0, 200) + "..."
        );
        console.log("Lesson data:", result.lesson);
        console.log("Lesson ID:", result.lesson_id);

        // ✅ CRITICAL FIX: Store lesson_id for Quiz and Notes components
        if (result.lesson_id) {
          sessionStorage.setItem("lessonId", result.lesson_id);
          sessionStorage.setItem("conversationId", result.lesson_id); // Also set as conversationId for compatibility
          console.log("✅ Lesson ID stored:", result.lesson_id);
        } else {
          console.warn("⚠️ No lesson_id in response!");
        }

        // Store PDF text, filename AND lesson data for WebSocket communication
        sessionStorage.setItem("pdfText", result.text || "");
        sessionStorage.setItem(
          "pdfFilename",
          result.filename || selectedFile.name
        );

        // Store the complete lesson data from Lesson Service
        if (result.lesson) {
          sessionStorage.setItem("lessonData", JSON.stringify(result.lesson));
          console.log(
            "✅ Lesson data stored:",
            result.lesson.teaching_steps?.length,
            "steps"
          );
        } else {
          console.warn("⚠️ No lesson data in response!");
        }

        // Verify storage
        console.log(
          "Stored in sessionStorage - lessonId:",
          sessionStorage.getItem("lessonId")
        );
        console.log(
          "Stored in sessionStorage - pdfText length:",
          sessionStorage.getItem("pdfText")?.length
        );
        console.log(
          "Stored in sessionStorage - pdfFilename:",
          sessionStorage.getItem("pdfFilename")
        );
        console.log(
          "Stored in sessionStorage - lessonData:",
          !!sessionStorage.getItem("lessonData")
        );

        // Start the session flow
        onStartSession(result.filename || selectedFile.name);
      } catch (error) {
        console.error("Error uploading PDF:", error);
        alert(`Failed to upload PDF: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black bg-opacity-60 rounded-2xl">
          <div className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mb-4"></div>
          <span className="text-white text-lg font-semibold">
            Processing PDF and preparing lesson...
          </span>
        </div>
      )}
      {!selectedFile ? (
        <div
          className={`spotlight relative mx-auto max-w-3xl rounded-2xl border-2 border-dashed px-6 py-14 sm:py-16 md:py-20 transition-all duration-300 ${
            isDragging
              ? "border-indigo-400/80 bg-indigo-950/30 shadow-glow"
              : "border-slate-600/40 bg-slate-900/40 hover:border-indigo-400/50 hover:bg-slate-900/60 hover:shadow-glow2"
          }`}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            e.currentTarget.style.setProperty(
              "--x",
              `${e.clientX - rect.left}px`
            );
            e.currentTarget.style.setProperty(
              "--y",
              `${e.clientY - rect.top}px`
            );
          }}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          <div className="flex flex-col items-center text-center">
            <div
              className={`mb-4 h-14 w-14 rounded-full flex items-center justify-center bg-indigo-500/10 text-indigo-300 ${
                isDragging ? "animate-float" : ""
              }`}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 16v-8M8 12l4-4 4 4"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M20 16.5a3.5 3.5 0 01-3.5 3.5h-9A3.5 3.5 0 014 16.5c0-1.7 1.2-3.1 2.8-3.4.3-2.7 2.6-4.8 5.2-4.8 2.6 0 4.9 2.1 5.2 4.8 1.6.3 2.8 1.7 2.8 3.4z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-medium text-white">
              Drag & Drop your PDF here
            </h3>
            <p className="mt-2 text-sm text-slate-400">or</p>

            <div className="mt-4">
              <button
                onClick={() => inputRef.current?.click()}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-glow transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-indigo-400/50"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="opacity-90"
                >
                  <path
                    d="M12 5v14M5 12h14"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
                Select PDF
              </button>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="hidden"
                onChange={onChange}
              />
            </div>

            <p className="mt-3 text-xs text-slate-500">
              Supported: PDF up to 50MB
            </p>
          </div>
        </div>
      ) : (
        <div className="mx-auto max-w-3xl">
          <div className="rounded-2xl border border-slate-600/40 bg-slate-900/40 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white">Selected PDF</h3>
              <button
                onClick={removeFile}
                className="text-slate-400 hover:text-rose-400 p-2 rounded-lg hover:bg-slate-800/60 transition-colors"
                title="Remove file"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M6 18L18 6M6 6l12 12"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-lg border border-slate-600/30 bg-slate-800/30">
              <div className="h-12 w-12 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="text-indigo-400"
                >
                  <path
                    d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M14 2v6h6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M16 13H8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M16 17H8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M10 9H8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-slate-400">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-center">
              <button
                onClick={handleUpload}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-3 text-sm font-medium text-white shadow-glow transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-green-400/50"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M7 10l5 5 5-5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M12 15V3"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Upload PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
