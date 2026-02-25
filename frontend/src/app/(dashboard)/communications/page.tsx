"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getThreads,
  getMessages,
  sendMessage,
  getClarificationQuestions,
  createThread,
} from "@/services/communications";
import {
  CommunicationThread,
  Message,
  ClarificationQuestion,
} from "@/types/communications";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Loader2,
  MessageSquare,
  Bot,
  Send,
  Plus,
  ChevronRight,
  X,
} from "lucide-react";

type TabId = "threads" | "clarifications";

const THREAD_TYPE_STYLES: Record<string, string> = {
  internal: "bg-gray-100 text-gray-700",
  client: "bg-blue-100 text-blue-700",
  agency: "bg-purple-100 text-purple-700",
  vendor: "bg-orange-100 text-orange-700",
  teaming_partner: "bg-teal-100 text-teal-700",
};

const THREAD_TYPE_LABELS: Record<string, string> = {
  internal: "Internal",
  client: "Client",
  agency: "Agency",
  vendor: "Vendor",
  teaming_partner: "Teaming Partner",
};

const THREAD_STATUS_STYLES: Record<string, string> = {
  active: "bg-green-500",
  archived: "bg-gray-400",
  resolved: "bg-blue-500",
};

const QUESTION_STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  submitted: "bg-yellow-100 text-yellow-700",
  answered: "bg-green-100 text-green-700",
  withdrawn: "bg-red-100 text-red-700",
};

