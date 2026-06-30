"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type EmptyStateAction =
  | { label: string; href: string; onClick?: never }
  | { label: string; onClick: () => void; href?: never };

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: EmptyStateAction;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-sand-300 bg-sand-100 p-8 text-center shadow-sm sm:p-10",
        className
      )}
    >
      <div className="flex size-16 items-center justify-center rounded-full bg-sand-200 text-coral-500 sm:size-20">
        <Icon className="size-8 sm:size-10" />
      </div>
      <h3 className="font-display mt-5 text-xl font-medium text-ink-900">{title}</h3>
      <p className="mt-2 max-w-xs text-sm text-ink-700">{description}</p>
      {action && (
        <div className="mt-6">
          {action.href ? (
            <Link href={action.href} className={buttonVariants()}>
              {action.label}
            </Link>
          ) : (
            <Button onClick={action.onClick}>{action.label}</Button>
          )}
        </div>
      )}
    </div>
  );
}
