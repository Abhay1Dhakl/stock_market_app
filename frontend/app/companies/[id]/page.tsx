"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { PriceTrendChart } from "@/components/price-trend-chart";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
import { trackEvent } from "@/lib/telemetry";
import type {
  BehaviorSummary,
  CompanyFloorsheetResponse,
  CompanyPricesResponse,
  CompanySummary,
  FloorsheetTransaction,
  NewsArticleSummary,
  NewsListResponse,
  NewsPriceCorrelationResponse,
  TokenResponse,
  UserWatchlistResponse,
} from "@/types";

type BrokerSummary = {
  brokerCode: string;
  boughtQuantity: number;
  soldQuantity: number;
  netQuantity: number;
  boughtAmount: number;
  soldAmount: number;
};

type CompanyTabKey = "overview" | "flow" | "news" | "data";

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
  const [isTracked, setIsTracked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [savingWatchlist, setSavingWatchlist] = useState(false);
  const [activeTab, setActiveTab] = useState<CompanyTabKey>("overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedSession = loadSession();
    setSession(storedSession);
    if (!storedSession) {
      setLoading(false);
      return;
    }

    async function loadCompany(activeSession: TokenResponse) {
      setLoading(true);
      setError(null);

      try {
        const [
          companyResponse,
          pricesResponse,
          floorsheetResponse,
          summaryResponse,
          correlationResponse,
          newsResponse,
          watchlistResponse,
        ] = await Promise.all([
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
          apiRequest<NewsListResponse>(`/news?company_id=${companyId}&limit=12`, {
            token: activeSession.access_token,
          }),
          apiRequest<UserWatchlistResponse>("/users/me/watchlist", {
            token: activeSession.access_token,
          }),
        ]);

        setCompany(companyResponse);
        setPrices(pricesResponse);
        setFloorsheet(floorsheetResponse);
        setSummary(summaryResponse);
        setCorrelation(correlationResponse);
        setNewsItems(newsResponse.items);
        setIsTracked(watchlistResponse.items.some((item) => item.company.id === companyId));
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Unable to load company details.");
      } finally {
        setLoading(false);
      }
    }

    void loadCompany(storedSession);
  }, [companyId]);

  useEffect(() => {
    if (!session) {
      return;
    }
    void trackEvent(session, {
      event_type: "company_view",
      page_path: `/companies/${companyId}`,
      company_id: companyId,
    });
  }, [companyId, session]);

  useEffect(() => {
    setActiveTab("overview");
  }, [companyId]);

  async function toggleWatchlist() {
    if (!session || !company) {
      return;
    }

    setSavingWatchlist(true);
    setError(null);

    try {
      if (isTracked) {
        await apiRequest(`/users/me/watchlist/${company.id}`, {
          token: session.access_token,
          method: "DELETE",
        });
      } else {
        await apiRequest("/users/me/watchlist", {
          token: session.access_token,
          method: "POST",
          body: { company_id: company.id },
        });
      }
      setIsTracked(!isTracked);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to update your watchlist.");
    } finally {
      setSavingWatchlist(false);
    }
  }

  if (!session) {
    return (
      <LayoutShell
        title="Company Detail"
        description="A stored session is required before this page can call protected company, news, and analysis endpoints."
      >
        <SectionCard title="Session Required">
          <p>Sign in first, then return to the market desk and open a company from there.</p>
          <Link className="button" href="/login">
            Go to Sign In
          </Link>
        </SectionCard>
      </LayoutShell>
    );
  }

  const topBrokerCount = summary?.snapshot_payload.top_brokers?.length ?? 0;
  const priceSeries =
    prices?.items
      .map((row) => ({
        trading_date: row.trading_date,
        close_price: parseNumericValue(row.close_price),
        volume: row.volume,
      }))
      .filter((row) => Number.isFinite(row.close_price)) ?? [];
  const closePrices = priceSeries.map((row) => row.close_price);
  const thirtyDayHigh = closePrices.length ? Math.max(...closePrices) : 0;
  const thirtyDayLow = closePrices.length ? Math.min(...closePrices) : 0;
  const averageVolume = priceSeries.length
    ? Math.round(priceSeries.reduce((total, row) => total + row.volume, 0) / priceSeries.length)
    : 0;

  const brokerSummaries = aggregateBrokerRows(floorsheet?.items ?? []);
  const topBuyers = [...brokerSummaries].sort((left, right) => right.boughtQuantity - left.boughtQuantity).slice(0, 5);
  const topSellers = [...brokerSummaries].sort((left, right) => right.soldQuantity - left.soldQuantity).slice(0, 5);
  const netAccumulation = [...brokerSummaries].filter((row) => row.netQuantity > 0).sort((left, right) => right.netQuantity - left.netQuantity).slice(0, 5);
  const netDistribution = [...brokerSummaries].filter((row) => row.netQuantity < 0).sort((left, right) => left.netQuantity - right.netQuantity).slice(0, 5);
  const totalFloorsheetTurnover = floorsheet?.items.reduce((total, row) => total + parseNumericValue(row.amount), 0) ?? 0;
  const totalFloorsheetQuantity = floorsheet?.items.reduce((total, row) => total + row.quantity, 0) ?? 0;
  const latestHeadline = newsItems[0] ?? null;
  const tabs: Array<{
    key: CompanyTabKey;
    label: string;
    note: string;
  }> = [
    {
      key: "overview",
      label: "Overview",
      note: "Signals, chart, and coverage health",
    },
    {
      key: "flow",
      label: "Broker Flow",
      note: "Buyer, seller, and tape concentration",
    },
    {
      key: "news",
      label: "News",
      note: "Headlines and price impact context",
    },
    {
      key: "data",
      label: "Market Data",
      note: "Raw price and transaction tables",
    },
  ];

  return (
    <LayoutShell
      title={company ? `${company.symbol} · ${company.name}` : `Company ${companyId}`}
      description="Study price behavior, broker positioning, linked headlines, and coverage health for a single tracked company."
    >
      {loading ? (
        <SectionCard title="Loading">
          <p>Loading price history, broker flow, and related market context.</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="Error">
          <p>{error}</p>
        </SectionCard>
      ) : company && summary && prices && floorsheet && correlation ? (
        <>
          <div className="toolbar">
            <div className="toolbar__copy">
              <div className="tag-row">
                <span className="badge">{company.sector}</span>
                <span className={`badge badge--${statusTone(company.coverage_status)}`}>
                  {coverageLabel(company.coverage_status)}
                </span>
                <span className="badge">{labelize(company.source_kind)}</span>
              </div>
              <p className="muted">
                {company.coverage_status === "error"
                  ? company.last_refresh_error ?? "Coverage refresh needs attention."
                  : company.last_refresh_at
                    ? `Last refreshed ${formatDate(company.last_refresh_at)}.`
                    : "Coverage refresh has not completed yet."}
              </p>
            </div>
            <div className="tag-row">
              <button className="button button--ghost" disabled={savingWatchlist} onClick={toggleWatchlist} type="button">
                {savingWatchlist ? "Saving..." : isTracked ? "Remove From Watchlist" : "Add To Watchlist"}
              </button>
              <Link className="button button--ghost" href="/dashboard">
                Back To Market Desk
              </Link>
            </div>
          </div>

          <div className="kpi-strip">
            <div className="kpi">
              <div className="kpi__label">Close Price</div>
              <div className="kpi__value">{summary.close_price ? `Rs. ${summary.close_price}` : "Pending"}</div>
              <div className="kpi__note">Latest stored close in the company analysis snapshot.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">30D High / Low</div>
              <div className="kpi__value">{closePrices.length ? `${thirtyDayHigh.toFixed(2)} / ${thirtyDayLow.toFixed(2)}` : "N/A"}</div>
              <div className="kpi__note">A quick range view of the visible thirty-session history.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Average Volume</div>
              <div className="kpi__value">{averageVolume ? averageVolume.toLocaleString() : "N/A"}</div>
              <div className="kpi__note">Average daily traded quantity across the current chart window.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Tagged News</div>
              <div className="kpi__value">{summary.news_count}</div>
              <div className="kpi__note">News items linked to this company inside the current stored snapshot.</div>
            </div>
          </div>

          <div className="tab-strip" role="tablist" aria-label="Company analysis sections">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                aria-selected={activeTab === tab.key}
                className={`tab-strip__button${activeTab === tab.key ? " tab-strip__button--active" : ""}`}
                onClick={() => setActiveTab(tab.key)}
                role="tab"
                type="button"
              >
                <span>{tab.label}</span>
                <small>{tab.note}</small>
              </button>
            ))}
          </div>

          {activeTab === "overview" ? (
            <>
              <div className="grid grid--three">
                <SectionCard eyebrow="Profile" title="Coverage Profile">
                  <div className="metric">{company.symbol}</div>
                  <p>{company.name}</p>
                  <p className="muted">{company.description ?? `${company.sector} coverage with dynamic watchlist support.`}</p>
                </SectionCard>

                <SectionCard eyebrow="Signal" title="Price And Pressure">
                  <div className="stat-row">
                    <span>VWAP</span>
                    <strong>{summary.vwap ?? "Pending"}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Pressure</span>
                    <strong>{summary.pressure_indicator ? labelize(summary.pressure_indicator) : "Pending"}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Price Change</span>
                    <strong>{summary.price_change_pct ?? "N/A"}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Volume Change</span>
                    <strong>{summary.volume_change_pct ?? "N/A"}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Anomaly Flag</span>
                    <strong>{summary.is_volume_anomaly ? "Triggered" : "Clear"}</strong>
                  </div>
                </SectionCard>

                <SectionCard eyebrow="Broker" title="Top Net Positions">
                  {summary.snapshot_payload.top_brokers?.length ? (
                    <div className="stack">
                      {summary.snapshot_payload.top_brokers.map((broker) => (
                        <div key={broker.broker_code} className="stat-row">
                          <span>Broker {broker.broker_code}</span>
                          <strong>{broker.net_quantity.toLocaleString()}</strong>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="muted">No stored broker summary is available yet.</p>
                  )}
                  <div className="stat-row">
                    <span>Tracked Brokers</span>
                    <strong>{topBrokerCount}</strong>
                  </div>
                </SectionCard>
              </div>

              <div className="grid grid--two">
                <SectionCard eyebrow="Chart" title="Thirty-Day Price Trend" aside={<span className="badge">{priceSeries.length} sessions</span>}>
                  <PriceTrendChart points={priceSeries} />
                </SectionCard>

                <SectionCard eyebrow="Desk Notes" title="Coverage Health">
                  <div className="detail-grid">
                    <div className="stat-row">
                      <span>Source Kind</span>
                      <strong>{labelize(company.source_kind)}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Coverage Status</span>
                      <strong>{coverageLabel(company.coverage_status)}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Floorsheet Turnover</span>
                      <strong>{totalFloorsheetTurnover ? `Rs. ${formatCompactNumber(totalFloorsheetTurnover)}` : "N/A"}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Total Floorsheet Qty</span>
                      <strong>{totalFloorsheetQuantity.toLocaleString()}</strong>
                    </div>
                  </div>
                  <p className="muted">
                    {latestHeadline
                      ? `Latest linked headline: ${latestHeadline.headline}`
                      : "No tagged company headline is available yet. News items will appear when the crawler links them to this symbol."}
                  </p>
                </SectionCard>
              </div>
            </>
          ) : null}

          {activeTab === "flow" ? (
            <>
              <div className="grid grid--two">
                <SectionCard eyebrow="Broker Flow" title="Buyer And Seller Analysis" aside={<span className="badge">{brokerSummaries.length} brokers</span>}>
                  <div className="broker-panels">
                    <div className="broker-panel">
                      <div className="card__eyebrow">Top Buyers</div>
                      <div className="broker-list">
                        {topBuyers.length ? (
                          topBuyers.map((broker) => (
                            <div key={`buyer-${broker.brokerCode}`} className="broker-row">
                              <div>
                                <strong>Broker {broker.brokerCode}</strong>
                                <div className="muted">{broker.boughtQuantity.toLocaleString()} bought</div>
                              </div>
                              <strong className="broker-row__value broker-row__value--positive">
                                +{broker.boughtQuantity.toLocaleString()}
                              </strong>
                            </div>
                          ))
                        ) : (
                          <p className="muted">No buyer rows are available for the selected company yet.</p>
                        )}
                      </div>
                    </div>

                    <div className="broker-panel">
                      <div className="card__eyebrow">Top Sellers</div>
                      <div className="broker-list">
                        {topSellers.length ? (
                          topSellers.map((broker) => (
                            <div key={`seller-${broker.brokerCode}`} className="broker-row">
                              <div>
                                <strong>Broker {broker.brokerCode}</strong>
                                <div className="muted">{broker.soldQuantity.toLocaleString()} sold</div>
                              </div>
                              <strong className="broker-row__value broker-row__value--negative">
                                -{broker.soldQuantity.toLocaleString()}
                              </strong>
                            </div>
                          ))
                        ) : (
                          <p className="muted">No seller rows are available for the selected company yet.</p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="broker-panels">
                    <div className="broker-panel">
                      <div className="card__eyebrow">Net Accumulation</div>
                      <div className="broker-list">
                        {netAccumulation.length ? (
                          netAccumulation.map((broker) => (
                            <div key={`net-long-${broker.brokerCode}`} className="broker-row">
                              <div>
                                <strong>Broker {broker.brokerCode}</strong>
                                <div className="muted">
                                  Buy {broker.boughtQuantity.toLocaleString()} / Sell {broker.soldQuantity.toLocaleString()}
                                </div>
                              </div>
                              <strong className="broker-row__value broker-row__value--positive">
                                +{broker.netQuantity.toLocaleString()}
                              </strong>
                            </div>
                          ))
                        ) : (
                          <p className="muted">No net accumulators identified in the visible tape.</p>
                        )}
                      </div>
                    </div>

                    <div className="broker-panel">
                      <div className="card__eyebrow">Net Distribution</div>
                      <div className="broker-list">
                        {netDistribution.length ? (
                          netDistribution.map((broker) => (
                            <div key={`net-short-${broker.brokerCode}`} className="broker-row">
                              <div>
                                <strong>Broker {broker.brokerCode}</strong>
                                <div className="muted">
                                  Buy {broker.boughtQuantity.toLocaleString()} / Sell {broker.soldQuantity.toLocaleString()}
                                </div>
                              </div>
                              <strong className="broker-row__value broker-row__value--negative">
                                {broker.netQuantity.toLocaleString()}
                              </strong>
                            </div>
                          ))
                        ) : (
                          <p className="muted">No net distributors identified in the visible tape.</p>
                        )}
                      </div>
                    </div>
                  </div>
                </SectionCard>

                <SectionCard eyebrow="Tape Summary" title="Where Activity Is Concentrating">
                  <div className="detail-grid">
                    <div className="stat-row">
                      <span>Floorsheet Turnover</span>
                      <strong>{totalFloorsheetTurnover ? `Rs. ${formatCompactNumber(totalFloorsheetTurnover)}` : "N/A"}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Total Quantity</span>
                      <strong>{totalFloorsheetQuantity.toLocaleString()}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Largest Buyer</span>
                      <strong>{topBuyers[0] ? `Broker ${topBuyers[0].brokerCode}` : "N/A"}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Largest Seller</span>
                      <strong>{topSellers[0] ? `Broker ${topSellers[0].brokerCode}` : "N/A"}</strong>
                    </div>
                  </div>
                  <p className="muted">
                    Use this section when you want to understand who is accumulating, who is distributing, and whether the tape
                    supports the price move shown in the overview.
                  </p>
                </SectionCard>
              </div>
            </>
          ) : null}

          {activeTab === "news" ? (
            <div className="grid grid--two">
              <SectionCard eyebrow="News" title="Company News Feed" aside={<span className="badge">{newsItems.length} items</span>}>
                {newsItems.length === 0 ? (
                  <p className="muted">No tagged articles are stored for this company yet.</p>
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
                        <p>{article.excerpt ?? "No summary is available for this article."}</p>
                      </article>
                    ))}
                  </div>
                )}
              </SectionCard>

              <SectionCard eyebrow="Correlation" title="News Impact Table">
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
          ) : null}

          {activeTab === "data" ? (
            <>
              <div className="grid grid--two">
                <SectionCard eyebrow="Market Data" title="Recent Price History">
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
                          <th>Turnover</th>
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
                            <td>{row.turnover}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </SectionCard>

                <SectionCard eyebrow="Tape" title="Latest Floorsheet Transactions">
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Buyer</th>
                          <th>Seller</th>
                          <th>Qty</th>
                          <th>Rate</th>
                          <th>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {floorsheet.items.slice(0, 12).map((row, index) => (
                          <tr key={`${row.trading_date}-${row.buyer_broker_code}-${row.seller_broker_code}-${index}`}>
                            <td>{row.trading_date}</td>
                            <td>{row.buyer_broker_code}</td>
                            <td>{row.seller_broker_code}</td>
                            <td>{row.quantity.toLocaleString()}</td>
                            <td>{row.rate}</td>
                            <td>{row.amount}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </SectionCard>
              </div>
            </>
          ) : null}
        </>
      ) : null}
    </LayoutShell>
  );
}

function aggregateBrokerRows(rows: FloorsheetTransaction[]): BrokerSummary[] {
  const byBroker = new Map<string, BrokerSummary>();

  for (const row of rows) {
    const amount = parseNumericValue(row.amount);

    if (!byBroker.has(row.buyer_broker_code)) {
      byBroker.set(row.buyer_broker_code, createBrokerSummary(row.buyer_broker_code));
    }
    if (!byBroker.has(row.seller_broker_code)) {
      byBroker.set(row.seller_broker_code, createBrokerSummary(row.seller_broker_code));
    }

    const buyer = byBroker.get(row.buyer_broker_code);
    const seller = byBroker.get(row.seller_broker_code);

    if (buyer) {
      buyer.boughtQuantity += row.quantity;
      buyer.boughtAmount += amount;
      buyer.netQuantity += row.quantity;
    }

    if (seller) {
      seller.soldQuantity += row.quantity;
      seller.soldAmount += amount;
      seller.netQuantity -= row.quantity;
    }
  }

  return [...byBroker.values()];
}

function createBrokerSummary(brokerCode: string): BrokerSummary {
  return {
    brokerCode,
    boughtQuantity: 0,
    soldQuantity: 0,
    netQuantity: 0,
    boughtAmount: 0,
    soldAmount: 0,
  };
}

function parseNumericValue(value: string | null): number {
  if (!value) {
    return 0;
  }
  const parsed = Number.parseFloat(value.replaceAll(",", ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleString();
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
