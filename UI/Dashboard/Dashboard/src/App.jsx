import React, { useMemo, useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import UploadBox from "./components/UploadBox";
import ProfileMenu from "./components/ProfileMenu";
import GlowingBackground from "./components/GlowingBackground";
import SessionManager from "./components/SessionManager";

// Import logo for watermark

// API Configuration
const API_BASE_URL = "http://localhost:8000";

// API Helper function
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage;
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.error || "An error occurred";
    } catch {
      errorMessage = errorText || "An error occurred";
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data;
};

// Helper function to get conversation ID
const getConversationId = (item) => {
  return item._id || item.conversation_id || item.id;
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isSessionFullscreen, setIsSessionFullscreen] = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);

  // Check for login data in URL hash (passed from landing page)
  useEffect(() => {
    console.log("� Dashboard: Checking for login data in URL...");

    const hash = window.location.hash;
    if (hash.includes("#login?")) {
      console.log(" Found login data in URL!");

      // Parse the URL parameters
      const params = new URLSearchParams(hash.split("?")[1]);

      const userId = params.get("userId");
      const userEmail = params.get("userEmail");
      const userName = params.get("userName");
      const accessToken = params.get("accessToken");
      const refreshToken = params.get("refreshToken");
      const userJson = params.get("user");

      console.log("� Storing user data in Dashboard's localStorage...");

      if (accessToken) {
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("gnyansetu_auth_token", accessToken);
        console.log(" Access token stored");
      }

      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
        console.log(" Refresh token stored");
      }

      if (userId) {
        localStorage.setItem("userId", userId);
        sessionStorage.setItem("userId", userId);
        console.log(" User ID stored:", userId);
      }

      if (userEmail) {
        localStorage.setItem("userEmail", userEmail);
        sessionStorage.setItem("userEmail", userEmail);
        console.log(" User email stored:", userEmail);
      }

      if (userName) {
        localStorage.setItem("userName", userName);
        sessionStorage.setItem("userName", userName);
        console.log(" User name stored:", userName);
      }

      if (userJson) {
        try {
          const user = JSON.parse(userJson);
          localStorage.setItem("user", JSON.stringify(user));
          localStorage.setItem("gnyansetu_user", JSON.stringify(user));
          console.log(" User object stored");
        } catch (e) {
          console.error(" Failed to parse user JSON:", e);
        }
      }

      console.log("\n� Storage Summary (Dashboard):");
      console.log("- userId:", localStorage.getItem("userId") || " Missing");
      console.log(
        "- userEmail:",
        localStorage.getItem("userEmail") || " Missing"
      );
      console.log(
        "- userName:",
        localStorage.getItem("userName") || " Missing"
      );
      console.log(
        "- access_token:",
        localStorage.getItem("access_token") ? " Stored" : " Missing"
      );

      // Clean up URL
      window.history.replaceState(null, "", "/");
      console.log(" URL cleaned up");
    } else {
      console.log("ℹ No login data in URL, checking existing storage...");
      console.log(
        "- userId:",
        localStorage.getItem("userId") ||
          sessionStorage.getItem("userId") ||
          " Not found"
      );
    }
  }, []);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get user ID from sessionStorage/localStorage on mount
  useEffect(() => {
    const storedUserId =
      sessionStorage.getItem("userId") ||
      sessionStorage.getItem("studentId") ||
      localStorage.getItem("userId") ||
      localStorage.getItem("studentId");

    if (storedUserId) {
      console.log(" User ID loaded:", storedUserId);
      setCurrentUserId(storedUserId);
    } else {
      console.warn(" No user ID found in storage. User needs to login.");
      // Optionally redirect to login
      // window.location.href = 'http://localhost:3001';
    }
  }, []);

  // Load chat history when user ID is available
  useEffect(() => {
    if (currentUserId) {
      loadChatHistory();
    }
  }, [currentUserId]);

  const loadChatHistory = async () => {
    if (!currentUserId) {
      console.warn(" Cannot load chat history: No user ID");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log(`� Loading chat history for user: ${currentUserId}`);
      const response = await apiCall(
        `/api/conversations/?user_id=${currentUserId}`
      );

      const conversations = response.conversations || [];

      // Transform backend conversations to match frontend format
      const transformedConversations = conversations.map((conv) => ({
        ...conv,
        id: getConversationId(conv), // Ensure consistent ID access
        title: conv.title || "Untitled Chat",
        timestamp:
          conv.timestamp || formatTimestamp(conv.updated_at || conv.created_at),
      }));

      setHistoryItems(transformedConversations);

      // Always start with a new chat on login/dashboard load
      handleNewChat();
    } catch (error) {
      console.error("Error loading chat history:", error);
      setError("Failed to load chat history");
      // Fallback to creating a new chat
      handleNewChat();
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (dateString) => {
    if (!dateString) {
      return new Date().toLocaleString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const messageDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate()
    );

    if (messageDate.getTime() === today.getTime()) {
      return `Today, ${date.toLocaleString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
    } else {
      return date.toLocaleDateString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
  };

  const handleNewChat = () => {
    const timestamp = new Date().toLocaleString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    // Create temporary local ID that will be replaced when conversation is created on backend
    const tempId = `temp_${Date.now()}`;

    const newItem = {
      id: tempId,
      title: "Untitled Chat",
      timestamp: `Today, ${timestamp}`,
      isTemp: true, // Mark as temporary
    };

    setHistoryItems((prev) => [newItem, ...prev]);
    setCurrentSessionId(tempId);
    setCurrentSession(null); // Reset to upload screen
  };

  const handleHistoryItemClick = (item) => {
    const itemId = getConversationId(item);
    setCurrentSessionId(itemId);

    if (item.title && item.title !== "Untitled Chat") {
      setCurrentSession(item.title);
    } else {
      setCurrentSession(null);
    }
  };

  const handleStartSession = (pdfName) => {
    // Update the current untitled chat with the PDF name
    if (currentSessionId) {
      const updatedHistory = historyItems.map((item) =>
        getConversationId(item) === currentSessionId
          ? { ...item, title: pdfName }
          : item
      );
      setHistoryItems(updatedHistory);
      setCurrentSession(pdfName);
    } else {
      // Fallback: create a new history entry when starting a session
      const timestamp = new Date().toLocaleString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      const tempId = `temp_${Date.now()}`;

      const newItem = {
        id: tempId,
        title: pdfName,
        timestamp: `Today, ${timestamp}`,
        isTemp: true,
      };

      setHistoryItems((prev) => [newItem, ...prev]);
      setCurrentSessionId(tempId);
      setCurrentSession(pdfName);
    }
  };

  const handleExitSession = () => {
    setCurrentSession(null);
    setCurrentSessionId(null);
    // Automatically create a new chat entry when exiting
    handleNewChat();
  };

  const handleHistoryUpdate = (updatedHistory) => {
    setHistoryItems(updatedHistory);
  };

  const handleDeleteConversation = async (conversationId) => {
    if (
      !conversationId ||
      conversationId === "undefined" ||
      conversationId.startsWith("temp_")
    ) {
      console.error(
        "Invalid or temporary conversation ID for deletion:",
        conversationId
      );

      // If it's a temp conversation, just remove it locally
      if (conversationId.startsWith("temp_")) {
        setHistoryItems((prev) =>
          prev.filter((item) => getConversationId(item) !== conversationId)
        );
        if (currentSessionId === conversationId) {
          handleNewChat();
        }
      }
      return;
    }

    try {
      setLoading(true);

      console.log("� Deleting conversation (lesson):", conversationId);

      // Try to delete from Lesson Service first (this is the lesson ID)
      try {
        const lessonDeleteResponse = await fetch(
          `${API_BASE_URL}/api/lessons/${conversationId}/delete/`,
          {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${
                localStorage.getItem("access_token") || ""
              }`,
            },
          }
        );

        if (lessonDeleteResponse.ok) {
          console.log(" Lesson deleted successfully");
        } else {
          console.warn(
            " Failed to delete lesson:",
            lessonDeleteResponse.status
          );
        }
      } catch (lessonError) {
        console.warn(" Error deleting lesson:", lessonError);
      }

      // Also try to delete from Teaching Service (conversations endpoint)
      try {
        await apiCall(`/api/conversations/${conversationId}/delete/`, {
          method: "DELETE",
        });
        console.log(" Conversation deleted successfully");
      } catch (conversationError) {
        console.warn(" Error deleting conversation:", conversationError);
      }

      // Remove from local state immediately
      setHistoryItems((prev) =>
        prev.filter((item) => getConversationId(item) !== conversationId)
      );

      // If the deleted conversation was current, create a new one
      if (currentSessionId === conversationId) {
        handleNewChat();
      }

      console.log(" Deletion completed");

      // Optional: Refresh from backend after a short delay to ensure consistency
      setTimeout(() => {
        loadChatHistory();
      }, 1000);
    } catch (error) {
      console.error(" Error deleting conversation:", error);
      setError("Failed to delete conversation");

      // Refresh conversations to ensure UI consistency
      loadChatHistory();

      // Show user-friendly error message
      alert("Failed to delete conversation. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRenameConversation = async (conversationId, newTitle) => {
    if (
      !conversationId ||
      !newTitle.trim() ||
      conversationId === "undefined" ||
      conversationId.startsWith("temp_")
    ) {
      console.error(
        "Invalid conversation ID or title for rename:",
        conversationId
      );

      // If it's a temp conversation, just update it locally
      if (conversationId.startsWith("temp_")) {
        setHistoryItems((prev) =>
          prev.map((item) =>
            getConversationId(item) === conversationId
              ? { ...item, title: newTitle.trim() }
              : item
          )
        );
      }
      return;
    }

    try {
      await apiCall(`/api/conversations/${conversationId}/rename/`, {
        method: "POST",
        body: JSON.stringify({ title: newTitle.trim() }),
      });

      // Update local state immediately
      setHistoryItems((prev) =>
        prev.map((item) =>
          getConversationId(item) === conversationId
            ? { ...item, title: newTitle.trim() }
            : item
        )
      );

      console.log("Conversation renamed successfully");
    } catch (error) {
      console.error("Error renaming conversation:", error);
      setError("Failed to rename conversation");
      alert("Failed to rename conversation. Please try again.");
    }
  };

  const handleFullscreenChange = (isFullscreen) => {
    setIsSessionFullscreen(isFullscreen);
  };

  const handleConversationCreated = (conversationId, title) => {
    if (!conversationId) return;

    // Store conversation ID for Quiz and Notes components
    console.log("� Storing conversation ID for Quiz/Notes:", conversationId);
    sessionStorage.setItem("lessonId", conversationId);
    sessionStorage.setItem("conversationId", conversationId);
    localStorage.setItem("currentConversationId", conversationId);

    // Replace the temporary conversation with the real one
    setCurrentSessionId(conversationId);

    // Update the history item with the new conversation ID
    setHistoryItems((prev) =>
      prev.map((item) => {
        const itemId = getConversationId(item);
        return itemId === currentSessionId || item.isTemp
          ? {
              ...item,
              id: conversationId,
              _id: conversationId, // Ensure backend compatibility
              conversation_id: conversationId,
              title: title || item.title,
              isTemp: false, // Remove temp flag
            }
          : item;
      })
    );

    console.log("Conversation created with ID:", conversationId);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const mainPaddingLeft = useMemo(() => {
    if (isSessionFullscreen) return "lg:pl-0"; // No padding in fullscreen
    if (sidebarCollapsed) return "lg:pl-0";
    return "lg:pl-72";
  }, [sidebarCollapsed, isSessionFullscreen]);

  return (
    <div className="relative min-h-screen bg-background overflow-hidden">
      <GlowingBackground />
      {/* Watermark Logo */}
      {/* <img
        src="/GnyanSetu.png"
        alt="GnyanSetu Watermark"
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "600px",
          opacity: 0.08,
          zIndex: 0,
          pointerEvents: "none",
          userSelect: "none",
        }}
      /> */}

      {/* Error Toast */}
      {error && (
        <div className="fixed top-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-white/80 hover:text-white"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>Processing...</span>
          </div>
        </div>
      )}

      {/* Mobile top bar only */}
      {!isSessionFullscreen && (
        <div
          className={`lg:hidden fixed top-0 left-0 right-0 z-30 flex items-center justify-between border-b border-slate-700/40 bg-background px-4 h-14`}
        >
          <button
            className="inline-flex items-center gap-2 rounded-md border border-slate-700/50 bg-slate-800/60 px-3 py-2 text-slate-200 hover:bg-slate-700/60 transition-colors"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              className="text-slate-200"
            >
              <path
                d="M3 6h18M3 12h18M3 18h18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            <span className="text-sm">Menu</span>
          </button>

          <ProfileMenu />
        </div>
      )}

      {/* Desktop profile top-right */}
      {!isSessionFullscreen && (
        <div className="hidden lg:block fixed top-4 right-8 z-30">
          <ProfileMenu />
        </div>
      )}

      {/* Sidebar */}
      {!isSessionFullscreen && (
        <Sidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onNewChat={handleNewChat}
          history={historyItems}
          onHistoryUpdate={handleHistoryUpdate}
          onHistoryItemClick={handleHistoryItemClick}
          currentSessionId={currentSessionId}
          onToggleSidebar={toggleSidebar}
          collapsed={sidebarCollapsed}
          onDeleteConversation={handleDeleteConversation}
          onRenameConversation={handleRenameConversation}
        />
      )}

      {/* Main content */}
      <main
        className={`relative z-10 ${mainPaddingLeft} pt-20 lg:pt-12 transition-all duration-300 overflow-hidden`}
      >
        {currentSession ? (
          <SessionManager
            pdfName={currentSession}
            onExitSession={handleExitSession}
            onFullscreenChange={handleFullscreenChange}
            currentUserId={currentUserId}
            currentConversationId={currentSessionId}
            onConversationCreated={handleConversationCreated}
          />
        ) : (
          <div className="mx-auto max-w-5xl px-4 lg:px-8">
            <header className="mb-8 lg:mb-10">
              <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-white">
                Upload Your PDF
              </h1>
              <p className="mt-3 max-w-2xl text-slate-300/90 md:text-lg leading-relaxed">
                Transform your documents into interactive learning experiences
                with AI.
              </p>
            </header>

            <UploadBox onStartSession={handleStartSession} />
          </div>
        )}
      </main>
    </div>
  );
}