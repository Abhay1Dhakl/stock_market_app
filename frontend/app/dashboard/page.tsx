"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { API_BASE_URL, apiRequest } from "@/lib/api";
import { clearSession, loadSession } from "@/lib/auth";
import { trackEvent } from "@/lib/telemetry";
import type {
  CompanyInsight,
  DiscoveryFeedResponse,
  NewsArticleSummary,
  NewsListResponse,
  TokenResponse,
  UserBehaviorSummaryResponse,
  UserWatchlistResponse,
  WatchlistMutationRequest,
} from "@/types";

export default function DashboardPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [watchlist, setWatchlist] = useState<CompanyInsight[]>([]);
  const [discovery, setDiscovery] = useState<CompanyInsight[]>([]);
  const [behavior, setBehavior] = useState<UserBehaviorSummaryResponse | null>(null);
  const [newsItems, setNewsItems] = useState<NewsArticleSummary[]>([]);
  const [reviewQueueCount, setReviewQueueCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [submittingAdd, setSubmittingAdd] = useState(false);
  const [removingCompanyId, setRemovingCompanyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [newSymbol, setNewSymbol] = useState("");
  const [newName, setNewName] = useState("");
  const [newSector, setNewSector] = useState("");
  const [newAliases, setNewAliases] = useState("");
  const [newDescription, setNewDescription] = useState("");

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }

    void loadDashboard(storedSession);
  }, []);

  useEffect(() => {
    if (!session) {
      return;
    }
    void trackEvent(session, {
      event_type: "dashboard_view",
      page_path: "/dashboard",
    });
  }, [session]);

  async function loadDashboard(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);

    try {
      const [watchlistResponse, discoveryResponse, behaviorResponse, latestNews] = await Promise.all([
        apiRequest<UserWatchlistResponse>("/users/me/watchlist", {
          token: activeSession.access_token,
        }),
        apiRequest<DiscoveryFeedResponse>("/users/me/discovery-feed", {
          token: activeSession.access_token,
        }),
        apiRequest<UserBehaviorSummaryResponse>("/users/me/behavior-summary", {
          token: activeSession.access_token,
        }),
        apiRequest<NewsListResponse>("/news?limit=24", {
          token: activeSession.access_token,
        }),
      ]);

      setWatchlist(watchlistResponse.items);
      setDiscovery(discoveryResponse.items);
      setBehavior(behaviorResponse);
      setNewsItems(latestNews.items);

      if (activeSession.user.role !== "viewer") {
        try {
          const reviewQueue = await apiRequest<NewsListResponse>("/news/review-queue?limit=20", {
            token: activeSession.access_token,
          });
          setReviewQueueCount(reviewQueue.items.length);
        } catch {
          setReviewQueueCount(null);
        }
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load the market desk.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    clearSession();
    setSession(null);
    setWatchlist([]);
    setDiscovery([]);
    setBehavior(null);
    setNewsItems([]);
    setReviewQueueCount(null);
  }

  async function downloadWatchlistReport() {
    if (!session) {
      return;
    }

    setDownloadingReport(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/reports/watchlist-summary.csv`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error(`Unable to export report (${response.status}).`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "watchlist-summary.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMessage("Watchlist report exported.");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to export report.");
    } finally {
      setDownloadingReport(false);
    }
  }

  async function handleAddWatchlist(payload: WatchlistMutationRequest) {
    if (!session) {
      return;
    }

    setSubmittingAdd(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await apiRequest("/users/me/watchlist", {
        token: session.access_token,
        method: "POST",
        body: payload,
      });
      setSuccessMessage("Company added to your watchlist.");
      resetForm();
      await loadDashboard(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to add the company.");
    } finally {
      setSubmittingAdd(false);
    }
  }

  async function handleRemoveWatchlist(companyId: number) {
    if (!session) {
      return;
    }

    setRemovingCompanyId(companyId);
    setError(null);
    setSuccessMessage(null);

    try {
      await apiRequest(`/users/me/watchlist/${companyId}`, {
        token: session.access_token,
        method: "DELETE",
      });
      setSuccessMessage("Company removed from your watchlist.");
      await loadDashboard(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to remove the company.");
    } finally {
      setRemovingCompanyId(null);
    }
  }

  async function submitCustomCompany(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload: WatchlistMutationRequest = {
      symbol: newSymbol.trim() || undefined,
      name: newName.trim() || undefined,
      sector: newSector.trim() || undefined,
      aliases: parseAliases(newAliases),
      description: newDescription.trim() || undefined,
    };
    await handleAddWatchlist(payload);
  }

  function resetForm() {
    setNewSymbol("");
    setNewName("");
    setNewSector("");
    setNewAliases("");
    setNewDescription("");
  }

  if (!session) {
    return (
      <LayoutShell
        title="Market Desk"
        description="A protected session is required to load personal watchlists, dynamic discovery, and behavior analytics."
      >
        <SectionCard title="Session Required">
          <p>Sign in to open the market desk and start building your own coverage set.</p>
          <Link className="button" href="/login">
            Go to Sign In
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const anomalyCount = watchlist.filter((item) => item.summary.is_volume_anomaly).length;
  const pendingCoverage = watchlist.filter((item) => item.company.coverage_status !== "ready").length;
  const focusCompany =
    [...watchlist]
      .sort((left, right) => right.summary.news_count - left.summary.news_count)[0] ?? null;
  const strongestMove =
    [...watchlist]
      .map((item) => ({
        company: item.company,
        change: parseNumericValue(item.summary.price_change_pct),
      }))
      .filter((item) => Number.isFinite(item.change))
      .sort((left, right) => Math.abs(right.change) - Math.abs(left.change))[0] ?? null;
  const companyLinkedNews = newsItems.filter((article) => article.tags.length > 0).slice(0, 6);
  const generalMarketNews = newsItems.filter((article) => article.tags.length === 0).slice(0, 6);

  return (
    <LayoutShell
      title="Market Desk"
      description="Manage a personal NEPSE watchlist, discover companies surfacing in the news, and understand how you are using the platform over time."
    >
      <div className="toolbar">
        <div className="toolbar__copy">
          <div className="badge">Signed in as {session.user.full_name}</div>
          <p className="muted">
            {session.user.role === "viewer"
              ? "Read-only market coverage with personal watchlist tracking."
              : `Review queue: ${reviewQueueCount ?? "N/A"} item(s) waiting for analyst attention.`}
          </p>
        </div>
        <div className="tag-row">
          <button className="button button--ghost" disabled={downloadingReport} onClick={downloadWatchlistReport} type="button">
            {downloadingReport ? "Exporting..." : "Export CSV"}
          </button>
          <button className="button button--ghost" onClick={handleLogout} type="button">
            Log Out
          </button>
        </div>
      </div>

      {loading ? (
        <SectionCard title="Loading">
          <p>Preparing your watchlist, discovery feed, and usage insights.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
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
              <div className="kpi__label">My Watchlist</div>
              <div className="kpi__value">{watchlist.length}</div>
              <div className="kpi__note">Companies you explicitly track for price, broker, and news analysis.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Discovery Feed</div>
              <div className="kpi__value">{discovery.length}</div>
              <div className="kpi__note">Active companies already surfacing in recent news but not yet in your watchlist.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Open Signals</div>
              <div className="kpi__value">{anomalyCount}</div>
              <div className="kpi__note">
                {focusCompany ? `${focusCompany.company.symbol} is carrying the heaviest news volume right now.` : "No active anomalies yet."}
              </div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Behavior Events</div>
              <div className="kpi__value">{behavior?.total_events ?? 0}</div>
              <div className="kpi__note">
                {behavior?.favorite_sector
                  ? `Your strongest usage pattern is in ${behavior.favorite_sector}.`
                  : "Behavior analytics will grow as you use the workspace."}
              </div>
            </div>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Watchlist" title="My Coverage">
              {watchlist.length === 0 ? (
                <div className="empty-state">
                  <p>No companies are in your personal watchlist yet.</p>
                  <p className="muted">Start with the discovery feed or add a symbol manually below.</p>
                </div>
              ) : (
                <div className="stack">
                  {watchlist.map((item) => (
                    <article key={item.company.id} className="list-card list-card--spacious">
                      <div className="list-card__header">
                        <div>
                          <div className="card__eyebrow">{item.company.sector}</div>
                          <h3 className="list-card__title">
                            {item.company.symbol} · {item.company.name}
                          </h3>
                        </div>
                        <div className="tag-row">
                          <span className={`badge badge--${statusTone(item.company.coverage_status)}`}>
                            {coverageLabel(item.company.coverage_status)}
                          </span>
                          <Link className="button button--ghost" href={`/companies/${item.company.id}`}>
                            Open
                          </Link>
                          <button
                            className="button button--ghost"
                            disabled={removingCompanyId === item.company.id}
                            onClick={() => handleRemoveWatchlist(item.company.id)}
                            type="button"
                          >
                            {removingCompanyId === item.company.id ? "Removing..." : "Remove"}
                          </button>
                        </div>
                      </div>

                      <div className="detail-grid">
                        <div className="stat-row">
                          <span>Coverage Source</span>
                          <strong>{labelize(item.company.source_kind)}</strong>
                        </div>
                        <div className="stat-row">
                          <span>Latest Close</span>
                          <strong>{item.summary.close_price ? `Rs. ${item.summary.close_price}` : "Pending"}</strong>
                        </div>
                        <div className="stat-row">
                          <span>Price Move</span>
                          <strong>{item.summary.price_change_pct ?? "Pending"}</strong>
                        </div>
                        <div className="stat-row">
                          <span>Tagged News</span>
                          <strong>{item.summary.news_count}</strong>
                        </div>
                      </div>

                      <p className="muted">
                        {item.company.coverage_status === "error"
                          ? item.company.last_refresh_error ?? "Coverage refresh failed for this symbol."
                          : item.recent_headline
                            ? `Latest headline: ${item.recent_headline}`
                            : "Coverage is ready. News and market data will keep updating through the crawl pipeline."}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard eyebrow="Expand Coverage" title="Add A Company">
              <form className="form" onSubmit={submitCustomCompany}>
                <label className="field">
                  <span>Symbol</span>
                  <input
                    onChange={(event) => setNewSymbol(event.target.value.toUpperCase())}
                    placeholder="Example: NICA"
                    value={newSymbol}
                  />
                </label>
                <label className="field">
                  <span>Company Name</span>
                  <input
                    onChange={(event) => setNewName(event.target.value)}
                    placeholder="Optional but recommended for a new symbol"
                    value={newName}
                  />
                </label>
                <label className="field">
                  <span>Sector</span>
                  <input
                    onChange={(event) => setNewSector(event.target.value)}
                    placeholder="Optional but recommended for a new symbol"
                    value={newSector}
                  />
                </label>
                <label className="field">
                  <span>Aliases</span>
                  <input
                    onChange={(event) => setNewAliases(event.target.value)}
                    placeholder="Comma-separated aliases"
                    value={newAliases}
                  />
                </label>
                <label className="field">
                  <span>Description</span>
                  <textarea
                    onChange={(event) => setNewDescription(event.target.value)}
                    placeholder="Optional context for the team"
                    rows={3}
                    value={newDescription}
                  />
                </label>
                <p className="muted">
                  If the symbol already exists, the platform adds it to your watchlist and refreshes coverage. If it is new,
                  the platform creates a coverage record, attempts a market refresh, and reruns analysis.
                </p>
                <button className="button" disabled={submittingAdd} type="submit">
                  {submittingAdd ? "Adding..." : "Add To Watchlist"}
                </button>
              </form>
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Discovery" title="Companies Gaining Attention">
              {discovery.length === 0 ? (
                <p className="muted">No additional companies are standing out in recent tagged news yet.</p>
              ) : (
                <div className="stack">
                  {discovery.map((item) => (
                    <article key={item.company.id} className="list-card">
                      <div className="list-card__header">
                        <div>
                          <div className="card__eyebrow">{item.company.sector}</div>
                          <h3 className="list-card__title">{item.company.symbol}</h3>
                        </div>
                        <button
                          className="button button--ghost"
                          disabled={submittingAdd}
                          onClick={() => handleAddWatchlist({ company_id: item.company.id })}
                          type="button"
                        >
                          Add
                        </button>
                      </div>
                      <p>{item.company.name}</p>
                      <div className="stat-row">
                        <span>Recent mentions</span>
                        <strong>{item.mention_count}</strong>
                      </div>
                      <p className="muted">{item.recent_headline ?? "No headline summary is stored yet."}</p>
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard eyebrow="Behavior" title="My Usage Pattern">
              <div className="detail-grid">
                <div className="stat-row">
                  <span>Total Events</span>
                  <strong>{behavior?.total_events ?? 0}</strong>
                </div>
                <div className="stat-row">
                  <span>Companies Explored</span>
                  <strong>{behavior?.companies_explored ?? 0}</strong>
                </div>
                <div className="stat-row">
                  <span>Favorite Sector</span>
                  <strong>{behavior?.favorite_sector ?? "Building..."}</strong>
                </div>
                <div className="stat-row">
                  <span>Coverage Pending</span>
                  <strong>{pendingCoverage}</strong>
                </div>
              </div>

              {behavior?.top_companies.length ? (
                <div className="stack">
                  {behavior.top_companies.map((company) => (
                    <div key={company.company_id} className="stat-row">
                      <span>
                        {company.symbol} · {company.name}
                      </span>
                      <strong>{company.interactions} interactions</strong>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">Your activity profile will appear here as you open companies and manage watchlists.</p>
              )}

              {behavior?.recent_activity.length ? (
                <div className="stack">
                  {behavior.recent_activity.slice(0, 4).map((event, index) => (
                    <div key={`${event.event_type}-${event.occurred_at}-${index}`} className="stat-row">
                      <span>
                        {labelize(event.event_type)}
                        {event.company_symbol ? ` · ${event.company_symbol}` : ""}
                      </span>
                      <strong>{formatShortDate(event.occurred_at)}</strong>
                    </div>
                  ))}
                </div>
              ) : null}
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="News Desk" title="Company-Linked News" aside={<span className="badge">{companyLinkedNews.length} linked stories</span>}>
              {companyLinkedNews.length === 0 ? (
                <p className="muted">No company-linked stories are visible in the current news window yet.</p>
              ) : (
                <div className="stack">
                  {companyLinkedNews.map((article) => (
                    <article key={article.id} className="list-card">
                      <div className="list-card__meta">
                        <span>{article.source_name}</span>
                        <span>{formatShortDate(article.published_at)}</span>
                      </div>
                      <a href={article.source_url} rel="noreferrer" target="_blank">
                        <strong>{article.headline}</strong>
                      </a>
                      <div className="tag-row">
                        {article.tags.slice(0, 3).map((tag) => (
                          <Link key={`${article.id}-${tag.company_id}`} className="badge badge--success" href={`/companies/${tag.company_id}`}>
                            {tag.symbol}
                          </Link>
                        ))}
                      </div>
                      <p>{article.excerpt ?? "No summary is available for this story."}</p>
                      <p className="muted">{`Matched to ${article.tags.map((tag) => tag.symbol).join(", ")} for company analysis.`}</p>
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard eyebrow="Market Wide" title="General Market News" aside={<span className="badge">{generalMarketNews.length} broad stories</span>}>
              {generalMarketNews.length === 0 ? (
                <p className="muted">No market-wide or uncategorized stories are visible in the current news window.</p>
              ) : (
                <div className="stack">
                  {generalMarketNews.map((article) => (
                    <article key={article.id} className="list-card">
                      <div className="list-card__meta">
                        <span>{article.source_name}</span>
                        <span>{formatShortDate(article.published_at)}</span>
                      </div>
                      <a href={article.source_url} rel="noreferrer" target="_blank">
                        <strong>{article.headline}</strong>
                      </a>
                      <div className="tag-row">
                        <span className="badge badge--pending">General Market News</span>
                      </div>
                      <p>{article.excerpt ?? "No summary is available for this story."}</p>
                      <p className="muted">This story is stored, but it is not linked to a single company analysis page.</p>
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          <SectionCard eyebrow="Pulse" title="Desk Snapshot">
            <div className="detail-grid">
              <div className="stat-row">
                <span>Focus Name</span>
                <strong>{focusCompany?.company.symbol ?? "None"}</strong>
              </div>
              <div className="stat-row">
                <span>Largest Move</span>
                <strong>
                  {strongestMove ? `${strongestMove.change > 0 ? "+" : ""}${strongestMove.change.toFixed(2)}%` : "N/A"}
                </strong>
              </div>
              <div className="stat-row">
                <span>Behavior Last Seen</span>
                <strong>{behavior?.last_activity_at ? formatShortDate(behavior.last_activity_at) : "N/A"}</strong>
              </div>
              <div className="stat-row">
                <span>Review Backlog</span>
                <strong>{reviewQueueCount ?? "Viewer"}</strong>
              </div>
              <div className="stat-row">
                <span>Company-Linked News</span>
                <strong>{companyLinkedNews.length}</strong>
              </div>
              <div className="stat-row">
                <span>General Stories</span>
                <strong>{generalMarketNews.length}</strong>
              </div>
            </div>
            <p className="muted">
              Company-linked stories feed stock analysis pages. Market-wide stories stay visible here without being forced into a wrong company match.
            </p>
          </SectionCard>
        </>
      )}
    </LayoutShell>
  );
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

function statusTone(value: string): string {
  switch (value) {
    case "ready":
      return "success";
    case "error":
      return "danger";
    default:
      return "pending";
  }
}

function labelize(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function parseAliases(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseNumericValue(value: string | null): number {
  if (!value) {
    return 0;
  }
  const parsed = Number.parseFloat(value.replaceAll(",", ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatShortDate(value: string | null): string {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
