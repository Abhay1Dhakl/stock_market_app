import type { ReactNode } from "react";
import Link from "next/link";

type LayoutShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/review", label: "Review" },
  { href: "/admin", label: "Admin" },
  { href: "/login", label: "Sign In" },
];

const tickerItems = ["News Crawlers", "30D Prices", "Floorsheet", "Categorization", "RBAC"];

const workspaceStats = [
  {
    label: "News Sources",
    value: "02",
    note: "ShareSansar and MeroLagani are used for the current news and market data pipeline.",
  },
  {
    label: "Seeded Names",
    value: "06",
    note: "The current watchlist ships with six seeded NEPSE companies across multiple sectors.",
  },
  {
    label: "Protected Roles",
    value: "03",
    note: "Admin, analyst, and viewer permissions are enforced by the backend on every route.",
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
              <span>NEPSE Stock Intelligence</span>
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
              <div className="shell__eyebrow">NEPSE Market Platform</div>
              <h1 className="shell__title">{title}</h1>
              <p className="shell__description">{description}</p>
              <div className="shell__meta">
                <span className="signal-pill signal-pill--accent">JWT + RBAC</span>
                <span className="signal-pill">News + OHLCV</span>
                <span className="signal-pill">Manual Recategorization</span>
              </div>
            </div>

            <aside className="shell__hero-side">
              <div className="shell__brief">
                <div className="card__eyebrow">System Summary</div>
                <p className="shell__brief-copy">
                  FastAPI and Next.js application for crawling NEPSE market news, tagging tracked companies, storing
                  30-day market data, and exposing analysis through protected review and administration screens.
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
