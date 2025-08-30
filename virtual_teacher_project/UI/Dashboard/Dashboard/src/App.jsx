import React, { useMemo, useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import UploadBox from "./components/UploadBox";
import ProfileMenu from "./components/ProfileMenu";
import GlowingBackground from "./components/GlowingBackground";
import SessionManager from "./components/SessionManager";

// API Configuration
const API_BASE_URL = "http://localhost:8001";

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
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "An error occurred");
  }

  return data;
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isSessionFullscreen, setIsSessionFullscreen] = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentUserId, setCurrentUserId] = useState("anonymous");

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await apiCall(
        `/api/conversations/?user_id=${currentUserId}`
      );
      setHistoryItems(response.conversations || []);

      // If no conversations, create a new one
      if (!response.conversations || response.conversations.length === 0) {
        handleNewChat();
      } else {
        // Set the most recent conversation as current
        setCurrentSessionId(response.conversations[0].id);
      }
    } catch (error) {
      console.error("Error loading chat history:", error);
      // Fallback to creating a new chat
      handleNewChat();
    }
  };

  const handleNewChat = () => {
    const timestamp = new Date().toLocaleString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    const newItem = {
      id: String(Date.now()),
      title: "Untitled Chat",
      timestamp: `Today, ${timestamp}`,
    };
    setHistoryItems((prev) => [newItem, ...prev]);
    setCurrentSessionId(newItem.id);
    setCurrentSession(null); // Reset to upload screen
  };

  const handleHistoryItemClick = (item) => {
    setCurrentSessionId(item.id);
    if (item.title !== "Untitled Chat") {
      setCurrentSession(item.title);
    } else {
      setCurrentSession(null);
    }
  };

  const handleStartSession = (pdfName) => {
    // Update the current untitled chat with the PDF name
    if (currentSessionId) {
      const updatedHistory = historyItems.map((item) =>
        item.id === currentSessionId ? { ...item, title: pdfName } : item
      );
      setHistoryItems(updatedHistory);
      setCurrentSession(pdfName);
    } else {
      // Fallback: create a new history entry when starting a session
      const timestamp = new Date().toLocaleString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      const newItem = {
        id: String(Date.now()),
        title: pdfName,
        timestamp: `Today, ${timestamp}`,
      };
      setHistoryItems((prev) => [newItem, ...prev]);
      setCurrentSessionId(newItem.id);
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
    try {
      await apiCall(`/api/conversations/${conversationId}/delete/`, {
        method: "POST",
      });

      // Remove from local state
      setHistoryItems((prev) =>
        prev.filter((item) => item.id !== conversationId)
      );

      // If the deleted conversation was current, create a new one
      if (currentSessionId === conversationId) {
        handleNewChat();
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const handleRenameConversation = async (conversationId, newTitle) => {
    try {
      await apiCall(`/api/conversations/${conversationId}/rename/`, {
        method: "POST",
        body: JSON.stringify({ title: newTitle }),
      });

      // Update local state
      setHistoryItems((prev) =>
        prev.map((item) =>
          item.id === conversationId ? { ...item, title: newTitle } : item
        )
      );
    } catch (error) {
      console.error("Error renaming conversation:", error);
    }
  };

  const handleFullscreenChange = (isFullscreen) => {
    setIsSessionFullscreen(isFullscreen);
  };

  const handleConversationCreated = (conversationId, title) => {
    // Update the current session to use the new conversation ID
    setCurrentSessionId(conversationId);

    // Update the history item with the new conversation ID
    setHistoryItems((prev) =>
      prev.map((item) =>
        item.id === currentSessionId
          ? { ...item, id: conversationId, title: title }
          : item
      )
    );
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
