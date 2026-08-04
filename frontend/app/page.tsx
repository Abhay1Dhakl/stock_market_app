import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <LayoutShell
      title="NEPSE Stock Intelligence"
      description="Role-based application for crawling NEPSE news, tagging tracked companies, analyzing one month of trading behavior, and reviewing low-confidence categorization results."
    >
      <div className="kpi-strip">
        <div className="kpi">
          <div className="kpi__label">News Sources</div>
          <div className="kpi__value">02</div>
          <div className="kpi__note">ShareSansar and MeroLagani provide the crawled article and market data inputs.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Tracked Companies</div>
          <div className="kpi__value">06</div>
          <div className="kpi__note">The seeded watchlist covers banking, telecom, hydro, insurance, and cement names.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Analysis Outputs</div>
          <div className="kpi__value">05</div>
          <div className="kpi__note">Pressure, anomalies, sentiment, broker activity, and news-price correlation are exposed.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Access Roles</div>
          <div className="kpi__value">03</div>
          <div className="kpi__note">Viewer, analyst, and admin permissions are enforced server-side through JWT and RBAC.</div>
        </div>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Coverage" title="Current Product Scope" aside={<span className="badge">Backend + UI</span>}>
          <ul className="list">
            <li>Protected REST APIs for companies, news, analysis, and administration</li>
            <li>News crawling from ShareSansar and MeroLagani with URL-level deduplication</li>
            <li>One month of OHLCV data and sampled floorsheet activity for tracked NEPSE companies</li>
            <li>Rule-based multi-label company tagging with stored confidence scores</li>
            <li>Persisted behavior summaries for pressure, anomalies, broker flow, and news correlation</li>
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Workflow" title="Primary User Flows" aside={<span className="badge">Role Aware</span>}>
          <ul className="list">
            <li>
              <Link href="/login">Sign in</Link> stores a browser session issued by the backend JWT login endpoint
            </li>
            <li>
              <Link href="/dashboard">Dashboard</Link> compares the tracked watchlist across news volume, price movement, and anomaly flags
            </li>
            <li>
              <Link href="/review">Review queue</Link> lets analysts and admins correct low-confidence categorizations
            </li>
            <li>
              <Link href="/admin">Admin</Link> triggers crawls, inspects run history, and provisions users by role
            </li>
          </ul>
        </SectionCard>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Runbook" title="Suggested Product Walkthrough">
          <ol className="list">
            <li>Sign in with the seeded administrator account.</li>
            <li>Run a full crawl from the admin page with inline execution enabled.</li>
            <li>Open the dashboard and compare the watchlist by news volume and anomaly status.</li>
            <li>Drill into a company page to inspect the 30-day chart, buyer/seller activity, and correlation view.</li>
            <li>Finish in the review queue and persist one manual categorization correction if needed.</li>
          </ol>
        </SectionCard>

        <SectionCard
          eyebrow="Bootstrap"
          title="Default Administrator Access"
          aside={
            <Link className="button" href="/login">
              Open Sign In
            </Link>
          }
        >
          <p>
            Email: <strong>admin@example.com</strong>
          </p>
          <p>
            Password: <strong>admin123</strong>
          </p>
          <p className="muted">
            The initial watchlist is seeded from the backend data folder so crawling and analysis can run immediately.
          </p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
