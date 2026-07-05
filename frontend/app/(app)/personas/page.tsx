"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Users } from "lucide-react";

import {
  useCreatePersona,
  useDeletePersona,
  usePersonas,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/vachan/EmptyState";
import { PersonaCard } from "@/components/vachan/PersonaCard";

const LANGUAGES = [
  { value: "hi-en", label: "Hinglish (hi-en)" },
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
];

export default function PersonasPage() {
  const router = useRouter();
  const personasQuery = usePersonas();
  const createPersona = useCreatePersona();
  const deletePersona = useDeletePersona();

  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("hi-en");

  const [deleteId, setDeleteId] = useState<string | null>(null);

  const personas = personasQuery.data ?? [];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    createPersona.mutate(
      { name: trimmed, languagePrimary: language },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setName("");
          setLanguage("hi-en");
        },
      }
    );
  };

  const handleDeleteConfirm = () => {
    if (!deleteId) return;
    deletePersona.mutate(deleteId, {
      onSuccess: () => setDeleteId(null),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink-900">Personas</h1>
          <p className="mt-2 text-ink-700">Manage your voices.</p>
        </div>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger
            render={
              <Button>
                <Plus className="size-4" />
                New persona
              </Button>
            }
          />
          <DialogContent>
            <form onSubmit={handleCreate}>
              <DialogHeader>
                <DialogTitle>Create persona</DialogTitle>
                <DialogDescription>
                  Give your new voice a name and choose its primary language.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <label htmlFor="persona-name" className="label">
                    Name
                  </label>
                  <Input
                    id="persona-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Work Alex"
                    disabled={createPersona.isPending}
                  />
                </div>
                <div className="grid gap-2">
                  <label htmlFor="persona-language" className="label">
                    Language
                  </label>
                  <select
                    id="persona-language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={createPersona.isPending}
                    className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-base outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:bg-input/50 disabled:opacity-50 md:text-sm"
                  >
                    {LANGUAGES.map((lang) => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {createPersona.isError && (
                <p className="mb-4 text-sm text-rose-600">
                  {createPersona.error.message}
                </p>
              )}
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateOpen(false)}
                  disabled={createPersona.isPending}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createPersona.isPending}>
                  {createPersona.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {personasQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-40 animate-pulse rounded-xl bg-sand-200"
            />
          ))}
        </div>
      ) : personas.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No personas yet"
          description="Create a persona to capture your writing style and chat with your clone."
          action={{ label: "New persona", onClick: () => setCreateOpen(true) }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {personas.map((persona) => (
            <PersonaCard
              key={persona.id}
              persona={persona}
              onClick={() => router.push(`/personas/${persona.id}`)}
              actions={{
                onDelete: () => setDeleteId(persona.id),
              }}
            />
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      <Dialog open={Boolean(deleteId)} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete persona?</DialogTitle>
            <DialogDescription>
              This will permanently remove the persona and all of its captured
              data. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {deletePersona.isError && (
            <p className="text-sm text-rose-600">{deletePersona.error.message}</p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteId(null)}
              disabled={deletePersona.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deletePersona.isPending}
            >
              <Trash2 className="size-4" />
              {deletePersona.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
