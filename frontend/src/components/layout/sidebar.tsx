"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import {
  LayoutDashboard,
  Search,
  Handshake,
  FileText,
  FileEdit,
  DollarSign,
  ClipboardCheck,
  Lightbulb,
  Megaphone,
  BookOpen,
  Scale,
  Users,
  ShieldCheck,
  Database,
  MessageSquare,
  Settings,
  KeyRound,
  BarChart3,
  Award,
  Cpu,
  X,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Opportunities", href: "/opportunities", icon: Search },
  { name: "Deals", href: "/deals", icon: Handshake },
  { name: "Solutions", href: "/solutions", icon: Cpu },
  { name: "RFP", href: "/rfp", icon: FileText },
  { name: "Proposals", href: "/proposals", icon: FileEdit },
  { name: "Pricing", href: "/pricing", icon: DollarSign },
  { name: "Contracts", href: "/contracts", icon: ClipboardCheck },
  { name: "Strategy", href: "/strategy", icon: Lightbulb },
  { name: "Marketing", href: "/marketing", icon: Megaphone },
  { name: "Research", href: "/research", icon: BookOpen },
  { name: "Legal", href: "/legal", icon: Scale },
  { name: "Teaming", href: "/teaming", icon: Users },
  { name: "Security", href: "/security", icon: ShieldCheck },
  { name: "Knowledge Vault", href: "/knowledge-vault", icon: Database },
  { name: "Communications", href: "/communications", icon: MessageSquare },
  { name: "Past Performance", href: "/past-performance", icon: Award },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

const adminNavigation = [
  { name: "Manage Users", href: "/admin/users", icon: KeyRound },
];

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex h-full w-72 flex-col border-r border-border bg-card transition-transform duration-300 ease-in-out",
          "md:static md:w-64 md:translate-x-0 md:transition-none",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo header */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4 md:px-6">
          <div className="flex items-center gap-2">
            <Handshake className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold text-foreground">Deal Manager</span>
          </div>
          {/* Close button — mobile only */}
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground md:hidden"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {navigation.map((item) => {
              const isActive =
                pathname === item.href || pathname?.startsWith(item.href + "/");

              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.name}
                  </Link>
                </li>
              );
            })}

            {/* Admin Section */}
            {user?.role === "admin" && (
              <>
                <li className="px-3 py-3 mt-4 pt-4 border-t border-border">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Admin
                  </p>
                </li>
                {adminNavigation.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    pathname?.startsWith(item.href + "/");

                  return (
                    <li key={item.name}>
                      <Link
                        href={item.href}
                        onClick={onClose}
                        className={cn(
                          "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        )}
                      >
                        <item.icon className="h-4 w-4 shrink-0" />
                        {item.name}
                      </Link>
                    </li>
                  );
                })}
              </>
            )}
          </ul>
        </nav>

        <div className="border-t border-border px-3 py-4">
          <p className="px-3 text-xs text-muted-foreground">
            AI Deal Manager v0.1.0
          </p>
        </div>
      </aside>
    </>
  );
}
