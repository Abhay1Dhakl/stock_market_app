"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import type {
  BehaviorSummary,
  CompanyFloorsheetResponse,
  CompanyPricesResponse,
  CompanySummary,
  NewsArticleSummary,
  NewsListResponse,
  NewsPriceCorrelationResponse,
  TokenResponse,
} from "@/types";

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const companyId = Number(params.id);
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [company, setCompany] = useState<CompanySummary | null>(null);
  const [prices, setPrices] = useState<CompanyPricesResponse | null>(null);
  const [floorsheet, setFloorsheet] = useState<CompanyFloorsheetResponse | null>(null);
  const [summary, setSummary] = useState<BehaviorSummary | null>(null);
  const [correlation, setCorrelation] = useState<NewsPriceCorrelationResponse | null>(null);
  const [newsItems, setNewsItems] = useState<NewsArticleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }

    void loadCompany(storedSession);
  }, [companyId]);

  async function loadCompany(activeSession: TokenResponse) {
    setLoading(true);
    setError(null);

    try {
      const [companyResponse, pricesResponse, floorsheetResponse, summaryResponse, correlationResponse, newsResponse] =
        await Promise.all([
          apiRequest<CompanySummary>(`/companies/${companyId}`, { token: activeSession.access_token }),
          apiRequest<CompanyPricesResponse>(`/companies/${companyId}/prices?range=30d`, {
            token: activeSession.access_token,
          }),
          apiRequest<CompanyFloorsheetResponse>(`/companies/${companyId}/floorsheet`, {
            token: activeSession.access_token,
          }),
          apiRequest<BehaviorSummary>(`/companies/${companyId}/behavior-summary`, {
            token: activeSession.access_token,
          }),
          apiRequest<NewsPriceCorrelationResponse>(`/companies/${companyId}/news-price-correlation`, {
            token: activeSession.access_token,
          }),
          apiRequest<NewsListResponse>(`/news?company_id=${companyId}&limit=15`, {
            token: activeSession.access_token,
          }),
        ]);

      setCompany(companyResponse);
      setPrices(pricesResponse);
      setFloorsheet(floorsheetResponse);
      setSummary(summaryResponse);
      setCorrelation(correlationResponse);
      setNewsItems(newsResponse.items);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to load company details.");
    } finally {
      setLoading(false);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Company Detail"
        description="A stored session is required before this page can call protected company and analysis endpoints."
      >
        <SectionCard title="Session Required">
          <p>Login first, then return to the dashboard and open a company from there.</p>
          <Link className="button" href="/login">
            Go to Login
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  return (
    <LayoutShell
      title={company ? `${company.symbol} Detail` : `Company ${companyId}`}
      description="Price history, tagged news, broker activity, and behavior-analysis outputs for a single tracked company."
    >
      {loading ? (
        <SectionCard title="Loading">
          <p>Fetching company detail, market data, and analysis snapshots.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : company && summary && prices && floorsheet && correlation ? (
        <>
          <div className="grid grid--three">
            <SectionCard title="Company">
              <div className="metric">{company.symbol}</div>
              <p>{company.name}</p>
              <p className="muted">{company.sector}</p>
            </SectionCard>
            <SectionCard title="Behavior Snapshot">
              <div className="stat-row">
                <span>Close Price</span>
                <strong>{summary.close_price ? `Rs. ${summary.close_price}` : "N/A"}</strong>
              </div>
              <div className="stat-row">
                <span>VWAP</span>
                <strong>{summary.vwap ?? "N/A"}</strong>
              </div>
              <div className="stat-row">
                <span>Pressure</span>
                <strong>{summary.pressure_indicator ?? "pending"}</strong>
              </div>
              <div className="stat-row">
                <span>News Count</span>
                <strong>{summary.news_count}</strong>
              </div>
            </SectionCard>
            <SectionCard title="Broker Signal">
              {summary.snapshot_payload.top_brokers?.length ? (
                <div className="stack">
                  {summary.snapshot_payload.top_brokers.map((broker) => (
                    <div key={broker.broker_code} className="stat-row">
                      <span>Broker {broker.broker_code}</span>
                      <strong>{broker.net_quantity}</strong>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No floorsheet-derived broker signal is available yet.</p>
              )}
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard title="Recent Price History">
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Open</th>
                      <th>Close</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prices.items.slice(-10).map((row) => (
                      <tr key={row.trading_date}>
                        <td>{row.trading_date}</td>
                        <td>{row.open_price}</td>
                        <td>{row.close_price}</td>
                        <td>{row.high_price}</td>
                        <td>{row.low_price}</td>
                        <td>{row.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>

            <SectionCard title="Recent Tagged News">
              {newsItems.length === 0 ? (
                <p>No tagged articles are stored for this company yet.</p>
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
                    </article>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard title="Floorsheet Sample">
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Buyer</th>
                      <th>Seller</th>
                      <th>Qty</th>
                      <th>Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {floorsheet.items.slice(0, 12).map((row, index) => (
                      <tr key={`${row.trading_date}-${row.buyer_broker_code}-${index}`}>
                        <td>{row.trading_date}</td>
                        <td>{row.buyer_broker_code}</td>
                        <td>{row.seller_broker_code}</td>
                        <td>{row.quantity.toLocaleString()}</td>
                        <td>{row.rate}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>

            <SectionCard title="News/Price Correlation">
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>News</th>
                      <th>Sentiment</th>
                      <th>Next-Day Price %</th>
                      <th>Next-Day Volume %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {correlation.items.slice(-10).map((row) => (
                      <tr key={row.trading_date}>
                        <td>{row.trading_date}</td>
                        <td>{row.news_count}</td>
                        <td>{row.news_sentiment_score ?? "0.0000"}</td>
                        <td>{row.next_day_price_change_pct ?? "N/A"}</td>
                        <td>{row.next_day_volume_change_pct ?? "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          </div>
        </>
      ) : null}
    </LayoutShell>
  );
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleString();
}
