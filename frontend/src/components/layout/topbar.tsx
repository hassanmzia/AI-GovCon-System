"use client";

import Link from "next/link";
import { Bell, LogOut, User, Trash2, Sun, Moon, Menu } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import api from "@/lib/api";

interface Notification {
  id: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  timestamp: Date;
  /** Internal router path to navigate when the item is clicked. */
  link: string;
}

interface TopbarProps {
  onMenuClick?: () => void;
}

// ---------------------------------------------------------------------------
// Fetch live notifications from real API endpoints
// ---------------------------------------------------------------------------

async function fetchLiveNotifications(): Promise<Notification[]> {
  const results: Notification[] = [];

  // 1. Pending approvals  → /deals/approvals/?status=pending
  //    Backend now returns `deal_title` (added to ApprovalSerializer).
  //    Link: /deals/<deal-id>
  try {
    const res = await api.get("/deals/approvals/", {
      params: { status: "pending", ordering: "-created_at", page_size: 20 },
    });
    const approvals: Array<{
      id: string;
      deal: string;
      deal_title?: string;
      approval_type?: string;
      created_at: string;
    }> = res.data.results ?? res.data ?? [];

    for (const a of approvals) {
      const ts = a.created_at ? new Date(a.created_at) : new Date();
      results.push({
        id: `approval-${a.id}`,
        message: `${(a.deal_title ?? "Deal").slice(0, 55)} needs ${(
          a.approval_type ?? "approval"
        ).replace(/_/g, " ")}`,
        type: "warning",
        timestamp: ts,
        link: `/deals/${a.deal}`,
      });
    }
  } catch {
    // silently ignore — auth may not be ready yet
  }

  // 2. Deals with deadline in the next 7 days  → /deals/deals/
  //    Timestamp = now (the notification is generated now, not at the deadline).
  //    Link: /deals/<deal-id>
  try {
    const now = new Date();
    const soon = new Date(now.getTime() + 7 * 86400000);
    const res = await api.get("/deals/deals/", {
      params: { ordering: "due_date", page_size: 50 },
    });
    const deals: Array<{
      id: string;
      title?: string;
      due_date?: string | null;
    }> = res.data.results ?? res.data ?? [];

    for (const d of deals) {
      if (!d.due_date) continue;
      const due = new Date(d.due_date);
      if (isNaN(due.getTime()) || due < now || due > soon) continue;
      const daysLeft = Math.ceil((due.getTime() - now.getTime()) / 86400000);
      results.push({
        id: `deadline-${d.id}`,
        message: `"${(d.title ?? "Deal").slice(0, 50)}" deadline in ${daysLeft} day${
          daysLeft === 1 ? "" : "s"
        }`,
        type: daysLeft <= 2 ? "error" : "warning",
        timestamp: now,
        link: `/deals/${d.id}`,
      });
    }
  } catch {
    // silently ignore
  }

  // 3. Opportunities posted in the last 24 h  → /opportunities/
  //    The list serializer exposes `posted_date` (not `created_at`).
  //    Link: /opportunities/<opp-id>
  try {
    const cutoff = new Date(Date.now() - 86400000);
    const res = await api.get("/opportunities/", {
      params: { ordering: "-posted_date", page_size: 10 },
    });
    const opps: Array<{
      id: string;
      title?: string;
      posted_date?: string | null;
    }> = res.data.results ?? res.data ?? [];

    for (const opp of opps) {
      if (!opp.posted_date) continue;
      const posted = new Date(opp.posted_date);
      if (isNaN(posted.getTime()) || posted < cutoff) continue;
      results.push({
        id: `opp-${opp.id}`,
        message: `New opportunity: ${(opp.title ?? "Untitled").slice(0, 55)}`,
        type: "info",
        timestamp: posted,
        link: `/opportunities/${opp.id}`,
      });
    }
  } catch {
    // silently ignore
  }

  // Sort newest-first, cap at 20
  return results
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 20);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Topbar({ onMenuClick }: TopbarProps) {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const { theme, toggleTheme } = useThemeStore();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    const live = await fetchLiveNotifications();
    setNotifications(live);
  }, []);

  // Load on mount, refresh every 60 s
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60_000);
    return () => clearInterval(interval);
  }, [refresh]);

  const visible = notifications.filter((n) => !dismissed.has(n.id));
  const unreadCount = visible.length;

  const removeNotification = (id: string) => {
    setDismissed((prev) => new Set(prev).add(id));
  };

  const clearAll = () => {
    setDismissed(new Set(notifications.map((n) => n.id)));
  };

  const displayName = user
    ? `${user.first_name || user.username} ${user.last_name || ""}`.trim()
    : "User";

  const formatTime = (date: Date) => {
    if (isNaN(date.getTime())) return "";
    const diff = Date.now() - date.getTime();
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (Math.abs(hours) < 1) return "just now";
    if (hours > 0 && hours < 24) return `${hours}h ago`;
    if (days > 0 && days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-4 md:px-6">
      {/* Left: hamburger (mobile) + title */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <h2 className="text-base font-semibold text-foreground md:text-lg">
          AI Deal Manager
        </h2>
      </div>

      {/* Right: theme toggle + notifications + user */}
      <div className="flex items-center gap-1 md:gap-4">
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? (
            <Sun className="h-5 w-5 text-yellow-400" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-[calc(100vw-2rem)] max-w-sm md:w-80"
          >
            <div className="flex items-center justify-between px-2 py-2">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              {unreadCount > 0 && (
                <button
                  onMouseDown={(e) => {
                    e.preventDefault();
                    clearAll();
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear all
                </button>
              )}
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-72 overflow-y-auto">
              {visible.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No notifications
                </div>
              ) : (
                visible.map((notification) => (
                  <div key={notification.id} className="border-b last:border-b-0">
                    <div className="flex items-start gap-3 hover:bg-accent transition-colors group">
                      {/* Clickable area navigates to the relevant page */}
                      <Link
                        href={notification.link}
                        className="flex flex-1 items-start gap-3 px-2 py-3 min-w-0"
                        onClick={() => removeNotification(notification.id)}
                      >
                        <div
                          className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 ${
                            notification.type === "success"
                              ? "bg-green-500"
                              : notification.type === "warning"
                              ? "bg-yellow-500"
                              : notification.type === "error"
                              ? "bg-red-500"
                              : "bg-blue-500"
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground break-words">
                            {notification.message}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatTime(notification.timestamp)}
                          </p>
                        </div>
                      </Link>
                      {/* Dismiss button — does not navigate */}
                      <button
                        onMouseDown={(e) => {
                          e.preventDefault();
                          removeNotification(notification.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 mt-2 mr-2 hover:bg-destructive/10 rounded flex-shrink-0"
                        aria-label="Dismiss"
                      >
                        <Trash2 className="h-3 w-3 text-destructive" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2 md:gap-3 md:px-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                <User className="h-4 w-4" />
              </div>
              <span className="hidden text-sm font-medium text-foreground sm:block">
                {displayName}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem asChild>
              <Link href="/profile" className="flex cursor-pointer items-center gap-2">
                <User className="h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={logout}
              className="flex cursor-pointer items-center gap-2 text-destructive"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
