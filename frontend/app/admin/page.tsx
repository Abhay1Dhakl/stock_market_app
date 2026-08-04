import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function AdminPage() {
  return (
    <LayoutShell
      title="Admin Console"
      description="Admin-facing screen for watchlist management, crawl runs, and user-role administration."
    >
      <div className="grid grid--two">
        <SectionCard title="Crawl Runs">
          <p>Trigger and monitor crawl runs here.</p>
        </SectionCard>
        <SectionCard title="Users & Roles">
          <p>Manage admin, analyst, and viewer access here.</p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
