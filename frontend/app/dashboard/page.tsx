import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

const watchlist = [
  { symbol: "NABIL", note: "Banking" },
  { symbol: "NICA", note: "Commercial Bank" },
  { symbol: "HIDCL", note: "Investment" },
];

export default function DashboardPage() {
  return (
    <LayoutShell
      title="Cross-Company Dashboard"
      description="This screen will compare the watchlist across price action, activity, and recent categorized news."
    >
      <div className="grid grid--two">
        <SectionCard title="Watchlist Preview">
          <ul className="list">
            {watchlist.map((company) => (
              <li key={company.symbol}>
                <Link href={`/companies/${company.symbol}`}>{company.symbol}</Link> - {company.note}
              </li>
            ))}
          </ul>
        </SectionCard>
        <SectionCard title="Future Metrics">
          <div className="metric">5-10</div>
          <p>Tracked NEPSE companies with comparable behavior-analysis snapshots.</p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}

