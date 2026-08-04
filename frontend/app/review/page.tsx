import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function ReviewPage() {
  return (
    <LayoutShell
      title="Review Queue"
      description="Analyst-facing workspace for correcting miscategorized news and recording manual review decisions."
    >
      <SectionCard title="Planned Flow">
        <p>
          Articles with low confidence or ambiguous entity matches will be listed
          here for analyst review and correction.
        </p>
      </SectionCard>
    </LayoutShell>
  );
}

