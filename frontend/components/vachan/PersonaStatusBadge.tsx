"use client";

import { Badge } from "@/components/ui/badge";

const LABELS: Record<string, string> = {
  warming_up: "Warming up",
  calibrating: "Calibrating",
  stable: "Stable",
};

export function PersonaStatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase();
  const label = LABELS[key] ?? status;

  if (key === "stable") {
    return (
      <Badge className="bg-teal-500 text-sand-50 hover:bg-teal-500/90">
        {label}
      </Badge>
    );
  }

  return (
    <Badge className="bg-amber-500 text-sand-50 hover:bg-amber-500/90">
      {label}
    </Badge>
  );
}
