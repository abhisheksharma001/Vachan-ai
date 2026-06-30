import Link from "next/link";
import { Plus, User } from "lucide-react";
import { AppSidebar } from "@/components/vachan/AppSidebar";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-sand-50">
      <AppSidebar />
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-sand-300 bg-sand-50/90 px-6 backdrop-blur-sm">
          <Link
            href="/"
            className="font-display text-xl font-medium text-ink-900 lg:hidden"
          >
            Vachan<span className="text-coral-500">.</span>ai
          </Link>

          <div className="ml-auto flex items-center gap-3">
            <Link
              href="/personas"
              className={cn(
                buttonVariants({ variant: "secondary", size: "sm" }),
                "gap-1.5"
              )}
            >
              <Plus className="size-4" />
              New persona
            </Link>

            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-2 pl-2"
                    aria-label="Open user menu"
                  >
                    <Avatar size="sm">
                      <AvatarFallback className="bg-coral-500/10 text-coral-700">
                        <User className="size-4" />
                      </AvatarFallback>
                    </Avatar>
                    <span className="hidden text-sm font-medium text-ink-900 sm:inline">
                      Alex
                    </span>
                  </Button>
                }
              />
              <DropdownMenuContent align="end" className="min-w-44">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="text-ink-900">Alex Sharma</span>
                    <span className="text-xs font-normal text-ink-500">
                      alex@vachan.ai
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuLabel className="text-xs font-normal text-ink-500">
                  Vachan Labs
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem render={<Link href="/settings" />}>
                  Profile & settings
                </DropdownMenuItem>
                <DropdownMenuItem render={<Link href="/settings" />}>
                  Organization
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive">
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <span className="chip hidden sm:inline-flex">Dev mode</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
