import Link from "next/link";
import { ExternalLink, GitFork, Code2, FileText, HeartHandshake, Terminal, BookOpen } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function OpenSourcePage() {
  return (
    <>
      {/* Hero */}
      <section className="px-6 pt-20 pb-16 sm:pt-28">
        <div className="mx-auto max-w-3xl text-center">
          <p className="label mb-4 text-coral-600">Open source</p>
          <h1 className="font-display text-ink-900 mb-6">Open source by default</h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-ink-700">
            Vachan.ai is built in public. Self-host it, fork it, audit it, and contribute back.
          </p>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <a
              href="https://github.com/abhisheksharma001/Vachan-ai"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-pill bg-coral-500 px-6 py-2.5 text-sm font-semibold text-sand-50 shadow-sm transition-colors hover:bg-coral-600"
            >
              <Code2 className="size-4" />
              View on GitHub
              <ExternalLink className="size-3.5 opacity-70" />
            </a>
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-pill border border-sand-300 bg-sand-100 px-6 py-2.5 text-sm font-semibold text-ink-900 transition-colors hover:bg-sand-200"
            >
              Try the Mirror
            </Link>
          </div>
        </div>
      </section>

      {/* License + self-host */}
      <section className="px-6 py-16">
        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2">
          <Card className="bg-sand-50">
            <CardHeader>
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full bg-coral-500/10 text-coral-600">
                <FileText className="size-5" />
              </div>
              <CardTitle className="font-display text-ink-900">MIT license</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-ink-700">
                Vachan.ai is released under the MIT license. Use it commercially, modify it, and ship it with your own products.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-sand-50">
            <CardHeader>
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full bg-coral-500/10 text-coral-600">
                <Terminal className="size-5" />
              </div>
              <CardTitle className="font-display text-ink-900">Self-host in minutes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-ink-700">
                Clone the repo, copy <code className="rounded bg-sand-200 px-1 py-0.5 text-xs text-ink-900">.env.example</code> to <code className="rounded bg-sand-200 px-1 py-0.5 text-xs text-ink-900">.env</code>, and run:
              </p>
              <pre className="mt-3 overflow-x-auto rounded-lg bg-ink-900 p-3 text-xs text-sand-100">
                <code>docker compose up --build</code>
              </pre>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Links */}
      <section className="border-y border-sand-300 bg-sand-100 px-6 py-16">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display text-ink-900 mb-8 text-center">Resources for contributors</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <a
              href="https://github.com/abhisheksharma001/Vachan-ai"
              target="_blank"
              rel="noreferrer"
              className="group flex items-start gap-4 rounded-xl bg-sand-50 p-5 ring-1 ring-foreground/10 transition-shadow hover:shadow-md"
            >
              <Code2 className="size-5 shrink-0 text-coral-600" />
              <div>
                <h3 className="font-display text-ink-900 mb-1">GitHub repository</h3>
                <p className="text-sm text-ink-700">Browse the code, open issues, and fork the project.</p>
              </div>
            </a>

            <a
              href="https://github.com/abhisheksharma001/Vachan-ai/blob/main/CONTRIBUTING.md"
              target="_blank"
              rel="noreferrer"
              className="group flex items-start gap-4 rounded-xl bg-sand-50 p-5 ring-1 ring-foreground/10 transition-shadow hover:shadow-md"
            >
              <HeartHandshake className="size-5 shrink-0 text-coral-600" />
              <div>
                <h3 className="font-display text-ink-900 mb-1">Contributing guide</h3>
                <p className="text-sm text-ink-700">Learn how to set up the dev environment and submit PRs.</p>
              </div>
            </a>

            <a
              href="https://github.com/abhisheksharma001/Vachan-ai/blob/main/docs/02_ARCHITECTURE.md"
              target="_blank"
              rel="noreferrer"
              className="group flex items-start gap-4 rounded-xl bg-sand-50 p-5 ring-1 ring-foreground/10 transition-shadow hover:shadow-md"
            >
              <BookOpen className="size-5 shrink-0 text-coral-600" />
              <div>
                <h3 className="font-display text-ink-900 mb-1">Architecture docs</h3>
                <p className="text-sm text-ink-700">Understand the tone engine, capsule pipeline, and channel layer.</p>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Contributor CTA */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="font-display text-ink-900 mb-4">Help us build the voice layer for India</h2>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-ink-700">
            We are looking for contributors who care about voice AI, Indian languages, and privacy-first design.
          </p>
          <a
            href="https://github.com/abhisheksharma001/Vachan-ai/blob/main/CONTRIBUTING.md"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center rounded-pill bg-coral-500 px-7 py-3 text-base font-semibold text-sand-50 shadow-md transition-colors hover:bg-coral-600"
          >
            Become a contributor
          </a>
        </div>
      </section>
    </>
  );
}
