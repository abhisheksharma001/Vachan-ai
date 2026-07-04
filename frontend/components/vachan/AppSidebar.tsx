"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Menu,
  MessageSquare,
  Mic2,
  Settings,
  Users,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/personas", label: "Personas", icon: Users },
  { href: "/mirror", label: "Mirror", icon: MessageSquare },
  { href: "/conversations", label: "Conversations", icon: Mic2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function NavLinks({
  activeHref,
  onNavigate,
}: {
  activeHref: string;
  onNavigate?: () => void;
}) {
  return (
    <>
      {NAV.map((item) => {
        const active = activeHref.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all duration-200",
              active
                ? "bg-coral-500 text-sand-50"
                : "text-ink-700 hover:translate-x-0.5 hover:bg-sand-200 hover:text-ink-900"
            )}
          >
            <item.icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-sand-300 bg-sand-100 lg:flex">
        <div className="flex h-16 items-center px-6">
          <Link href="/" className="font-display text-2xl font-medium text-ink-900">
            Vachan<span className="text-coral-500">.</span>ai
          </Link>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-4 py-4">
          <NavLinks activeHref={pathname} />
        </nav>
      </aside>

      {/* Mobile sheet menu */}
      <Dialog>
        <DialogTrigger
          render={
            <Button
              variant="ghost"
              size="icon"
              className="fixed right-4 top-3.5 z-50 lg:hidden"
              aria-label="Open navigation menu"
            >
              <Menu className="size-5" />
            </Button>
          }
        />
        <DialogContent
          showCloseButton={false}
          className="!fixed !top-0 !left-0 !h-full !w-[280px] !max-w-[80vw] !-translate-x-0 !-translate-y-0 !rounded-none !p-0"
        >
          <DialogTitle className="sr-only">Navigation menu</DialogTitle>
          <div className="flex h-full flex-col bg-sand-100">
            <div className="flex h-16 items-center justify-between border-b border-sand-300 px-5">
              <Link
                href="/"
                className="font-display text-xl font-medium text-ink-900"
              >
                Vachan<span className="text-coral-500">.</span>ai
              </Link>
              <DialogClose
                render={
                  <Button variant="ghost" size="icon" aria-label="Close menu">
                    <X className="size-5" />
                  </Button>
                }
              />
            </div>
            <nav className="flex flex-1 flex-col gap-1 px-4 py-4">
              <NavLinks activeHref={pathname} />
            </nav>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
