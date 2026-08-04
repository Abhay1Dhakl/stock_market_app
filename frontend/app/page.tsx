import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <LayoutShell
      title="Assignment Scaffold"
      description="Phase 1 sets up the application shape so the next phases can focus on data models, APIs, crawling, and analysis."
    >
      <div className="grid grid--two">
        <SectionCard title="What Exists">
          <ul className="list">
            <li>FastAPI route skeleton with assignment-aligned endpoints</li>
            <li>Next.js route skeleton for dashboard, review, admin, and login</li>
            <li>Docker Compose baseline for PostgreSQL, Redis, backend, and frontend</li>
          </ul>
        </SectionCard>
        <SectionCard title="Next Phase">
          <p>
            We now have a clean place to add the database schema, roles, models,
            and seed data without restructuring the repo again.
          </p>
          <p>
            Start from the <Link href="/dashboard">dashboard shell</Link> once the
            backend models are added.
          </p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}

