import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: {
    template: "%s | Vachan.ai",
    default: "Vachan.ai — Every agent. Your voice.",
  },
  description:
    "Vachan.ai is an open-source tone engine. Capture how you write, build a persona capsule, and chat with a clone that sounds like you.",
};

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-sand-50">
      <header className="sticky top-0 z-50 border-b border-sand-300 bg-sand-50/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="font-display text-2xl font-medium text-ink-900">
            Vachan<span className="text-coral-500">.</span>ai
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/open-source"
              className="text-sm font-medium text-ink-700 hover:text-coral-600"
            >
              Open Source
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-pill bg-coral-500 px-5 py-2.5 text-sm font-semibold text-sand-50 shadow-sm hover:bg-coral-600"
            >
              Try the Mirror
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-sand-300 bg-sand-100 py-12">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <p className="text-ink-500">
            Vachan.ai — your voice, on every channel. Made in India, for how India
            actually talks.
          </p>
        </div>
      </footer>
    </div>
  );
}