const QUESTION_SOURCE_LABELS: Record<string, string> = {
  vendor_submitted: "Vendor",
  government_issued: "Government",
  internal: "Internal",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  if (diffHours < 1) {
    const mins = Math.floor(diffMs / (1000 * 60));
    return `${mins}m ago`;
  }
  if (diffHours < 24) {
    return `${Math.floor(diffHours)}h ago`;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatFullDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function truncate(str: string, maxLen: number): string {
  if (!str) return "--";
  return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
}

// ── New Thread Modal ──────────────────────────────────────────────────────

interface NewThreadModalProps {
  onClose: () => void;
  onCreated: (thread: CommunicationThread) => void;
}

function NewThreadModal({ onClose, onCreated }: NewThreadModalProps) {
  const [subject, setSubject] = useState("");
  const [threadType, setThreadType] = useState("internal");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const threadTypes = [
    { value: "internal", label: "Internal" },
    { value: "client", label: "Client" },
    { value: "agency", label: "Agency" },
    { value: "vendor", label: "Vendor" },
    { value: "teaming_partner", label: "Teaming Partner" },
  ];

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim()) {
      setError("Subject is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const thread = await createThread({
        subject: subject.trim(),
        thread_type: threadType as CommunicationThread["thread_type"],
        deal: dealId || undefined,
      });
      onCreated(thread);
    } catch {
      setError("Failed to create thread. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">New Thread</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Subject <span className="text-red-500">*</span></label>
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Technical Questions – RFP Section L" autoFocus />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Type</label>
            <select value={threadType} onChange={(e) => setThreadType(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              {threadTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Deal (optional)</label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2"><Loader2 className="h-4 w-4 animate-spin" />Loading deals...</div>
            ) : (
              <select value={dealId} onChange={(e) => setDealId(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option value="">No deal selected</option>
                {deals.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
              </select>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : "Create Thread"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function CommunicationsPage() {
  const [showNewModal, setShowNewModal] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("threads");
  const [threads, setThreads] = useState<CommunicationThread[]>([]);
  const [selectedThread, setSelectedThread] =
    useState<CommunicationThread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [questions, setQuestions] = useState<ClarificationQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchThreads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [threadsData, questionsData] = await Promise.all([
        getThreads().catch(() => ({ results: [], count: 0 })),
        getClarificationQuestions().catch(() => ({ results: [], count: 0 })),
      ]);
      setThreads(threadsData.results || []);
      setQuestions(questionsData.results || []);
    } catch (err) {
      setError("Failed to load communications. Please try again.");
      console.error("Error fetching communications:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSelectThread = async (thread: CommunicationThread) => {
    setSelectedThread(thread);
    setMessagesLoading(true);
    try {
      const data = await getMessages(thread.id);
      setMessages(data.results || []);
    } catch (err) {
      console.error("Error fetching messages:", err);
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedThread || !newMessage.trim()) return;
    setSending(true);
    try {
      const msg = await sendMessage({
        thread: selectedThread.id,
        content: newMessage.trim(),
        message_type: "text",
      });
      setMessages((prev) => [...prev, msg]);
      setNewMessage("");
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const tabs: { id: TabId; label: string }[] = [
    { id: "threads", label: "Threads" },
    { id: "clarifications", label: "Clarification Questions" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Communications</h1>
          <p className="text-muted-foreground">
            Manage threads, messages, and clarification questions
          </p>
        </div>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Thread
        </Button>
      </div>

      {showNewModal && (
        <NewThreadModal
          onClose={() => setShowNewModal(false)}
          onCreated={(thread) => {
            setThreads((prev) => [thread, ...prev]);
            setShowNewModal(false);
          }}
        />
      )}

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="outline" onClick={fetchThreads}>
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* Threads Tab */}
          {activeTab === "threads" && (
            <div className="grid grid-cols-1 gap-0 lg:grid-cols-[360px_1fr] h-[calc(100vh-320px)] min-h-[500px]">
              {/* Left Panel - Thread List */}
              <Card className="lg:rounded-r-none border-r-0 overflow-hidden flex flex-col">
                <CardHeader className="pb-3 shrink-0">
                  <CardTitle className="text-base">
                    Threads
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      ({threads.length})
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-0">
                  {threads.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full py-12 px-4">
                      <MessageSquare className="h-10 w-10 text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground text-center">
                        No threads yet. Create one to get started.
                      </p>
                    </div>
                  ) : (
                    threads.map((thread) => (
                      <button
                        key={thread.id}
                        onClick={() => handleSelectThread(thread)}
                        className={`w-full text-left px-4 py-3 border-b hover:bg-muted/50 transition-colors flex items-start gap-3 ${
                          selectedThread?.id === thread.id ? "bg-muted" : ""
                        }`}
                      >
                        {/* Status dot */}
                        <div className="mt-1.5 shrink-0">
                          <div
                            className={`h-2 w-2 rounded-full ${
                              THREAD_STATUS_STYLES[thread.status] ||
                              "bg-gray-400"
                            }`}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1 mb-0.5">
                            <span className="font-medium text-sm truncate">
                              {thread.subject}
                            </span>
                            <span className="text-xs text-muted-foreground shrink-0">
                              {formatDate(thread.updated_at)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-medium ${
                                THREAD_TYPE_STYLES[thread.thread_type] ||
                                "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {THREAD_TYPE_LABELS[thread.thread_type] ||
                                thread.thread_type}
                            </span>
                            {thread.deal_name && (
                              <span className="text-xs text-muted-foreground truncate">
                                {truncate(thread.deal_name, 25)}
                              </span>
                            )}
                          </div>
                          {thread.message_count !== undefined && (
                            <span className="text-xs text-muted-foreground mt-0.5 block">
                              {thread.message_count} message
                              {thread.message_count !== 1 ? "s" : ""}
                            </span>
                          )}
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
                      </button>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Right Panel - Messages */}
              <Card className="lg:rounded-l-none overflow-hidden flex flex-col">
                {!selectedThread ? (
                  <div className="flex flex-col items-center justify-center h-full py-12 px-4">
                    <MessageSquare className="h-12 w-12 text-muted-foreground mb-3" />
                    <p className="text-muted-foreground">
                      Select a thread to view messages
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Thread header */}
                    <CardHeader className="pb-3 border-b shrink-0">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base">
                            {selectedThread.subject}
                          </CardTitle>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                THREAD_TYPE_STYLES[
                                  selectedThread.thread_type
                                ] || "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {THREAD_TYPE_LABELS[
                                selectedThread.thread_type
                              ] || selectedThread.thread_type}
                            </span>
                            <span className="text-xs text-muted-foreground capitalize">
                              {selectedThread.status}
                            </span>
                            {selectedThread.deal_name && (
                              <span className="text-xs text-muted-foreground">
                                &bull; {selectedThread.deal_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardHeader>

                    {/* Messages area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                      {messagesLoading ? (
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                      ) : messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12">
                          <p className="text-sm text-muted-foreground">
                            No messages yet. Start the conversation.
                          </p>
                        </div>
                      ) : (
                        messages.map((msg) => {
                          const isAI = msg.message_type === "ai_generated";
                          const isSystem = msg.message_type === "system";
                          return (
                            <div
                              key={msg.id}
                              className={`flex gap-2 ${
                                isSystem
                                  ? "justify-center"
                                  : isAI
                                  ? "justify-start"
                                  : "justify-end"
                              }`}
                            >
                              {isSystem ? (
                                <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
                                  {msg.content}
                                </span>
                              ) : isAI ? (
                                <div className="flex items-start gap-2 max-w-[75%]">
                                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 mt-0.5">
                                    <Bot className="h-4 w-4 text-primary" />
                                  </div>
                                  <div>
                                    <div className="rounded-2xl rounded-tl-sm bg-muted px-3 py-2 text-sm">
                                      {msg.content}
                                    </div>
                                    <span className="text-xs text-muted-foreground mt-0.5 block pl-1">
                                      {msg.sender_name || "AI"} &bull;{" "}
                                      {formatDate(msg.created_at)}
                                    </span>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-start gap-2 max-w-[75%]">
                                  <div>
                                    <div className="rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-3 py-2 text-sm">
                                      {msg.content}
                                    </div>
                                    <span className="text-xs text-muted-foreground mt-0.5 block text-right pr-1">
                                      {msg.sender_name || "You"} &bull;{" "}
                                      {formatDate(msg.created_at)}
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input */}
                    <div className="border-t p-3 shrink-0">
                      <div className="flex items-end gap-2">
                        <textarea
                          value={newMessage}
                          onChange={(e) => setNewMessage(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
                          className="flex-1 min-h-[60px] max-h-[120px] resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          rows={2}
                        />
                        <Button
                          onClick={handleSendMessage}
                          disabled={sending || !newMessage.trim()}
                          size="icon"
                          className="h-10 w-10 shrink-0"
                        >
                          {sending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Send className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </Card>
            </div>
          )}

          {/* Clarification Questions Tab */}
          {activeTab === "clarifications" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Clarification Questions
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({questions.length} total)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {questions.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <p className="text-muted-foreground">
                      No clarification questions found.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            #
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Question
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Section
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Source
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Status
                          </th>
                          <th className="pb-3 pr-4 font-medium text-muted-foreground">
                            Submitted
                          </th>
                          <th className="pb-3 font-medium text-muted-foreground">
                            Due Date
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {questions.map((q) => (
                          <tr
                            key={q.id}
                            className="border-b hover:bg-muted/50 transition-colors cursor-pointer"
                          >
                            <td className="py-3 pr-4 text-muted-foreground font-mono text-xs">
                              {q.question_number
                                ? `Q${q.question_number}`
                                : "—"}
                            </td>
                            <td className="py-3 pr-4 font-medium max-w-[280px]">
                              {truncate(q.question_text, 80)}
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground text-xs">
                              {q.rfp_section || "--"}
                            </td>
                            <td className="py-3 pr-4">
                              <span className="inline-flex items-center rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs">
                                {QUESTION_SOURCE_LABELS[q.source] || q.source}
                              </span>
                            </td>
                            <td className="py-3 pr-4">
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                  QUESTION_STATUS_STYLES[q.status] ||
                                  "bg-gray-100 text-gray-600"
                                }`}
                              >
                                {q.status.charAt(0).toUpperCase() +
                                  q.status.slice(1)}
                              </span>
                            </td>
                            <td className="py-3 pr-4 text-muted-foreground text-xs">
                              {formatFullDate(q.submitted_at)}
                            </td>
                            <td className="py-3 text-muted-foreground text-xs">
                              {formatFullDate(q.due_date)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
