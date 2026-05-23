import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pulse — Brand Intelligence",
  description: "Social listening + LLMO pipeline dashboard",
};

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/feed",      label: "Live Feed" },
  { href: "/clusters",  label: "Clusters" },
  { href: "/queue",     label: "Priority Queue" },
  { href: "/llmo",      label: "LLMO" },
  { href: "/actions",   label: "Actions" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <Providers>
          <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
            <div className="max-w-7xl mx-auto px-4 flex items-center gap-6 h-14">
              <span className="font-bold text-indigo-600 text-lg tracking-tight">Pulse</span>
              <nav className="flex gap-1">
                {NAV.map(({ href, label }) => (
                  <Link
                    key={href}
                    href={href}
                    className="px-3 py-1.5 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                  >
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
