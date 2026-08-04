"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import type { CrawlRunListResponse, CrawlRunResponse, TokenResponse, UserListResponse } from "@/types";

export default function AdminPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [crawlRuns, setCrawlRuns] = useState<CrawlRunResponse[]>([]);
  const [users, setUsers] = useState<UserListResponse["items"]>([]);
  const [runKind, setRunKind] = useState<"news" | "market_data" | "full">("full");
  const [sources, setSources] = useState<string[]>(["merolagani", "sharesansar"]);
  const [executeNow, setExecuteNow] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }
    void loadAdmin(storedSession);
  }, []);

  async function loadAdmin(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);

    try {
      const [crawlRunResponse, userResponse] = await Promise.all([
        apiRequest<CrawlRunListResponse>("/admin/crawl-runs?limit=10", {
          token: activeSession.access_token,
        }),
        apiRequest<UserListResponse>("/admin/users", {
          token: activeSession.access_token,
        }),
      ]);
      setCrawlRuns(crawlRunResponse.items);
      setUsers(userResponse.items);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load admin console.");
    } finally {
      setLoading(false);
    }
  }

  function toggleSource(source: string) {
    setSources((current) =>
      current.includes(source) ? current.filter((value) => value !== source) : [...current, source],
    );
  }

  async function triggerCrawl() {
    if (!session) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await apiRequest<CrawlRunResponse>(`/admin/crawl-runs?execute_now=${executeNow ? "true" : "false"}`, {
        token: session.access_token,
        method: "POST",
        body: { run_kind: runKind, sources },
      });
      setSuccessMessage("Crawl run created successfully.");
      await loadAdmin(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to trigger crawl.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Admin Console"
        description="Admin access is required before this page can manage crawl runs and user-role metadata."
      >
        <SectionCard title="Session Required">
          <p>Login as the admin user and return here.</p>
          <Link className="button" href="/login">
            Go to Login
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  return (
    <LayoutShell
      title="Admin Console"
      description="Trigger crawl runs, inspect pipeline output, and audit the current role-based users loaded by the backend."
    >
      {loading ? (
        <SectionCard title="Loading">
          <p>Fetching crawl history and users.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : (
        <>
          {successMessage ? (
            <SectionCard title="Success">
              <p>{successMessage}</p>
            </SectionCard>
          ) : null}

          <div className="grid grid--two">
            <SectionCard title="Trigger Crawl">
              <div className="form">
                <label className="field">
                  <span>Run Kind</span>
                  <select value={runKind} onChange={(event) => setRunKind(event.target.value as typeof runKind)}>
                    <option value="full">Full</option>
                    <option value="news">News Only</option>
                    <option value="market_data">Market Data Only</option>
                  </select>
                </label>

                <div className="field">
                  <span>Sources</span>
                  <div className="checkbox-grid">
                    {["merolagani", "sharesansar"].map((source) => (
                      <label key={source} className="checkbox">
                        <input
                          checked={sources.includes(source)}
                          onChange={() => toggleSource(source)}
                          type="checkbox"
                        />
                        <span>{source}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <label className="checkbox">
                  <input checked={executeNow} onChange={() => setExecuteNow((current) => !current)} type="checkbox" />
                  <span>Execute inline now instead of only enqueueing</span>
                </label>

                <button className="button" disabled={submitting} onClick={triggerCrawl} type="button">
                  {submitting ? "Running..." : "Start Crawl"}
                </button>
              </div>
            </SectionCard>

            <SectionCard title="Current Users">
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.full_name}</td>
                        <td>{user.email}</td>
                        <td>{user.role}</td>
                        <td>{user.is_active ? "Active" : "Inactive"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          </div>

          <SectionCard title="Recent Crawl Runs">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Kind</th>
                    <th>Requested By</th>
                    <th>Finished</th>
                    <th>Stats</th>
                  </tr>
                </thead>
                <tbody>
                  {crawlRuns.map((crawlRun) => (
                    <tr key={crawlRun.id}>
                      <td>{crawlRun.id}</td>
                      <td>{crawlRun.status}</td>
                      <td>{crawlRun.run_kind}</td>
                      <td>{crawlRun.requested_by ?? "system"}</td>
                      <td>{crawlRun.finished_at ? new Date(crawlRun.finished_at).toLocaleString() : "Pending"}</td>
                      <td>
                        <pre className="json-block">{JSON.stringify(crawlRun.run_stats, null, 2)}</pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </>
      )}
    </LayoutShell>
  );
}
