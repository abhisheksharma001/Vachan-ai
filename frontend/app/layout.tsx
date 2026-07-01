/*
 * Root layout — wires the three fonts (doc 06 §6.3) via next/font so they're
 * self-hosted and fast, then exposes each as a CSS variable that globals.css
 * maps onto --font-display / --font-body / --font-mono.
 *
 *   Fraunces      → display / headings (warm humanist serif)
 *   Inter         → body / UI
 *   JetBrains Mono → capsule + code views
 */
import type { Metadata } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import "./theme.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-fraunces",
  display: "swap",
});
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});
const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vachan.ai — Every agent. Your voice.",
  description:
    "Vachan.ai learns how you talk — your warmth, pacing, and Hinglish — so every reply your AI agents send still sounds like you wrote it.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${fraunces.variable} ${inter.variable} ${jetbrains.variable}`}
    >
      <body>
        <a href="#main" className="skipLink">
          Skip to main content
        </a>
        <main id="main">{children}</main>
      </body>
    </html>
  );
}
