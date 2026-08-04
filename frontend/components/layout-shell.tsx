import type { ReactNode } from "react";
import Link from "next/link";

type LayoutShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Console" },
  { href: "/dashboard", label: "Watchlist" },
  { href: "/review", label: "Review Desk" },
  { href: "/admin", label: "Ops" },
  { href: "/login", label: "Access" },
];

const tickerItems = ["News", "Prices", "Floorsheet", "Signals", "RBAC"];

const workspaceStats = [
  {
    label: "Coverage",
    value: "02",
    note: "Live crawlers connected for MeroLagani and ShareSansar.",
  },
  {
    label: "Roles",
    value: "03",
    note: "Viewer, analyst, and admin flows map cleanly to the backend guards.",
  },
  {
    label: "Loop",
    value: "24/7",
    note: "Crawl, tag, review, analyze, and expose the results in one workspace.",
  },
];

export function LayoutShell({ title, description, children }: LayoutShellProps) {
  return (
    <main>
      <div className="shell">
        <header className="shell__header">
          <div className="shell__topline">
            <div className="shell__terminal">
              <span aria-hidden className="shell__terminal-dot" />
              <span>NEPSE Market Console</span>
            </div>
            <div className="shell__ticker" aria-label="Workspace capabilities">
              {tickerItems.map((item) => (
                <span key={item} className="shell__ticker-chip">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="shell__hero">
            <div className="shell__hero-main">
              <div className="shell__eyebrow">Stock Market Intelligence</div>
              <h1 className="shell__title">{title}</h1>
              <p className="shell__description">{description}</p>
              <div className="shell__meta">
                <span className="signal-pill signal-pill--accent">Protected Workspace</span>
                <span className="signal-pill">News + Market Data</span>
                <span className="signal-pill">Manual Review Loop</span>
              </div>
            </div>

            <aside className="shell__hero-side">
              <div className="shell__brief">
                <div className="card__eyebrow">Workspace Brief</div>
                <p className="shell__brief-copy">
                  Terminal-inspired layout for scanning company movement, headline pressure, and operational state
                  without leaving the app.
                </p>
                <div className="shell__status-grid">
                  {workspaceStats.map((item) => (
                    <div key={item.label} className="shell__status-item">
                      <div className="shell__status-label">{item.label}</div>
                      <div className="shell__status-value">{item.value}</div>
                      <div className="shell__status-note">{item.note}</div>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>

          <nav className="shell__nav" aria-label="Primary">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <div className="shell__content">{children}</div>
      </div>
    </main>
  );
}
