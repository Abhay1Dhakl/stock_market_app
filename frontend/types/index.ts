export type CompanySummary = {
  id: number;
  symbol: string;
  name: string;
  sector: string;
};

export type NewsItem = {
  id: number;
  headline: string;
  source: string;
  publishedAt: string;
  confidence: number;
};

export type BehaviorSummary = {
  vwap: number;
  closingPrice: number;
  pressure: string;
};

