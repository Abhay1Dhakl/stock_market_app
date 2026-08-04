export type UserProfile = {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  last_login_at: string | null;
  role: "admin" | "analyst" | "viewer";
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: UserProfile;
};

export type CompanySummary = {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  aliases: string[];
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CompanyListResponse = {
  items: CompanySummary[];
};

export type DailyPrice = {
  trading_date: string;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
  volume: number;
  turnover: string;
  source_name: string | null;
};

export type CompanyPricesResponse = {
  company_id: number;
  range: string;
  items: DailyPrice[];
};

export type FloorsheetTransaction = {
  trading_date: string;
  transaction_time: string | null;
  buyer_broker_code: string;
  seller_broker_code: string;
  quantity: number;
  rate: string;
  amount: string;
  source_name: string | null;
};

export type CompanyFloorsheetResponse = {
  company_id: number;
  date: string | null;
  items: FloorsheetTransaction[];
};

export type TaggedCompanySummary = {
  company_id: number;
  symbol: string;
  name: string;
  confidence_score: string;
  tag_source: string;
  match_summary: string | null;
};

export type NewsArticleSummary = {
  id: number;
  source_name: string;
  source_url: string;
  headline: string;
  excerpt: string | null;
  published_at: string | null;
  crawled_at: string;
  sentiment_label: string | null;
  tags: TaggedCompanySummary[];
};

export type NewsListResponse = {
  company_id?: number | null;
  items: NewsArticleSummary[];
};

export type BehaviorSummary = {
  company_id: number;
  trading_date: string | null;
  close_price: string | null;
  vwap: string | null;
  price_change_pct: string | null;
  volume_change_pct: string | null;
  pressure_indicator: string | null;
  is_volume_anomaly: boolean;
  anomaly_threshold: string | null;
  news_count: number;
  news_sentiment_score: string | null;
  next_day_price_change_pct: string | null;
  next_day_volume_change_pct: string | null;
  snapshot_payload: {
    top_brokers?: Array<{ broker_code: string; net_quantity: number }>;
    news_headlines?: string[];
    window_close_prices?: number[];
    window_volumes?: number[];
    floorsheet_trade_count?: number;
  };
};

export type CorrelationPoint = {
  trading_date: string;
  news_count: number;
  news_sentiment_score: string | null;
  next_day_price_change_pct: string | null;
  next_day_volume_change_pct: string | null;
};

export type NewsPriceCorrelationResponse = {
  company_id: number;
  items: CorrelationPoint[];
};

export type CrawlRunResponse = {
  id: number;
  run_kind: string;
  status: string;
  requested_sources: string[];
  error_message: string | null;
  run_stats: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  triggered_by_user_id: number | null;
  requested_by: string | null;
};

export type CrawlRunListResponse = {
  items: CrawlRunResponse[];
};

export type UserSummary = {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  role: string;
  last_login_at: string | null;
};

export type UserListResponse = {
  items: UserSummary[];
};
