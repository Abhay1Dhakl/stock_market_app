"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import type {
  CompanyCreateRequest,
  CompanyListResponse,
  CompanySummary,
  CompanyUpdateRequest,
  CrawlRunListResponse,
  CrawlRunResponse,
  TokenResponse,
  UserListResponse,
} from "@/types";

export default function AdminPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [crawlRuns, setCrawlRuns] = useState<CrawlRunResponse[]>([]);
  const [users, setUsers] = useState<UserListResponse["items"]>([]);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [runKind, setRunKind] = useState<"news" | "market_data" | "full">("full");
  const [sources, setSources] = useState<string[]>(["merolagani", "sharesansar"]);
  const [executeNow, setExecuteNow] = useState(true);
  const [newUserFullName, setNewUserFullName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState<"admin" | "analyst" | "viewer">("analyst");
  const [newUserIsActive, setNewUserIsActive] = useState(true);
  const [newCompanySymbol, setNewCompanySymbol] = useState("");
  const [newCompanyName, setNewCompanyName] = useState("");
  const [newCompanySector, setNewCompanySector] = useState("");
  const [newCompanyAliases, setNewCompanyAliases] = useState("");
  const [newCompanyDescription, setNewCompanyDescription] = useState("");
  const [newCompanyIsActive, setNewCompanyIsActive] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);
  const [creatingCompany, setCreatingCompany] = useState(false);
  const [updatingCompanyId, setUpdatingCompanyId] = useState<number | null>(null);
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
      const [crawlRunResponse, userResponse, companyResponse] = await Promise.all([
        apiRequest<CrawlRunListResponse>("/admin/crawl-runs?limit=10", {
          token: activeSession.access_token,
        }),
        apiRequest<UserListResponse>("/admin/users", {
          token: activeSession.access_token,
        }),
        apiRequest<CompanyListResponse>("/admin/companies", {
          token: activeSession.access_token,
        }),
      ]);
      setCrawlRuns(crawlRunResponse.items);
      setUsers(userResponse.items);
      setCompanies(companyResponse.items);
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

  async function createCompany() {
    if (!session) {
      return;
    }

    setCreatingCompany(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const payload: CompanyCreateRequest = {
        symbol: newCompanySymbol,
        name: newCompanyName,
        sector: newCompanySector,
        aliases: parseAliases(newCompanyAliases),
        description: newCompanyDescription.trim() || null,
        is_active: newCompanyIsActive,
      };
      await apiRequest("/admin/companies", {
        token: session.access_token,
        method: "POST",
        body: payload,
      });
      setSuccessMessage(`Added ${newCompanySymbol.toUpperCase()} to the watchlist.`);
      setNewCompanySymbol("");
      setNewCompanyName("");
      setNewCompanySector("");
      setNewCompanyAliases("");
      setNewCompanyDescription("");
      setNewCompanyIsActive(true);
      await loadAdmin(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to create company.");
    } finally {
      setCreatingCompany(false);
    }
  }

  async function toggleCompanyStatus(company: CompanySummary) {
    if (!session) {
      return;
    }

    setUpdatingCompanyId(company.id);
    setError(null);
    setSuccessMessage(null);

    try {
      const payload: CompanyUpdateRequest = {
        is_active: !company.is_active,
      };
      await apiRequest(`/admin/companies/${company.id}`, {
        token: session.access_token,
        method: "PATCH",
        body: payload,
      });
      setSuccessMessage(`${company.symbol} is now ${company.is_active ? "inactive" : "active"}.`);
      await loadAdmin(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to update company.");
    } finally {
      setUpdatingCompanyId(null);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Administration"
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
  const succeededRuns = crawlRuns.filter((run) => run.status === "succeeded").length;
  const activeCompanies = companies.filter((company) => company.is_active).length;

  return (
    <LayoutShell
      title="Administration"
      description="Trigger crawl jobs, inspect recent run history, and provision role-based users from the protected admin API."
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
              <div className="kpi__label">Provisioned Users</div>
              <div className="kpi__value">{users.length}</div>
              <div className="kpi__note">Accounts created through bootstrap and the protected admin user creation flow.</div>
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
              <div className="kpi__label">Active Watchlist</div>
              <div className="kpi__value">{activeCompanies}</div>
              <div className="kpi__note">Tracked companies currently active for crawling, categorization, and analysis.</div>
            </div>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Crawlers" title="Run Crawl Pipeline" aside={<span className="badge">{runKind}</span>}>
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
                  <span>Execute immediately in the API process instead of queue-only mode</span>
                </label>

                <button className="button" disabled={submitting} onClick={triggerCrawl} type="button">
                  {submitting ? "Running..." : "Start Crawl Run"}
                </button>
              </div>
            </SectionCard>

            <SectionCard eyebrow="Users" title="Create Platform User" aside={<span className="badge">{newUserRole}</span>}>
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
            <SectionCard eyebrow="Directory" title="User Directory" aside={<span className="badge">{users.length} total</span>}>
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

            <SectionCard eyebrow="Runs" title="Run History" aside={<span className="badge">{crawlRuns.length} loaded</span>}>
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

          <div className="grid grid--two">
            <SectionCard eyebrow="Watchlist" title="Add Tracked Company" aside={<span className="badge">{activeCompanies} active</span>}>
              <div className="form">
                <label className="field">
                  <span>Symbol</span>
                  <input
                    value={newCompanySymbol}
                    onChange={(event) => setNewCompanySymbol(event.target.value.toUpperCase())}
                    placeholder="NICA"
                    type="text"
                  />
                </label>

                <label className="field">
                  <span>Company Name</span>
                  <input
                    value={newCompanyName}
                    onChange={(event) => setNewCompanyName(event.target.value)}
                    placeholder="NIC Asia Bank Limited"
                    type="text"
                  />
                </label>

                <label className="field">
                  <span>Sector</span>
                  <input
                    value={newCompanySector}
                    onChange={(event) => setNewCompanySector(event.target.value)}
                    placeholder="Banking"
                    type="text"
                  />
                </label>

                <label className="field">
                  <span>Aliases</span>
                  <input
                    value={newCompanyAliases}
                    onChange={(event) => setNewCompanyAliases(event.target.value)}
                    placeholder="NIC Asia, NICA"
                    type="text"
                  />
                </label>

                <label className="field">
                  <span>Description</span>
                  <textarea
                    rows={3}
                    value={newCompanyDescription}
                    onChange={(event) => setNewCompanyDescription(event.target.value)}
                    placeholder="Short reason for tracking this company."
                  />
                </label>

                <label className="checkbox">
                  <input checked={newCompanyIsActive} onChange={() => setNewCompanyIsActive((current) => !current)} type="checkbox" />
                  <span>Track this company immediately</span>
                </label>

                <button
                  className="button"
                  disabled={creatingCompany || !newCompanySymbol || !newCompanyName || !newCompanySector}
                  onClick={createCompany}
                  type="button"
                >
                  {creatingCompany ? "Adding..." : "Add Company"}
                </button>
              </div>
            </SectionCard>

            <SectionCard eyebrow="Watchlist" title="Current Coverage" aside={<span className="badge">{companies.length} total</span>}>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Name</th>
                      <th>Sector</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {companies.map((company) => (
                      <tr key={company.id}>
                        <td>{company.symbol}</td>
                        <td>{company.name}</td>
                        <td>{company.sector}</td>
                        <td>{company.is_active ? "Active" : "Inactive"}</td>
                        <td>
                          <button
                            className="button button--ghost"
                            disabled={updatingCompanyId === company.id}
                            onClick={() => toggleCompanyStatus(company)}
                            type="button"
                          >
                            {updatingCompanyId === company.id
                              ? "Updating..."
                              : company.is_active
                                ? "Deactivate"
                                : "Activate"}
                          </button>
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

function parseAliases(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
