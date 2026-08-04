"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
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

  return (
    <LayoutShell
      title="Cross-Company Dashboard"
      description="Live dashboard across the seeded NEPSE watchlist using crawled news, market data, categorization, and analysis snapshots."
    >
      <div className="toolbar">
        <div className="badge">
          Signed in as {session.user.full_name} ({session.user.role})
        </div>
        <button className="button button--ghost" onClick={handleLogout} type="button">
          Log Out
        </button>
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
          <div className="grid grid--three">
            {cards.map(({ company, summary }) => (
              <SectionCard key={company.id} title={`${company.symbol} · ${company.sector}`}>
                <div className="metric">
                  {summary.close_price ? `Rs. ${summary.close_price}` : "No close price"}
                </div>
                <p className="muted">{company.name}</p>
                <div className="stat-row">
                  <span>Pressure</span>
                  <strong>{summary.pressure_indicator ?? "pending"}</strong>
                </div>
                <div className="stat-row">
                  <span>News Count</span>
                  <strong>{summary.news_count}</strong>
                </div>
                <div className="stat-row">
                  <span>Volume Anomaly</span>
                  <strong>{summary.is_volume_anomaly ? "Yes" : "No"}</strong>
                </div>
                <Link className="button" href={`/companies/${company.id}`}>
                  Open Company View
                </Link>
              </SectionCard>
            ))}
          </div>

          <div className="grid grid--two">
            <SectionCard title="Recent Tagged News">
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
                      <strong>{article.headline}</strong>
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

            <SectionCard title="Operational Summary">
              <div className="stat-row">
                <span>Tracked Companies</span>
                <strong>{cards.length}</strong>
              </div>
              <div className="stat-row">
                <span>Latest News Loaded</span>
                <strong>{newsItems.length}</strong>
              </div>
              {reviewQueueCount !== null ? (
                <div className="stat-row">
                  <span>Needs Review</span>
                  <strong>{reviewQueueCount}</strong>
                </div>
              ) : null}
              <p className="muted">
                Use the review page for low-confidence tags and the admin page to run full crawls inline or through
                Celery.
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
