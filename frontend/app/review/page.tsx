"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import { trackEvent } from "@/lib/telemetry";
import type { CompanyListResponse, CompanySummary, NewsArticleSummary, NewsListResponse, TokenResponse } from "@/types";

type SelectionState = Record<number, number[]>;
type NotesState = Record<number, string>;

export default function ReviewPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [articles, setArticles] = useState<NewsArticleSummary[]>([]);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<SelectionState>({});
  const [notes, setNotes] = useState<NotesState>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }

    void loadReviewQueue(storedSession);
  }, []);

  useEffect(() => {
    if (!session) {
      return;
    }
    void trackEvent(session, {
      event_type: "review_view",
      page_path: "/review",
    });
  }, [session]);

  async function loadReviewQueue(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const [companiesResponse, articlesResponse] = await Promise.all([
        apiRequest<CompanyListResponse>("/companies", { token: activeSession.access_token }),
        apiRequest<NewsListResponse>("/news/review-queue?limit=20", { token: activeSession.access_token }),
      ]);

      setCompanies(companiesResponse.items);
      setArticles(articlesResponse.items);

      const selection: SelectionState = {};
      for (const article of articlesResponse.items) {
        selection[article.id] = article.tags.map((tag) => tag.company_id);
      }
      setSelectedCompanyIds(selection);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load review queue.");
    } finally {
      setLoading(false);
    }
  }

  function toggleCompany(articleId: number, companyId: number) {
    setSelectedCompanyIds((current) => {
      const existing = current[articleId] ?? [];
      const next = existing.includes(companyId)
        ? existing.filter((value) => value !== companyId)
        : [...existing, companyId];
      return { ...current, [articleId]: next };
    });
  }

  async function submitReview(articleId: number) {
    if (!session) {
      return;
    }

    setError(null);
    setSuccessMessage(null);

    try {
      await apiRequest(`/news/${articleId}/recategorize`, {
        token: session.access_token,
        method: "POST",
        body: {
          company_ids: selectedCompanyIds[articleId] ?? [],
          notes: notes[articleId] ?? "",
        },
      });
      setSuccessMessage(`Updated categorization for article ${articleId}.`);
      await loadReviewQueue(session);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to update categorization.");
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Review Desk"
        description="Analyst or admin access is required before the review desk can load low-confidence or untagged news items."
      >
        <SectionCard title="Session Required">
          <p>Sign in as an analyst or administrator to review tagging decisions.</p>
          <Link className="button" href="/login">
            Go to Sign In
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const suggestedLinks = Object.values(selectedCompanyIds).reduce((total, companyIds) => total + companyIds.length, 0);

  return (
    <LayoutShell
      title="Review Desk"
      description="Validate weak matches, correct company associations, and keep the market intelligence layer trustworthy."
    >
      {loading ? (
        <SectionCard title="Loading">
          <p>Fetching review candidates and company watchlist.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : (
        <>
          {successMessage ? (
            <SectionCard eyebrow="Review" title="Updated">
              <p>{successMessage}</p>
            </SectionCard>
          ) : null}

          {articles.length === 0 ? (
            <SectionCard eyebrow="Queue" title="All Clear">
              <p>No low-confidence or untagged news items currently need review.</p>
            </SectionCard>
          ) : (
            <>
              <div className="kpi-strip">
                <div className="kpi">
                  <div className="kpi__label">Articles Pending</div>
                  <div className="kpi__value">{articles.length}</div>
                  <div className="kpi__note">Stories waiting for a human decision before the tags can be trusted.</div>
                </div>
                <div className="kpi">
                  <div className="kpi__label">Chosen Links</div>
                  <div className="kpi__value">{suggestedLinks}</div>
                  <div className="kpi__note">Company associations currently selected across the loaded review set.</div>
                </div>
                <div className="kpi">
                  <div className="kpi__label">Active Role</div>
                  <div className="kpi__value">{session.user.role}</div>
                  <div className="kpi__note">Saved corrections become the trusted label set for the affected article.</div>
                </div>
              </div>

              <div className="stack">
                {articles.map((article) => (
                  <SectionCard
                    key={article.id}
                    eyebrow={article.source_name}
                    title={article.headline}
                    aside={<span className="badge">{article.tags.length ? `${article.tags.length} tags` : "untagged"}</span>}
                  >
                    <div className="list-card__meta">
                      <span>{article.source_name}</span>
                      <span>{formatDate(article.published_at)}</span>
                      <span>Sentiment: {article.sentiment_label ?? "neutral"}</span>
                    </div>
                    <p>
                      <a href={article.source_url} rel="noreferrer" target="_blank">
                        Open source article
                      </a>
                    </p>
                    <p>{article.excerpt ?? "No excerpt is available for this story."}</p>
                    <div className="tag-row">
                      {article.tags.length ? (
                        article.tags.map((tag) => (
                          <span key={`${article.id}-${tag.company_id}`} className="badge">
                            {tag.symbol} · {tag.confidence_score} · {tag.tag_source}
                          </span>
                        ))
                      ) : (
                        <span className="badge">No tags yet</span>
                      )}
                    </div>

                    <div className="checkbox-grid">
                      {companies.map((company) => (
                        <label key={company.id} className="checkbox">
                          <input
                            checked={(selectedCompanyIds[article.id] ?? []).includes(company.id)}
                            onChange={() => toggleCompany(article.id, company.id)}
                            type="checkbox"
                          />
                          <span>
                            {company.symbol} · {company.name}
                          </span>
                        </label>
                      ))}
                    </div>

                    <label className="field">
                      <span>Reviewer Notes</span>
                      <textarea
                        rows={3}
                        placeholder="Optional rationale for the correction"
                        value={notes[article.id] ?? ""}
                        onChange={(event) =>
                          setNotes((current) => ({
                            ...current,
                            [article.id]: event.target.value,
                          }))
                        }
                      />
                    </label>

                    <button className="button" onClick={() => submitReview(article.id)} type="button">
                      Save Decision
                    </button>
                  </SectionCard>
                ))}
              </div>
            </>
          )}
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
