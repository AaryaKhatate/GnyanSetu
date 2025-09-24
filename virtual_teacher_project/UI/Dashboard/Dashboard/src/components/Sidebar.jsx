import React, { useEffect, useState } from "react";

export default function Sidebar({
  open,
  onClose,
  onNewChat,
  history,
  onHistoryUpdate,
  onHistoryItemClick,
  currentSessionId,
  onToggleSidebar,
  collapsed,
  onDeleteConversation,
  onRenameConversation,
}) {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [openMenuId, setOpenMenuId] = useState(null);
  const [deletingIds, setDeletingIds] = useState(new Set());
  const [renamingIds, setRenamingIds] = useState(new Set());

  useEffect(() => {
    const onEsc = (e) => {
      if (e.key === "Escape") {
        onClose?.();
        setOpenMenuId(null);
        setEditingId(null);
      }
    };
    if (open) {
      document.addEventListener("keydown", onEsc);
    }
    return () => document.removeEventListener("keydown", onEsc);
  }, [open, onClose]);

  // Helper function to get the correct ID from history item
  const getItemId = (item) => {
    return item._id || item.conversation_id || item.id;
  };

  // Helper function to validate item ID
  const isValidId = (itemId) => {
    return itemId && itemId !== 'undefined' && itemId !== 'null' && typeof itemId === 'string';
  };

  const handleRename = (item) => {
    const itemId = getItemId(item);
    
    if (!isValidId(itemId)) {
      console.error('Invalid conversation ID for rename:', itemId);
      return;
    }

    setEditingId(itemId);
    setEditTitle(item.title || "");
    setOpenMenuId(null);
  };

  const handleDelete = async (item) => {
    const itemId = getItemId(item);
    
    // Validate ID
    if (!isValidId(itemId)) {
      console.error('Invalid conversation ID for deletion:', itemId);
      return;
    }

    // Prevent duplicate delete requests
    if (deletingIds.has(itemId)) {
      console.log('Delete already in progress for:', itemId);
      return;
    }

    // Add to deleting set to prevent duplicates
    setDeletingIds(prev => new Set(prev).add(itemId));
    setOpenMenuId(null);

    try {
      if (onDeleteConversation) {
        await onDeleteConversation(itemId);
      } else if (onHistoryUpdate) {
        // Fallback to local handling
        onHistoryUpdate(history.filter((historyItem) => getItemId(historyItem) !== itemId));
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    } finally {
      // Remove from deleting set
      setDeletingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleSaveRename = async (item) => {
    const itemId = getItemId(item);
    
    if (!isValidId(itemId)) {
      console.error('Invalid conversation ID for rename:', itemId);
      return;
    }

    if (!editTitle.trim()) {
      console.error('Title cannot be empty');
      return;
    }

    // Prevent duplicate rename requests
    if (renamingIds.has(itemId)) {
      console.log('Rename already in progress for:', itemId);
      return;
    }

    setRenamingIds(prev => new Set(prev).add(itemId));

    try {
      if (onRenameConversation) {
        await onRenameConversation(itemId, editTitle.trim());
      } else if (onHistoryUpdate) {
        // Fallback to local handling
        const updatedHistory = history.map((historyItem) =>
          getItemId(historyItem) === itemId 
            ? { ...historyItem, title: editTitle.trim() } 
            : historyItem
        );
        onHistoryUpdate(updatedHistory);
      }
    } catch (error) {
      console.error('Error renaming conversation:', error);
    } finally {
      setRenamingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
      setEditingId(null);
      setEditTitle("");
    }
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleKeyPress = (e, item) => {
    if (e.key === "Enter") {
      handleSaveRename(item);
    } else if (e.key === "Escape") {
      handleCancelRename();
    }
  };

  const toggleMenu = (item) => {
    const itemId = getItemId(item);
    setOpenMenuId(openMenuId === itemId ? null : itemId);
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.menu-container')) {
        setOpenMenuId(null);
      }
    };

    if (openMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [openMenuId]);

  // Show toggle button when sidebar is collapsed
  if (collapsed) {
    return (
      <div className="fixed z-50 top-4 left-4">
        <button
          className="text-slate-300 hover:text-white p-2 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 transition-colors shadow-lg"
          onClick={onToggleSidebar}
          aria-label="Show sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
              d="M3 6h18M3 12h18M3 18h18"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <>
      {/* Backdrop for mobile */}
      <div
        className={`fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity lg:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
      />

      <aside
        className={`fixed z-50 top-14 lg:top-0 left-0 h-[calc(100%-3.5rem)] lg:h-full w-72 bg-slate-900/90 border-r border-slate-800/60 transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-slate-800/60">
          <div className="flex items-center gap-2">
            <img
              src="/GnyanSetu.png"
              alt="GyanSetu Logo"
              className="h-8 w-8 rounded-md"
            />
            <span className="text-white font-semibold tracking-wide">
              GyanSetu
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="hidden lg:block text-slate-300 hover:text-white p-1 rounded hover:bg-slate-800/60 transition-colors"
              onClick={onToggleSidebar}
              aria-label="Hide sidebar"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path
                  d="M3 6h18M3 12h18M3 18h18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
            <button
              className="lg:hidden text-slate-300 hover:text-white"
              onClick={onClose}
              aria-label="Close sidebar"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M6 6l12 12M6 18L18 6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-4">
          <button
            onClick={onNewChat}
            className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-indigo-300 hover:text-white hover:bg-indigo-500/20 hover:shadow-glow transition-all"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              className="text-indigo-300"
            >
              <path
                d="M12 5v14M5 12h14"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            New Chat
          </button>
        </div>

        <div className="px-4 text-xs uppercase tracking-wider text-slate-500">
          History
        </div>

        <div className="mt-2 h-[calc(100%-150px)] overflow-y-auto px-2 pb-6">
          {history && history.length > 0 ? (
            <ul className="space-y-2">
              {history.map((item) => {
                const itemId = getItemId(item);
                const isDeleting = deletingIds.has(itemId);
                const isRenaming = renamingIds.has(itemId);
                
                // Skip items with invalid IDs
                if (!isValidId(itemId)) {
                  console.warn('Skipping item with invalid ID:', item);
                  return null;
                }

                return (
                  <li key={itemId} className="group">
                    {editingId === itemId ? (
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-slate-800/40">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => handleKeyPress(e, item)}
                          className="flex-1 bg-transparent text-slate-200 border-none outline-none"
                          autoFocus
                          disabled={isRenaming}
                        />
                        <button
                          onClick={() => handleSaveRename(item)}
                          disabled={isRenaming}
                          className="text-green-400 hover:text-green-300 p-1 disabled:opacity-50"
                          title="Save"
                        >
                          {isRenaming ? (
                            <div className="w-3 h-3 border border-green-400 border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                            >
                              <path
                                d="M20 6L9 17l-5-5"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          )}
                        </button>
                        <button
                          onClick={handleCancelRename}
                          disabled={isRenaming}
                          className="text-slate-400 hover:text-slate-300 p-1 disabled:opacity-50"
                          title="Cancel"
                        >
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                          >
                            <path
                              d="M6 18L18 6M6 6l12 12"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                            />
                          </svg>
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => onHistoryItemClick?.(item)}
                        disabled={isDeleting}
                        className={`w-full flex items-center justify-between rounded-lg px-3 py-2 transition-colors disabled:opacity-50 ${
                          currentSessionId === itemId
                            ? "bg-blue-500/20 ring-1 ring-blue-500/40"
                            : "bg-slate-800/40 hover:bg-slate-800/70"
                        }`}
                      >
                        <span className="text-slate-200 truncate flex-1 text-left">
                          {item.title || "Untitled Chat"}
                        </span>
                        <div className="flex items-center gap-2 ml-2">
                          <span className="text-[10px] text-slate-500">
                            {item.timestamp}
                          </span>
                          <div className="relative menu-container">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (!isDeleting) {
                                  toggleMenu(item);
                                }
                              }}
                              disabled={isDeleting}
                              className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-300 p-1 rounded transition-opacity disabled:opacity-25"
                              title="More options"
                            >
                              {isDeleting ? (
                                <div className="w-3 h-3 border border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <svg
                                  width="14"
                                  height="14"
                                  viewBox="0 0 24 24"
                                  fill="none"
                                >
                                  <circle
                                    cx="12"
                                    cy="12"
                                    r="1"
                                    fill="currentColor"
                                  />
                                  <circle
                                    cx="19"
                                    cy="12"
                                    r="1"
                                    fill="currentColor"
                                  />
                                  <circle
                                    cx="5"
                                    cy="12"
                                    r="1"
                                    fill="currentColor"
                                  />
                                </svg>
                              )}
                            </button>
                            {openMenuId === itemId && !isDeleting && (
                              <div className="absolute right-0 top-8 w-32 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-10">
                                <button
                                  onClick={() => handleRename(item)}
                                  className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-700 rounded-t-lg"
                                >
                                  Rename
                                </button>
                                <button
                                  onClick={() => handleDelete(item)}
                                  className="w-full text-left px-3 py-2 text-sm text-rose-300 hover:bg-rose-900/40 rounded-b-lg"
                                >
                                  Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="text-slate-500 text-sm px-4 py-6">
              No chats yet. Start a new one!
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
