"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
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
        title="Review Queue"
        description="Analyst/admin access is required before this page can load low-confidence or uncategorized news items."
      >
        <SectionCard title="Session Required">
          <p>Login as an analyst or admin and return here.</p>
          <Link className="button" href="/login">
            Go to Login
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  return (
    <LayoutShell
      title="Review Queue"
      description="Analyst workspace for low-confidence or uncategorized articles. Manual corrections are preserved over future system tagging."
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
            <SectionCard title="Updated">
              <p>{successMessage}</p>
            </SectionCard>
          ) : null}

          {articles.length === 0 ? (
            <SectionCard title="Queue Empty">
              <p>No low-confidence or uncategorized news items currently need analyst review.</p>
            </SectionCard>
          ) : (
            <div className="stack">
              {articles.map((article) => (
                <SectionCard key={article.id} title={article.headline}>
                  <div className="list-card__meta">
                    <span>{article.source_name}</span>
                    <span>{formatDate(article.published_at)}</span>
                    <span>Sentiment: {article.sentiment_label ?? "neutral"}</span>
                  </div>
                  <p>{article.excerpt ?? "No excerpt available."}</p>
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
                    Save Correction
                  </button>
                </SectionCard>
              ))}
            </div>
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
