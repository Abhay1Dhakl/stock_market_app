import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <LayoutShell
      title="NEPSE Intelligence Workspace"
      description="Terminal-inspired assignment app for crawling market news, tagging companies, analyzing behavior, and routing the work through viewer, analyst, and admin surfaces."
    >
      <div className="kpi-strip">
        <div className="kpi">
          <div className="kpi__label">Crawler Sources</div>
          <div className="kpi__value">02</div>
          <div className="kpi__note">ShareSansar and MeroLagani provide the news and market input stream.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Access Roles</div>
          <div className="kpi__value">03</div>
          <div className="kpi__note">Viewer, analyst, and admin workflows are enforced through JWT and RBAC.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Analysis Modules</div>
          <div className="kpi__value">05</div>
          <div className="kpi__note">Pressure, anomalies, sentiment, broker activity, and correlation are exposed.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Review Loop</div>
          <div className="kpi__value">Manual</div>
          <div className="kpi__note">Low-confidence tags can be corrected and preserved from the review desk.</div>
        </div>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Platform" title="What The Stack Already Covers" aside={<span className="badge">Full Stack</span>}>
          <ul className="list">
            <li>JWT auth with admin, analyst, and viewer roles</li>
            <li>Live news crawling from ShareSansar and MeroLagani</li>
            <li>Daily price and floorsheet ingestion from ShareSansar</li>
            <li>Rule-based multi-label categorization with confidence scores</li>
            <li>Derived analysis snapshots for pressure, anomaly, sentiment, and broker activity</li>
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Workflow" title="How Operators Move Through The App" aside={<span className="badge">Role Aware</span>}>
          <ul className="list">
            <li>
              <Link href="/login">Access console</Link> issues the browser session through the backend JWT login endpoint
            </li>
            <li>
              <Link href="/dashboard">Watchlist dashboard</Link> scans cross-company signals, headlines, and anomalies
            </li>
            <li>
              <Link href="/review">Review desk</Link> lets analysts and admins override low-confidence categorization
            </li>
            <li>
              <Link href="/admin">Ops console</Link> triggers crawls, inspects users, and manages role creation
            </li>
          </ul>
        </SectionCard>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Demo Run" title="Best Submission Walkthrough">
          <ol className="list">
            <li>Open the access page and sign in with the bootstrapped admin account.</li>
            <li>Run a full crawl from the ops page with inline execution enabled.</li>
            <li>Move to the watchlist and inspect the company summary cards.</li>
            <li>Open a company board to review price history, floorsheet trades, and news correlation.</li>
            <li>Finish in the review desk and correct one low-confidence article if available.</li>
          </ol>
        </SectionCard>

        <SectionCard
          eyebrow="Access"
          title="Default Admin Credentials"
          aside={
            <Link className="button" href="/login">
              Start Demo
            </Link>
          }
        >
          <p>
            Email: <strong>admin@example.com</strong>
          </p>
          <p>
            Password: <strong>admin123</strong>
          </p>
          <p className="muted">Create analyst and viewer accounts from the ops console once the admin session is active.</p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
