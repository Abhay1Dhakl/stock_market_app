"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { API_BASE_URL, apiRequest } from "@/lib/api";
import { clearSession, loadSession } from "@/lib/auth";
import type {
  BehaviorSummary,
  CompanyListResponse,
  CompanySummary,
  NewsArticleSummary,
  NewsListResponse,
  TokenResponse,
} from "@/types";

type CompanyDashboardCard = {
  company: CompanySummary;
  summary: BehaviorSummary;
};

export default function DashboardPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [cards, setCards] = useState<CompanyDashboardCard[]>([]);
  const [newsItems, setNewsItems] = useState<NewsArticleSummary[]>([]);
  const [reviewQueueCount, setReviewQueueCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }

    void loadDashboard(storedSession);
  }, []);

  async function loadDashboard(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);

    try {
      const companies = await apiRequest<CompanyListResponse>("/companies", {
        token: activeSession.access_token,
      });
      const summaries = await Promise.all(
        companies.items.map(async (company) => ({
          company,
          summary: await apiRequest<BehaviorSummary>(`/companies/${company.id}/behavior-summary`, {
            token: activeSession.access_token,
          }),
        })),
      );
      const latestNews = await apiRequest<NewsListResponse>("/news?limit=8", {
        token: activeSession.access_token,
      });

      setCards(summaries);
      setNewsItems(latestNews.items);

      if (activeSession.user.role !== "viewer") {
        try {
          const reviewQueue = await apiRequest<NewsListResponse>("/news/review-queue?limit=50", {
            token: activeSession.access_token,
          });
          setReviewQueueCount(reviewQueue.items.length);
        } catch {
          setReviewQueueCount(null);
        }
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    clearSession();
    setSession(null);
    setCards([]);
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
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to export report.");
    } finally {
      setDownloadingReport(false);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Dashboard"
        description="Login is required before the dashboard can read protected company, news, and analysis endpoints."
      >
        <SectionCard title="Session Required">
          <p>Use the login page to store a JWT session in the browser, then return here.</p>
          <Link className="button" href="/login">
            Go to Login
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const anomalyCount = cards.filter(({ summary }) => summary.is_volume_anomaly).length;
  const totalTaggedNews = cards.reduce((total, { summary }) => total + summary.news_count, 0);
  const focusCompany = [...cards].sort((left, right) => right.summary.news_count - left.summary.news_count)[0] ?? null;
  const pressureSignals = cards.filter(({ summary }) => summary.pressure_indicator).length;
  const largestMover =
    [...cards]
      .map(({ company, summary }) => ({
        company,
        change: parseNumericValue(summary.price_change_pct),
      }))
      .filter((entry) => Number.isFinite(entry.change))
      .sort((left, right) => Math.abs(right.change) - Math.abs(left.change))[0] ?? null;

  return (
    <LayoutShell
      title="Cross-Company Dashboard"
      description="Compare the tracked NEPSE watchlist across closing price, VWAP, tagged news volume, pressure signals, and anomaly flags."
    >
      <div className="toolbar">
        <div className="badge">Signed in as {session.user.full_name} ({session.user.role})</div>
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
          <p>Fetching company summaries and recent tagged news.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : (
        <>
          <div className="kpi-strip">
            <div className="kpi">
              <div className="kpi__label">Tracked Companies</div>
              <div className="kpi__value">{cards.length}</div>
              <div className="kpi__note">All seeded companies currently loaded into the protected cross-company view.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Most In News</div>
              <div className="kpi__value">{focusCompany?.company.symbol ?? "N/A"}</div>
              <div className="kpi__note">Aggregate article references mapped across the latest company snapshots.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Largest Price Move</div>
              <div className="kpi__value">
                {largestMover ? `${largestMover.change > 0 ? "+" : ""}${largestMover.change.toFixed(2)}%` : "N/A"}
              </div>
              <div className="kpi__note">
                {largestMover
                  ? `${largestMover.company.symbol} has the biggest absolute price move in the latest snapshot.`
                  : "Run a crawl to populate price movement across the tracked watchlist."}
              </div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Volume Anomalies</div>
              <div className="kpi__value">{anomalyCount}</div>
              <div className="kpi__note">
                {focusCompany
                  ? `${focusCompany.summary.news_count} tagged stories make ${focusCompany.company.name} the current headline focus.`
                  : "Run a crawl to populate the dashboard and detect unusual trading activity."}
              </div>
            </div>
          </div>

          <div className="grid grid--three">
            {cards.map(({ company, summary }) => (
              <SectionCard
                key={company.id}
                eyebrow="Company"
                title={`${company.symbol} · ${company.sector}`}
                aside={<span className="badge">{summary.news_count} tagged news</span>}
              >
                <div className="metric">
                  {summary.close_price ? `Rs. ${summary.close_price}` : "No close price"}
                </div>
                <p className="muted">{company.name}</p>
                <div className="stat-row">
                  <span>VWAP</span>
                  <strong>{summary.vwap ?? "pending"}</strong>
                </div>
                <div className="stat-row">
                  <span>Pressure</span>
                  <strong>{summary.pressure_indicator ?? "pending"}</strong>
                </div>
                <div className="stat-row">
                  <span>Price Change %</span>
                  <strong>{summary.price_change_pct ?? "N/A"}</strong>
                </div>
                <div className="stat-row">
                  <span>Volume Change %</span>
                  <strong>{summary.volume_change_pct ?? "N/A"}</strong>
                </div>
                <div className="stat-row">
                  <span>Volume Anomaly</span>
                  <strong>{summary.is_volume_anomaly ? "Yes" : "No"}</strong>
                </div>
                <Link className="button" href={`/companies/${company.id}`}>
                  View Analysis
                </Link>
              </SectionCard>
            ))}
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Feed" title="Latest Tagged Headlines" aside={<span className="badge">{newsItems.length} loaded</span>}>
              {newsItems.length === 0 ? (
                <p>No crawled news is stored yet. Trigger a crawl from the admin page.</p>
              ) : (
                <div className="stack">
                  {newsItems.map((article) => (
                    <article key={article.id} className="list-card">
                      <div className="list-card__meta">
                        <span>{article.source_name}</span>
                        <span>{formatDate(article.published_at)}</span>
                      </div>
                      <a href={article.source_url} rel="noreferrer" target="_blank">
                        <strong>{article.headline}</strong>
                      </a>
                      <p>{article.excerpt ?? "No excerpt available."}</p>
                      <div className="tag-row">
                        {article.tags.map((tag) => (
                          <span key={`${article.id}-${tag.company_id}`} className="badge">
                            {tag.symbol} · {tag.confidence_score}
                          </span>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard eyebrow="Comparison" title="Cross-Company Leaders" aside={<span className="badge">{totalTaggedNews} total tags</span>}>
              <div className="stat-row">
                <span>Most In News</span>
                <strong>{focusCompany ? `${focusCompany.company.symbol} (${focusCompany.summary.news_count})` : "N/A"}</strong>
              </div>
              <div className="stat-row">
                <span>Largest Price Move</span>
                <strong>
                  {largestMover
                    ? `${largestMover.company.symbol} (${largestMover.change > 0 ? "+" : ""}${largestMover.change.toFixed(2)}%)`
                    : "N/A"}
                </strong>
              </div>
              <div className="stat-row">
                <span>Pressure Signals</span>
                <strong>{pressureSignals}</strong>
              </div>
              <div className="stat-row">
                <span>Volume Anomalies</span>
                <strong>{anomalyCount}</strong>
              </div>
              {reviewQueueCount !== null ? (
                <div className="stat-row">
                  <span>Review Queue</span>
                  <strong>{reviewQueueCount}</strong>
                </div>
              ) : null}
              <p className="muted">
                Use the company pages to inspect charts and floorsheet flow, the review page for low-confidence tags,
                and the admin page to trigger fresh crawl runs.
              </p>
            </SectionCard>
          </div>
        </>
      )}
    </LayoutShell>
  );
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleString();
}

function parseNumericValue(value: string | null): number {
  if (!value) {
    return Number.NaN;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
}
