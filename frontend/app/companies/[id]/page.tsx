import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function CompanyDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <LayoutShell
      title={`Company Detail: ${params.id}`}
      description="This page will combine OHLCV charts, categorized news, broker activity, and anomaly detection for one company."
    >
      <div className="grid grid--two">
        <SectionCard title="Price & Volume">
          <p>Daily market data chart placeholder.</p>
        </SectionCard>
        <SectionCard title="News Feed">
          <p>Recent categorized articles placeholder.</p>
        </SectionCard>
        <SectionCard title="Behavior Summary">
          <p>VWAP, pressure indicator, and anomaly outputs will render here.</p>
        </SectionCard>
        <SectionCard title="Floorsheet View">
          <p>Broker-wise sample-day activity will render here when collected.</p>
        </SectionCard>
      </div>
    </LayoutShell>
  );
}

