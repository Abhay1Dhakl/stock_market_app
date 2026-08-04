"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
  const [newUserFullName, setNewUserFullName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState<"admin" | "analyst" | "viewer">("analyst");
  const [newUserIsActive, setNewUserIsActive] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);
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

  async function createUser() {
    if (!session) {
      return;
    }

    setCreatingUser(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await apiRequest("/admin/users", {
        token: session.access_token,
        method: "POST",
        body: {
          full_name: newUserFullName,
          email: newUserEmail,
          password: newUserPassword,
          role: newUserRole,
          is_active: newUserIsActive,
        },
      });
      setSuccessMessage(`Created ${newUserRole} user ${newUserEmail}.`);
      setNewUserFullName("");
      setNewUserEmail("");
      setNewUserPassword("");
      setNewUserRole("analyst");
      setNewUserIsActive(true);
      await loadAdmin(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to create user.");
    } finally {
      setCreatingUser(false);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Ops Console"
        description="Admin access is required before this page can manage crawl runs, user creation, and operational metadata."
      >
        <SectionCard eyebrow="Access" title="Session Required">
          <p>Login as the admin user and return here.</p>
          <Link className="button" href="/login">
            Go to Login
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const activeUsers = users.filter((user) => user.is_active).length;
  const completedRuns = crawlRuns.filter((run) => run.status === "completed").length;

  return (
    <LayoutShell
      title="Operations Console"
      description="Admin workspace for crawl execution, role provisioning, and quick inspection of the pipeline state exposed by the backend."
    >
      {loading ? (
        <SectionCard eyebrow="Status" title="Loading">
          <p>Fetching crawl history and users.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard eyebrow="Status" title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : (
        <>
          {successMessage ? (
            <SectionCard eyebrow="Status" title="Success">
              <p>{successMessage}</p>
            </SectionCard>
          ) : null}

          <div className="kpi-strip">
            <div className="kpi">
              <div className="kpi__label">Known Users</div>
              <div className="kpi__value">{users.length}</div>
              <div className="kpi__note">Accounts provisioned through bootstrap and the in-app admin user creator.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Active Users</div>
              <div className="kpi__value">{activeUsers}</div>
              <div className="kpi__note">Users currently flagged as active and allowed to authenticate.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Recent Runs</div>
              <div className="kpi__value">{crawlRuns.length}</div>
              <div className="kpi__note">The latest crawl executions loaded from the protected admin API.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Completed Runs</div>
              <div className="kpi__value">{completedRuns}</div>
              <div className="kpi__note">Finished runs let you confirm whether the ingestion and analysis loop is healthy.</div>
            </div>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Crawlers" title="Trigger Crawl" aside={<span className="badge">{runKind}</span>}>
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

            <SectionCard eyebrow="Users" title="Create User" aside={<span className="badge">{newUserRole}</span>}>
              <div className="form">
                <label className="field">
                  <span>Full Name</span>
                  <input
                    value={newUserFullName}
                    onChange={(event) => setNewUserFullName(event.target.value)}
                    placeholder="Analyst User"
                    type="text"
                  />
                </label>

                <label className="field">
                  <span>Email</span>
                  <input
                    value={newUserEmail}
                    onChange={(event) => setNewUserEmail(event.target.value)}
                    placeholder="analyst@example.com"
                    type="email"
                  />
                </label>

                <label className="field">
                  <span>Password</span>
                  <input
                    value={newUserPassword}
                    onChange={(event) => setNewUserPassword(event.target.value)}
                    placeholder="analyst123"
                    type="password"
                  />
                </label>

                <label className="field">
                  <span>Role</span>
                  <select value={newUserRole} onChange={(event) => setNewUserRole(event.target.value as typeof newUserRole)}>
                    <option value="analyst">Analyst</option>
                    <option value="viewer">Viewer</option>
                    <option value="admin">Admin</option>
                  </select>
                </label>

                <label className="checkbox">
                  <input checked={newUserIsActive} onChange={() => setNewUserIsActive((current) => !current)} type="checkbox" />
                  <span>User is active</span>
                </label>

                <button
                  className="button"
                  disabled={creatingUser || !newUserFullName || !newUserEmail || !newUserPassword}
                  onClick={createUser}
                  type="button"
                >
                  {creatingUser ? "Creating..." : "Create User"}
                </button>
              </div>
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Directory" title="Current Users" aside={<span className="badge">{users.length} total</span>}>
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

            <SectionCard eyebrow="Runs" title="Recent Crawl Runs" aside={<span className="badge">{crawlRuns.length} loaded</span>}>
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
          </div>
        </>
      )}
    </LayoutShell>
  );
}
