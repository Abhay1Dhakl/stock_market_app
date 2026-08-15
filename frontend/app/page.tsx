import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <LayoutShell
      title="A Cleaner Way To Run NEPSE Analysis"
      description="Track the names that matter, surface the companies gaining attention in the news, study broker flow, and understand how your team is using the platform."
    >
      <div className="kpi-strip">
        <div className="kpi">
          <div className="kpi__label">Signals</div>
          <div className="kpi__value">02</div>
          <div className="kpi__note">Live news and market context come from MeroLagani and ShareSansar.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Coverage</div>
          <div className="kpi__value">06</div>
          <div className="kpi__note">The platform starts with six seeded NEPSE names and can now expand from user demand.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Product Layer</div>
          <div className="kpi__value">V1</div>
          <div className="kpi__note">Personal watchlists, dynamic discovery, broker flow, and behavior analytics sit on top of the pipeline.</div>
        </div>
        <div className="kpi">
          <div className="kpi__label">Roles</div>
          <div className="kpi__value">03</div>
          <div className="kpi__note">Viewer, analyst, and admin access stays enforced at the API layer.</div>
        </div>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Platform" title="What The Product Now Does" aside={<span className="badge">End To End</span>}>
          <ul className="list">
            <li>Monitor a personal stock watchlist instead of relying only on one global tracked set.</li>
            <li>Discover companies gaining attention in the news and add them into analysis coverage.</li>
            <li>Read broker accumulation, distribution, volume anomalies, and sentiment-linked price signals.</li>
            <li>Let analysts correct weak categorizations without losing the review trail.</li>
            <li>Measure which companies, workflows, and screens users engage with most.</li>
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Workflow" title="Primary Paths" aside={<span className="badge">Role Aware</span>}>
          <ul className="list">
            <li>
              <Link href="/login">Sign in</Link> opens a protected session against the FastAPI backend.
            </li>
            <li>
              <Link href="/dashboard">Market Desk</Link> combines personal watchlists, discovery ideas, and user behavior insights.
            </li>
            <li>
              <Link href="/review">Review</Link> gives analysts a clean place to approve or fix low-confidence matches.
            </li>
            <li>
              <Link href="/admin">Operations</Link> handles crawl runs, user provisioning, coverage, and adoption metrics.
            </li>
          </ul>
        </SectionCard>
      </div>

      <div className="grid grid--two">
        <SectionCard eyebrow="Walkthrough" title="Best Demo Sequence">
          <ol className="list">
            <li>Sign in with the seeded administrator account.</li>
            <li>Run a full crawl from Operations to refresh news and market coverage.</li>
            <li>Open Market Desk and add a company to a personal watchlist.</li>
            <li>Inspect a company page for broker flow, price behavior, and linked headlines.</li>
            <li>Finish in Review and save one manual correction to show the human-in-the-loop path.</li>
          </ol>
        </SectionCard>

        <SectionCard
          eyebrow="Access"
          title="Default Administrator Account"
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
            The seeded data gets the product running quickly, but the platform is now structured for user-driven watchlists and
            coverage expansion.
          </p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
