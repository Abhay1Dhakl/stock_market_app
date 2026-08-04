# Behavior Findings Summary

Date of analysis: **August 4, 2026**

This summary is based on the current local dataset produced by the live crawl pipeline in this repository. At the time of writing, the application had seeded **6 companies**, created **180 daily price rows**, stored **24 news articles**, auto-tagged **1 article**, and placed **23 articles** into the manual review queue.

## Most Interesting Observed Pattern

The strongest pattern in the current dataset is that the **market-behavior layer is already producing clear cross-company differences even when the news-categorization layer is still sparse**.

Three companies stood out for elevated volume behavior:

- `CHCL` showed the highest anomaly frequency in the current 30-session window, with **8 anomaly days** and a latest snapshot marked as **strong_buy_pressure**.
- `NTC` combined a latest **strong_sell_pressure** signal with a current volume anomaly flag, which makes it the clearest example of price weakness confirmed by activity rather than a quiet price drift.
- `SICL` also showed a latest anomaly flag, but with **strong_buy_pressure**, making it directionally different from `NTC` even though both names were unusually active.

By contrast, `SHIVM` was the cleanest “stable” example in the current sample:

- **0 anomaly days**
- latest snapshot not flagged as anomalous
- latest pressure state still positive

That creates a useful contrast for the dashboard: the pipeline can already separate names that are moving on unusual participation from names that are trending without abnormal activity.

## News And Sentiment Interpretation

The current crawl state also shows a limitation that is worth stating honestly: the **news-correlation signal is not yet strong in this sample**.

- Only **1 article** was automatically tagged with full confidence.
- **23 articles** were pushed into the review queue because the rule-based categorizer stayed conservative.
- As a result, the current company snapshots show very little same-day news alignment with trading dates.

This is not a failure of the architecture. It is mainly a consequence of:

- a narrow watchlist
- conservative rule-based tagging
- real-world article language that often mentions companies indirectly
- publication timestamps that do not always line up neatly with trading sessions

In practical terms, the current build demonstrates that the **review workflow is essential**: market-side analysis is already useful on its own, while the news layer becomes more valuable after analysts correct the ambiguous items.

## Buyer/Seller Behavior Note

The codebase supports broker aggregation, top buyers, top sellers, and net accumulation/distribution views. However, on the latest live crawl used for this summary, the source returned **no floorsheet rows**, so broker-level findings could not yet be defended from live data in this specific run.

The implementation still supports this analysis path:

- floorsheet ingestion and dedupe are implemented in the backend
- broker aggregation is computed in analysis snapshots
- the frontend company board renders buyer/seller panels when floorsheet rows exist

So the broker-analysis feature is structurally complete, but the current live evidence is limited by source availability rather than by missing application logic.

## Bottom Line

The most defensible conclusion from the present dataset is:

**the application already distinguishes abnormal trading participation across companies better than it currently distinguishes company-specific news impact, which makes the analyst review loop the key bridge between raw crawled news and stronger market interpretation.**
