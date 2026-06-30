"use client";

import { Edit2, Trash2, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Persona } from "@/lib/types";
import { PersonaStatusBadge } from "./PersonaStatusBadge";

export function PersonaCard({
  persona,
  onClick,
  actions,
  className,
}: {
  persona: Persona;
  onClick?: () => void;
  actions?: {
    onEdit?: () => void;
    onDelete?: () => void;
  };
  className?: string;
}) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-shadow hover:shadow-md",
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-sand-200 text-ink-700">
          <User className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <CardTitle className="truncate">{persona.name}</CardTitle>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <PersonaStatusBadge status={persona.status} />
            <span className="chip">{persona.languagePrimary}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm text-ink-700">
          <span>
            {persona.observationsCount.toLocaleString()} observation
            {persona.observationsCount === 1 ? "" : "s"}
          </span>
          <span className="text-ink-500">
            {persona.createdAt
              ? new Date(persona.createdAt).toLocaleDateString()
              : "—"}
          </span>
        </div>
      </CardContent>
      {actions && (actions.onEdit || actions.onDelete) && (
        <CardFooter className="gap-2">
          {actions.onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                actions.onEdit?.();
              }}
            >
              <Edit2 className="size-3.5" />
              Edit
            </Button>
          )}
          {actions.onDelete && (
            <Button
              variant="destructive"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                actions.onDelete?.();
              }}
            >
              <Trash2 className="size-3.5" />
              Delete
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
