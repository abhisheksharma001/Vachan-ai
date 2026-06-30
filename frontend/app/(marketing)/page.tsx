import Link from "next/link";
import {
  ClipboardPaste,
  MessageCircle,
  MessageSquare,
  Package,
  PenLine,
  Rocket,
  ShieldCheck,
  Star,
  User,
  Briefcase,
  Video,
  Languages,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const FEATURES = [
  {
    icon: PenLine,
    title: "Capture your voice",
    description:
      "Paste emails, chats, or scripts. Vachan builds a persona capsule from your real writing patterns.",
  },
  {
    icon: MessageSquare,
    title: "Chat with your clone",
    description:
      "Talk to a mirror that replies in your tone, pacing, and Hinglish — before any customer sees it.",
  },
  {
    icon: ShieldCheck,
    title: "Privacy-first PII scrubbing",
    description:
      "Names, numbers, and addresses are stripped before training. Your data stays yours.",
  },
];

const STEPS = [
  { icon: ClipboardPaste, title: "Paste writing", description: "Emails, chats, scripts, anything you have written." },
  { icon: Package, title: "Build a capsule", description: "We extract tone, pacing, and language habits into a reusable persona." },
  { icon: MessageCircle, title: "Chat & iterate", description: "Test replies in the Mirror and tune until it sounds like you." },
  { icon: Rocket, title: "Deploy to agents", description: "Plug the capsule into voice agents, chatbots, and outbound flows." },
];

const USE_CASES = [
  {
    icon: User,
    title: "Personal clone",
    description: "Never ghost a friend again. Let your clone handle routine messages in your voice.",
  },
  {
    icon: Briefcase,
    title: "Brand voice",
    description: "Turn one founder’s tone into a style guide that every agent follows consistently.",
  },
  {
    icon: Video,
    title: "Creator assistant",
    description: "Reply to comments, DMs, and sponsors without losing the personality your audience loves.",
  },
  {
    icon: Languages,
    title: "Hinglish & Indian languages",
    description: "Built for code-mixed speech. Train once, speak naturally across Indian languages.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden px-6 pt-20 pb-28 sm:pt-28 sm:pb-36">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,var(--coral-300),transparent_35%)] opacity-30" />
        <div className="mx-auto max-w-4xl text-center">
          <p className="label mb-4 text-coral-600">Open-source tone engine</p>
          <h1 className="font-display text-ink-900 mb-6 text-balance">
            Every agent.
            <br />
            <span className="text-coral-500">Your voice.</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-lg text-ink-700 text-balance">
            Vachan learns how you actually talk — your warmth, your pacing, your
            Hinglish — so every reply your agents send still sounds like you wrote it.
          </p>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-pill bg-coral-500 px-7 py-3 text-base font-semibold text-sand-50 shadow-md transition-colors hover:bg-coral-600"
            >
              Try the Mirror
            </Link>
            <a
              href="https://github.com/abhisheksharma/Vachan.ai"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-pill border border-sand-300 bg-sand-100 px-7 py-3 text-base font-semibold text-ink-900 transition-colors hover:bg-sand-200"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* Social proof strip */}
      <section className="border-y border-sand-300 bg-sand-100 px-6 py-8">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-4 text-center text-sm font-medium text-ink-500 sm:gap-8">
          <span className="chip">Open source</span>
          <span className="hidden text-sand-400 sm:inline">·</span>
          <span className="chip">Self-hostable</span>
          <span className="hidden text-sand-400 sm:inline">·</span>
          <span className="chip">MIT license</span>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 max-w-2xl text-center sm:mb-16">
            <p className="label mb-3 text-coral-600">Features</p>
            <h2 className="font-display text-ink-900 mb-4">A tone engine, not a template</h2>
            <p className="text-lg text-ink-700">
              Stop hard-coding prompts. Capture the way you communicate and scale it across every channel.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card
                key={feature.title}
                className="bg-sand-50 transition-shadow hover:shadow-md"
              >
                <CardHeader>
                  <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full bg-coral-500/10 text-coral-600">
                    <feature.icon className="size-5" />
                  </div>
                  <CardTitle className="font-display text-ink-900">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-ink-700">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-sand-100 px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 max-w-2xl text-center sm:mb-16">
            <p className="label mb-3 text-coral-600">How it works</p>
            <h2 className="font-display text-ink-900 mb-4">From samples to speaking clone</h2>
            <p className="text-lg text-ink-700">
              Four steps to a persona your agents can actually use.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, index) => (
              <div key={step.title} className="relative text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-coral-500 text-sand-50 font-display text-lg font-medium shadow-sm">
                  {index + 1}
                </div>
                <div className="mb-2 inline-flex items-center justify-center text-coral-600">
                  <step.icon className="size-5" />
                </div>
                <h3 className="font-display text-ink-900 mb-2 text-lg">{step.title}</h3>
                <p className="text-sm text-ink-700">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 max-w-2xl text-center sm:mb-16">
            <p className="label mb-3 text-coral-600">Use cases</p>
            <h2 className="font-display text-ink-900 mb-4">One voice, endless channels</h2>
            <p className="text-lg text-ink-700">
              Whether it is personal, professional, or public — Vachan scales your tone.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {USE_CASES.map((useCase) => (
              <Card
                key={useCase.title}
                className="bg-sand-50 transition-shadow hover:shadow-md"
              >
                <CardHeader>
                  <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full bg-sand-200 text-ink-700">
                    <useCase.icon className="size-5" />
                  </div>
                  <CardTitle className="font-display text-ink-900">{useCase.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-ink-700">{useCase.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Open source band */}
      <section className="border-y border-sand-300 bg-ink-900 px-6 py-16 sm:py-24">
        <div className="mx-auto max-w-4xl text-center">
          <p className="label mb-3 text-coral-400">Built in public</p>
          <h2 className="font-display text-sand-50 mb-4">Open source by default</h2>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-sand-200">
            Self-host the tone engine, audit the PII scrubber, and ship your own voice agents with confidence.
          </p>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-sand-500/30 bg-sand-50/10 px-4 py-2 text-sm text-sand-100">
            <Star className="size-4 fill-amber-400 text-amber-400" />
            <span>1,204 stars on GitHub</span>
          </div>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <a
              href="https://github.com/abhisheksharma/Vachan.ai"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-pill bg-coral-500 px-7 py-3 text-base font-semibold text-sand-50 shadow-md transition-colors hover:bg-coral-600"
            >
              View on GitHub
            </a>
            <Link
              href="/open-source"
              className="inline-flex items-center justify-center rounded-pill border border-sand-500/30 bg-transparent px-7 py-3 text-base font-semibold text-sand-50 transition-colors hover:bg-sand-50/10"
            >
              Read the docs
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
