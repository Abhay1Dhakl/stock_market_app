"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { PriceTrendChart } from "@/components/price-trend-chart";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/auth";
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
} from "@/types";

type BrokerSummary = {
  brokerCode: string;
  boughtQuantity: number;
  soldQuantity: number;
  netQuantity: number;
  boughtAmount: number;
  soldAmount: number;
};

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

  return (
    <LayoutShell
      title={company ? `${company.symbol} Focus Board` : `Company ${companyId}`}
      description="Single-company workspace combining price action, tagged headlines, broker activity, and correlation outputs for one tracked name."
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
          <div className="kpi-strip">
            <div className="kpi">
              <div className="kpi__label">Close Price</div>
              <div className="kpi__value">{summary.close_price ? `Rs. ${summary.close_price}` : "N/A"}</div>
              <div className="kpi__note">Latest close captured in the behavior snapshot for the selected company.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">30D High / Low</div>
              <div className="kpi__value">{closePrices.length ? `${thirtyDayHigh.toFixed(2)} / ${thirtyDayLow.toFixed(2)}` : "N/A"}</div>
              <div className="kpi__note">Quick range scan from the last thirty days of close prices.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Average Volume</div>
              <div className="kpi__value">{averageVolume ? averageVolume.toLocaleString() : "N/A"}</div>
              <div className="kpi__note">Average daily traded quantity over the visible price window.</div>
            </div>
            <div className="kpi">
              <div className="kpi__label">Floorsheet Turnover</div>
              <div className="kpi__value">{totalFloorsheetTurnover ? `Rs. ${formatCompactNumber(totalFloorsheetTurnover)}` : "N/A"}</div>
              <div className="kpi__note">Approximate trade value accumulated from the loaded buyer and seller rows.</div>
            </div>
          </div>

          <div className="grid grid--three">
            <SectionCard eyebrow="Profile" title="Company">
              <div className="metric">{company.symbol}</div>
              <p>{company.name}</p>
              <p className="muted">{company.sector}</p>
            </SectionCard>
            <SectionCard eyebrow="Snapshot" title="Behavior Snapshot">
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
                <span>Price Change %</span>
                <strong>{summary.price_change_pct ?? "N/A"}</strong>
              </div>
              <div className="stat-row">
                <span>Volume Change %</span>
                <strong>{summary.volume_change_pct ?? "N/A"}</strong>
              </div>
            </SectionCard>
            <SectionCard eyebrow="Floorsheet" title="Broker Signal">
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
                <p>No floorsheet-derived broker signal is available yet.</p>
              )}
              <div className="stat-row">
                <span>Tracked Brokers</span>
                <strong>{topBrokerCount}</strong>
              </div>
            </SectionCard>
          </div>

          <div className="grid grid--two">
            <SectionCard eyebrow="Price Action" title="30 Day Trend" aside={<span className="badge">{priceSeries.length} sessions</span>}>
              <PriceTrendChart points={priceSeries} />
              <div className="grid grid--two">
                <div className="stat-row">
                  <span>Latest Close</span>
                  <strong>{summary.close_price ? `Rs. ${summary.close_price}` : "N/A"}</strong>
                </div>
                <div className="stat-row">
                  <span>Average Volume</span>
                  <strong>{averageVolume ? averageVolume.toLocaleString() : "N/A"}</strong>
                </div>
              </div>
            </SectionCard>

            <SectionCard eyebrow="Broker Flow" title="Buyer / Seller Analysis" aside={<span className="badge">{brokerSummaries.length} brokers</span>}>
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
                      <p className="muted">No buyer data available yet.</p>
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
                      <p className="muted">No seller data available yet.</p>
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
                      <p className="muted">No net accumulators identified.</p>
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
                      <p className="muted">No net distributors identified.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="stat-row">
                <span>Total Floorsheet Quantity</span>
                <strong>{totalFloorsheetQuantity.toLocaleString()}</strong>
              </div>
            </SectionCard>
          </div>

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

            <SectionCard eyebrow="News Feed" title="Recent Tagged News" aside={<span className="badge">{newsItems.length} items</span>}>
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
            <SectionCard eyebrow="Execution Tape" title="Floorsheet Sample">
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

            <SectionCard eyebrow="Analysis" title="News / Price Correlation">
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

function parseNumericValue(value: string): number {
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
