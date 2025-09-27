import React, { useState, useEffect } from "react";

const ChatHistory = ({
  userId,
  onConversationSelect,
  currentConversationId,
}) => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchConversations();
  }, [userId]);

  const fetchConversations = async () => {
    if (!userId) return;

    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8001/api/conversations/?user_id=${userId}`
      );
      const data = await response.json();

      if (response.ok) {
        setConversations(data.conversations || []);
      } else {
        setError(data.error || "Failed to fetch conversations");
      }
    } catch (err) {
      setError("Network error while fetching conversations");
      console.error("Error fetching conversations:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteConversation = async (conversationId) => {
    if (!window.confirm("Are you sure you want to delete this conversation?")) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8001/api/conversations/${conversationId}/delete/`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        setConversations((prev) =>
          prev.filter((conv) => conv._id !== conversationId)
        );
        if (currentConversationId === conversationId) {
          onConversationSelect(null);
        }
      } else {
        const data = await response.json();
        alert(data.error || "Failed to delete conversation");
      }
    } catch (err) {
      alert("Network error while deleting conversation");
      console.error("Error deleting conversation:", err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-700 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-2/3 mb-2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-400">
        <p>Error: {error}</p>
        <button
          onClick={fetchConversations}
          className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold text-white">Chat History</h3>
        <p className="text-sm text-slate-400">
          {conversations.length} conversations
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-slate-400">
            <p>No conversations yet.</p>
            <p className="text-sm mt-1">Start a new lesson to begin!</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation._id}
                className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                  currentConversationId === conversation._id
                    ? "bg-blue-600/20 border-blue-500"
                    : "bg-slate-800/50 border-slate-700 hover:bg-slate-700/50"
                }`}
                onClick={() => onConversationSelect(conversation)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-white font-medium truncate">
                      {conversation.title}
                    </h4>
                    {conversation.topic && (
                      <p className="text-sm text-slate-400 truncate mt-1">
                        Topic: {conversation.topic}
                      </p>
                    )}
                    <p className="text-xs text-slate-500 mt-1">
                      {formatDate(conversation.updated_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversation(conversation._id);
                    }}
                    className="ml-2 p-1 text-slate-400 hover:text-red-400 transition-colors"
                    title="Delete conversation"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistory;
