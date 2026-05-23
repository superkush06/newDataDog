import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { TopShell } from "@/components/TopShell";

export const metadata: Metadata = {
  title: "PULSE — brand intelligence terminal",
  description:
    "Social listening + LLM Optimization. What the open web and AI models actually say about your brand.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,400;9..144,500;9..144,600;9..144,700;9..144,900&family=JetBrains+Mono:wght@400;500;600&family=Manrope:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-ink-950 text-paper antialiased">
        <Providers>
          <TopShell>{children}</TopShell>
        </Providers>
      </body>
    </html>
  );
}
