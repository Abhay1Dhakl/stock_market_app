import type { ReactNode } from "react";
import Link from "next/link";

type LayoutShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/dashboard", label: "Market Desk" },
  { href: "/review", label: "Review" },
  { href: "/admin", label: "Operations" },
  { href: "/login", label: "Sign In" },
];

const tickerItems = ["Personal Watchlists", "News Signals", "Broker Flow", "RBAC", "Behavior Analytics"];

const workspaceStats = [
  {
    label: "News Sources",
    value: "02",
    note: "ShareSansar and MeroLagani power the live market and news ingestion flow.",
  },
  {
    label: "Coverage",
    value: "06",
    note: "The platform starts with six NEPSE names and now supports user-led company expansion.",
  },
  {
    label: "Roles",
    value: "03",
    note: "Admin, analyst, and viewer permissions are enforced at the API layer.",
  },
];

export function LayoutShell({ title, description, children }: LayoutShellProps) {
  return (
    <main>
      <div className="shell">
        <header className="shell__header">
          <div className="shell__topline">
            <div className="shell__brand">
              <Link href="/" className="shell__mark">
                StockMarket Pro
              </Link>
              <span className="shell__brand-note">NEPSE intelligence workspace</span>
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
              <div className="shell__eyebrow">Stock Intelligence Platform</div>
              <h1 className="shell__title">{title}</h1>
              <p className="shell__description">{description}</p>
              <div className="shell__meta">
                <span className="signal-pill signal-pill--accent">Role-aware</span>
                <span className="signal-pill">Dynamic watchlists</span>
                <span className="signal-pill">Market + news analysis</span>
              </div>
            </div>

            <aside className="shell__hero-side">
              <div className="shell__brief">
                <div className="card__eyebrow">Platform Summary</div>
                <p className="shell__brief-copy">
                  A clean operator-facing product for monitoring NEPSE names, expanding coverage from user demand, and
                  tracking how teams actually use the analysis stack.
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
              <Link key={item.href} className="shell__nav-link" href={item.href}>
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
