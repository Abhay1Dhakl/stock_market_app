"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { Pager } from "@/components/pager";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import { trackEvent } from "@/lib/telemetry";
import type {
  AdminUserBehaviorResponse,
  CompanyCreateRequest,
  CompanyListResponse,
  CompanySummary,
  CompanyUpdateRequest,
  CrawlRunListResponse,
  CrawlRunResponse,
  TokenResponse,
  UserListResponse,
} from "@/types";

const COMPANIES_PER_PAGE = 10;
const USERS_PER_PAGE = 8;

export default function AdminPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [crawlRuns, setCrawlRuns] = useState<CrawlRunResponse[]>([]);
  const [behaviorRows, setBehaviorRows] = useState<AdminUserBehaviorResponse["items"]>([]);
  const [users, setUsers] = useState<UserListResponse["items"]>([]);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [companyPage, setCompanyPage] = useState(1);
  const [userPage, setUserPage] = useState(1);
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

  useEffect(() => {
    if (!session) {
      return;
    }
    void trackEvent(session, {
      event_type: "admin_view",
      page_path: "/admin",
    });
  }, [session]);

  async function loadAdmin(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);

    try {
      const [crawlRunResponse, userResponse, companyResponse, behaviorResponse] = await Promise.all([
        apiRequest<CrawlRunListResponse>("/admin/crawl-runs?limit=10", {
          token: activeSession.access_token,
        }),
        apiRequest<UserListResponse>("/admin/users", {
          token: activeSession.access_token,
        }),
        apiRequest<CompanyListResponse>("/admin/companies", {
          token: activeSession.access_token,
        }),
        apiRequest<AdminUserBehaviorResponse>("/admin/user-behavior?limit=10", {
          token: activeSession.access_token,
        }),
      ]);
      setCrawlRuns(crawlRunResponse.items);
      setUsers(userResponse.items);
      setCompanies(companyResponse.items);
      setBehaviorRows(behaviorResponse.items);
      setCompanyPage(1);
      setUserPage(1);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load the operations console.");
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
      setSuccessMessage(`Added ${newCompanySymbol.toUpperCase()} to platform coverage.`);
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
        title="Operations"
        description="Administrator access is required before the operations console can manage crawl runs, users, and dynamic coverage."
      >
        <SectionCard eyebrow="Access" title="Session Required">
          <p>Sign in as an administrator to open the operations console.</p>
          <Link className="button" href="/login">
            Go to Sign In
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const activeUsers = users.filter((user) => user.is_active).length;
  const succeededRuns = crawlRuns.filter((run) => run.status === "succeeded").length;
  const activeCompanies = companies.filter((company) => company.is_active).length;
  const pendingCoverage = companies.filter((company) => company.coverage_status !== "ready").length;
  const companyPageCount = getPageCount(companies.length, COMPANIES_PER_PAGE);
  const userPageCount = getPageCount(users.length, USERS_PER_PAGE);
  const visibleCompanies = paginateItems(companies, companyPage, COMPANIES_PER_PAGE);
  const visibleUsers = paginateItems(users, userPage, USERS_PER_PAGE);
  const companyRangeLabel = formatRangeLabel(companies.length, companyPage, COMPANIES_PER_PAGE);
  const userRangeLabel = formatRangeLabel(users.length, userPage, USERS_PER_PAGE);

  return (
    <LayoutShell
      title="Operations"
      description="Control crawls, curate company coverage, provision users, and inspect whether the product is actually being used in a meaningful way."
    >
      {loading ? (
        <SectionCard eyebrow="Status" title="Loading">
          <p>Fetching crawl history, users, coverage, and behavior analytics.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard eyebrow="Status" title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : (
        <>
          {successMessage ? (
            <SectionCard eyebrow="Status" title="Updated">
              <p>{successMessage}</p>
            </SectionCard>
          ) : null}

          <div className="kpi-strip">
            <div className="kpi">
              <div className="kpi__label">Provisioned Users</div>
              <div className="kpi__value">{users.length}</div>
              <div className="kpi__note">Role-based access accounts currently managed by the platform.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Succeeded Runs</div>
              <div className="kpi__value">{succeededRuns}</div>
              <div className="kpi__note">Recent crawl executions that completed without a stored failure state.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Active Coverage</div>
              <div className="kpi__value">{activeCompanies}</div>
              <div className="kpi__note">Companies currently eligible for the global crawl and analysis pipeline.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Pending Coverage</div>
              <div className="kpi__value">{pendingCoverage}</div>
              <div className="kpi__note">Names that still need a successful refresh or analyst attention.</div>
            </div>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Crawls" title="Trigger A Crawl">
              <div className="field">
                <span>Run Kind</span>
                <div className="tag-row">
                  {(["full", "news", "market_data"] as const).map((value) => (
                    <button
                      key={value}
                      className={`button ${runKind === value ? "" : "button--ghost"}`}
                      onClick={() => setRunKind(value)}
                      type="button"
                    >
                      {labelize(value)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="field">
                <span>Sources</span>
                <div className="tag-row">
                  {["merolagani", "sharesansar"].map((source) => (
                    <label key={source} className="checkbox checkbox--inline">
                      <input checked={sources.includes(source)} onChange={() => toggleSource(source)} type="checkbox" />
                      <span>{labelize(source)}</span>
                    </label>
                  ))}
                </div>
              </div>

              <label className="checkbox checkbox--inline">
                <input checked={executeNow} onChange={() => setExecuteNow((value) => !value)} type="checkbox" />
                <span>Run immediately inside the current request</span>
              </label>

              <button className="button" disabled={submitting} onClick={triggerCrawl} type="button">
                {submitting ? "Submitting..." : "Start Crawl"}
              </button>

              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Run</th>
                      <th>Status</th>
                      <th>Requested By</th>
                      <th>Started</th>
                    </tr>
                  </thead>
                  <tbody>
                    {crawlRuns.map((run) => (
                      <tr key={run.id}>
                        <td>{labelize(run.run_kind)}</td>
                        <td>{labelize(run.status)}</td>
                        <td>{run.requested_by ?? "System"}</td>
                        <td>{formatDate(run.started_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>

            <SectionCard eyebrow="Adoption" title="User Behavior Overview">
              {behaviorRows.length === 0 ? (
                <p className="muted">No behavior events have been recorded yet.</p>
              ) : (
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Role</th>
                        <th>Events</th>
                        <th>Watchlist</th>
                        <th>Favorite Symbol</th>
                      </tr>
                    </thead>
                    <tbody>
                      {behaviorRows.map((row) => (
                        <tr key={row.user_id}>
                          <td>
                            {row.full_name}
                            <div className="muted">{row.email}</div>
                          </td>
                          <td>{row.role}</td>
                          <td>{row.total_events}</td>
                          <td>{row.watchlist_size}</td>
                          <td>{row.favorite_symbol ?? "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Coverage" title="Company Coverage Status">
              <div className="section-toolbar">
                <p className="pager__summary">{companyRangeLabel}</p>
                <Pager
                  label="Company coverage pages"
                  onPageChange={setCompanyPage}
                  page={companyPage}
                  totalPages={companyPageCount}
                />
              </div>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Source</th>
                      <th>Status</th>
                      <th>Last Refresh</th>
                      <th>Mode</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleCompanies.map((company) => (
                      <tr key={company.id}>
                        <td>
                          {company.symbol}
                          <div className="muted">{company.name}</div>
                        </td>
                        <td>{labelize(company.source_kind)}</td>
                        <td>{coverageLabel(company.coverage_status)}</td>
                        <td>{formatDate(company.last_refresh_at)}</td>
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

            <SectionCard eyebrow="Coverage" title="Create A Company">
              <div className="form">
                <label className="field">
                  <span>Symbol</span>
                  <input value={newCompanySymbol} onChange={(event) => setNewCompanySymbol(event.target.value.toUpperCase())} />
                </label>
                <label className="field">
                  <span>Company Name</span>
                  <input value={newCompanyName} onChange={(event) => setNewCompanyName(event.target.value)} />
                </label>
                <label className="field">
                  <span>Sector</span>
                  <input value={newCompanySector} onChange={(event) => setNewCompanySector(event.target.value)} />
                </label>
                <label className="field">
                  <span>Aliases</span>
                  <input value={newCompanyAliases} onChange={(event) => setNewCompanyAliases(event.target.value)} />
                </label>
                <label className="field">
                  <span>Description</span>
                  <textarea rows={3} value={newCompanyDescription} onChange={(event) => setNewCompanyDescription(event.target.value)} />
                </label>
                <label className="checkbox checkbox--inline">
                  <input checked={newCompanyIsActive} onChange={() => setNewCompanyIsActive((value) => !value)} type="checkbox" />
                  <span>Include this company in active coverage immediately</span>
                </label>
                <button className="button" disabled={creatingCompany} onClick={createCompany} type="button">
                  {creatingCompany ? "Creating..." : "Create Company"}
                </button>
              </div>
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Users" title="Current Team">
              <div className="section-toolbar">
                <p className="pager__summary">{userRangeLabel}</p>
                <Pager label="User pages" onPageChange={setUserPage} page={userPage} totalPages={userPageCount} />
              </div>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Last Login</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleUsers.map((user) => (
                      <tr key={user.id}>
                        <td>
                          {user.full_name}
                          <div className="muted">{user.email}</div>
                        </td>
                        <td>{user.role}</td>
                        <td>{user.is_active ? "Active" : "Inactive"}</td>
                        <td>{formatDate(user.last_login_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="muted">{activeUsers} of {users.length} users are currently active.</p>
            </SectionCard>

            <SectionCard eyebrow="Users" title="Provision A New User">
              <div className="form">
                <label className="field">
                  <span>Full Name</span>
                  <input value={newUserFullName} onChange={(event) => setNewUserFullName(event.target.value)} />
                </label>
                <label className="field">
                  <span>Email</span>
                  <input type="email" value={newUserEmail} onChange={(event) => setNewUserEmail(event.target.value)} />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input type="password" value={newUserPassword} onChange={(event) => setNewUserPassword(event.target.value)} />
                </label>
                <label className="field">
                  <span>Role</span>
                  <select value={newUserRole} onChange={(event) => setNewUserRole(event.target.value as typeof newUserRole)}>
                    <option value="admin">Admin</option>
                    <option value="analyst">Analyst</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </label>
                <label className="checkbox checkbox--inline">
                  <input checked={newUserIsActive} onChange={() => setNewUserIsActive((value) => !value)} type="checkbox" />
                  <span>Create the user as active</span>
                </label>
                <button className="button" disabled={creatingUser} onClick={createUser} type="button">
                  {creatingUser ? "Creating..." : "Create User"}
                </button>
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

function formatDate(value: string | null): string {
  if (!value) {
    return "N/A";
  }
  return new Date(value).toLocaleString();
}

function labelize(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function coverageLabel(value: string): string {
  switch (value) {
    case "ready":
      return "Ready";
    case "error":
      return "Needs Attention";
    default:
      return "Refreshing";
  }
}

function getPageCount(totalItems: number, pageSize: number): number {
  return Math.max(1, Math.ceil(totalItems / pageSize));
}

function paginateItems<T>(items: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function formatRangeLabel(totalItems: number, page: number, pageSize: number): string {
  if (totalItems === 0) {
    return "Showing 0 items";
  }
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  return `Showing ${start}-${end} of ${totalItems}`;
}
