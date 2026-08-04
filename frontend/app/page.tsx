import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <LayoutShell
      title="Stock Market Intelligence"
      description="Full-stack assignment app for crawling NEPSE market news, auto-tagging companies, analyzing trading behavior, and exposing the workflow through role-aware pages."
    >
      <div className="grid grid--two">
        <SectionCard title="Completed Backend Flow">
          <ul className="list">
            <li>JWT auth with admin, analyst, and viewer roles</li>
            <li>Live news crawling from ShareSansar and MeroLagani</li>
            <li>Daily price and floorsheet ingestion from ShareSansar</li>
            <li>Rule-based multi-label categorization with confidence scores</li>
            <li>Derived analysis snapshots for pressure, anomaly, sentiment, and broker activity</li>
          </ul>
        </SectionCard>

        <SectionCard title="Completed Frontend Flow">
          <ul className="list">
            <li>
              <Link href="/login">Login page</Link> for creating a browser JWT session
            </li>
            <li>
              <Link href="/dashboard">Dashboard</Link> with cross-company summaries and recent tagged news
            </li>
            <li>
              <Link href="/review">Review queue</Link> for analyst/admin recategorization
            </li>
            <li>
              <Link href="/admin">Admin console</Link> for crawl execution and user inspection
            </li>
          </ul>
        </SectionCard>
      </div>

      <div className="grid grid--two">
        <SectionCard title="Recommended Demo Path">
          <ol className="list">
            <li>Login with the bootstrapped admin credentials.</li>
            <li>Run a full crawl from the admin page with inline execution enabled.</li>
            <li>Open the dashboard and then drill into a company detail page.</li>
            <li>Review low-confidence articles and submit a manual correction.</li>
          </ol>
        </SectionCard>

        <SectionCard title="Default Admin">
          <p>
            Email: <strong>admin@example.com</strong>
          </p>
          <p>
            Password: <strong>admin123</strong>
          </p>
          <Link className="button" href="/login">
            Start Demo
          </Link>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
