import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";

export default function LoginPage() {
  return (
    <LayoutShell
      title="Login"
      description="Authentication UI placeholder for admin, analyst, and viewer roles."
    >
      <SectionCard title="Planned Behavior">
        <p>
          This page will submit credentials to the backend JWT login endpoint and
          store the resulting access token for role-aware navigation.
        </p>
      </SectionCard>
    </LayoutShell>
  );
}

