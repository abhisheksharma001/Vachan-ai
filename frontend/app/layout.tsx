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
    "Vachan.ai Tone Engine — Phase 0 design-system shell (Sandy + Coral).",
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
      <body>{children}</body>
    </html>
  );
}
