"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";
import { Pager } from "@/components/pager";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import { trackEvent } from "@/lib/telemetry";
import type { CompanyListResponse, CompanySummary, NewsArticleSummary, NewsListResponse, TokenResponse } from "@/types";

type SelectionState = Record<number, number[]>;
type NotesState = Record<number, string>;

const REVIEW_ARTICLES_PER_PAGE = 3;
const REVIEW_COMPANIES_PER_PAGE = 10;

export default function ReviewPage() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [articles, setArticles] = useState<NewsArticleSummary[]>([]);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<SelectionState>({});
  const [notes, setNotes] = useState<NotesState>({});
  const [articlePage, setArticlePage] = useState(1);
  const [companyPickerPage, setCompanyPickerPage] = useState(1);
  const [companySearch, setCompanySearch] = useState("");
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
      setArticlePage(1);
      setCompanyPickerPage(1);
      setCompanySearch("");

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
  const articlePageCount = getPageCount(articles.length, REVIEW_ARTICLES_PER_PAGE);
  const filteredCompanies = companies.filter((company) => matchesCompanySearch(company, companySearch));
  const companyPickerPageCount = getPageCount(filteredCompanies.length, REVIEW_COMPANIES_PER_PAGE);
  const visibleArticles = paginateItems(articles, articlePage, REVIEW_ARTICLES_PER_PAGE);
  const visibleCompanies = paginateItems(filteredCompanies, companyPickerPage, REVIEW_COMPANIES_PER_PAGE);
  const articleRangeLabel = formatRangeLabel(articles.length, articlePage, REVIEW_ARTICLES_PER_PAGE);
  const companyRangeLabel = formatRangeLabel(filteredCompanies.length, companyPickerPage, REVIEW_COMPANIES_PER_PAGE);
  const companyLookup = new Map(companies.map((company) => [company.id, company]));

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

              <SectionCard eyebrow="Selector" title="Browse Company Options" aside={<span className="badge">{filteredCompanies.length} companies</span>}>
                <div className="section-toolbar">
                  <label className="field section-toolbar__grow">
                    <span>Filter Companies</span>
                    <input
                      onChange={(event) => {
                        setCompanySearch(event.target.value);
                        setCompanyPickerPage(1);
                      }}
                      placeholder="Search by symbol or company name"
                      value={companySearch}
                    />
                  </label>
                  <div className="stack">
                    <p className="pager__summary">{companyRangeLabel}</p>
                    <Pager
                      label="Review company picker pages"
                      onPageChange={setCompanyPickerPage}
                      page={companyPickerPage}
                      totalPages={companyPickerPageCount}
                    />
                  </div>
                </div>
              </SectionCard>

              <div className="section-toolbar">
                <p className="pager__summary">{articleRangeLabel}</p>
                <Pager
                  label="Review article pages"
                  onPageChange={setArticlePage}
                  page={articlePage}
                  totalPages={articlePageCount}
                />
              </div>

              <div className="stack">
                {visibleArticles.map((article) => {
                  const selectedCompanies = (selectedCompanyIds[article.id] ?? [])
                    .map((companyId) => companyLookup.get(companyId))
                    .filter((company): company is CompanySummary => Boolean(company));

                  return (
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

                    <div className="tag-row">
                      {selectedCompanies.length ? (
                        selectedCompanies.map((company) => (
                          <span key={`${article.id}-selected-${company.id}`} className="badge badge--success">
                            Selected: {company.symbol}
                          </span>
                        ))
                      ) : (
                        <span className="badge badge--pending">No company selected yet</span>
                      )}
                    </div>

                    <p className="muted">{companyRangeLabel} in the shared company picker for this review page.</p>

                    {visibleCompanies.length === 0 ? (
                      <p className="muted">No companies match the current filter.</p>
                    ) : (
                      <div className="checkbox-grid">
                        {visibleCompanies.map((company) => (
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
                    )}

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
                  );
                })}
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

function matchesCompanySearch(company: CompanySummary, query: string): boolean {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return true;
  }

  return (
    company.symbol.toLowerCase().includes(normalizedQuery) ||
    company.name.toLowerCase().includes(normalizedQuery)
  );
}
