"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { LiveDot } from "./LiveDot";

const NAV = [
  { href: "/dashboard", label: "Dashboard", code: "01" },
  { href: "/feed",      label: "Live Feed", code: "02" },
  { href: "/llmo",      label: "LLMO",      code: "03" },
  { href: "/clusters",  label: "Clusters",  code: "04" },
  { href: "/queue",     label: "Queue",     code: "05" },
  { href: "/actions",   label: "Actions",   code: "06" },
];

export function TopShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex flex-col">
      {/* MASTHEAD — terminal status bar */}
      <div className="border-b rule bg-ink-900/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-[1400px] mx-auto px-6 h-9 flex items-center gap-6 eyebrow text-[10px]">
          <LiveDot label="LIVE" />
          <span className="text-paper-mute">FEED · REDDIT</span>
          <span className="text-paper-mute hidden md:inline">CADENCE · 30s</span>
          <span className="text-paper-mute hidden md:inline">SOURCE · NIMBLE / GROQ</span>
          <span className="ml-auto text-paper-mute hidden md:inline">{currentDate()}</span>
        </div>
      </div>

      {/* MAIN NAV */}
      <header className="border-b rule bg-ink-950/95 backdrop-blur-md sticky top-9 z-30">
        <div className="max-w-[1400px] mx-auto px-6 flex items-end justify-between h-20">
          <Link href="/dashboard" className="flex items-baseline gap-3 group">
            <span className="font-display font-black text-[44px] leading-none text-paper">
              PULSE
            </span>
            <span className="eyebrow text-paper-mute hidden sm:block">
              brand intelligence ／ vol. 01
            </span>
          </Link>
          <nav className="flex items-end gap-1">
            {NAV.map(({ href, label, code }) => {
              const active = pathname === href || pathname?.startsWith(href + "/");
              return (
                <Link
                  key={href}
                  href={href}
                  className={clsx(
                    "group relative px-3 pb-2 pt-1 text-sm font-medium transition-colors",
                    active ? "text-paper" : "text-paper-mute hover:text-paper",
                  )}
                >
                  <span className="block font-mono text-[10px] tracking-terminal opacity-60">
                    {code}
                  </span>
                  <span>{label}</span>
                  {active && (
                    <span className="absolute left-3 right-3 -bottom-px h-px bg-signal" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-10">{children}</main>

      <footer className="border-t rule mt-12">
        <div className="max-w-[1400px] mx-auto px-6 py-6 flex items-center justify-between eyebrow text-[10px]">
          <span>PULSE ／ HACKATHON BUILD ／ 2026.05</span>
          <span className="text-paper-mute">
            CLICKHOUSE · POSTGRES · REDIS · GROQ · NIMBLE · DATADOG
          </span>
        </div>
      </footer>
    </div>
  );
}

function currentDate(): string {
  const d = new Date();
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${d.getUTCFullYear()}.${pad(d.getUTCMonth() + 1)}.${pad(d.getUTCDate())} · ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}
