from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="NEPSE Market Console", page_icon=":bar_chart:", layout="wide")

ROLE_LABELS = {
    "admin": "Administrator",
    "analyst": "Analyst",
    "viewer": "Viewer",
}
CRAWL_SOURCES = ["merolagani", "sharesansar"]
CRAWL_RUN_KINDS = ["full", "news", "market_data"]


def _default_api_base_url() -> str:
    secrets_value = None
    try:
        secrets_value = st.secrets.get("STREAMLIT_API_BASE_URL")
    except Exception:
        secrets_value = None

    return os.getenv("STREAMLIT_API_BASE_URL") or secrets_value or "http://localhost:8000/api"


def _inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(22, 78, 99, 0.22), transparent 28%),
                linear-gradient(180deg, #07111d 0%, #040910 100%);
        }
        .block-container {
            padding-top: 1.75rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(9, 18, 32, 0.85);
            border: 1px solid rgba(45, 212, 191, 0.18);
            border-radius: 16px;
            padding: 0.85rem 1rem;
        }
        .console-chip {
            display: inline-block;
            border: 1px solid rgba(56, 189, 248, 0.28);
            border-radius: 999px;
            padding: 0.2rem 0.65rem;
            color: #67e8f9;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }
        .console-panel {
            background: rgba(9, 18, 32, 0.88);
            border: 1px solid rgba(56, 189, 248, 0.16);
            border-radius: 20px;
            padding: 1.25rem 1.2rem;
            margin-bottom: 1rem;
        }
        .console-panel h1, .console-panel h3, .console-panel p {
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    st.session_state.setdefault("streamlit_api_base_url", _default_api_base_url())
    st.session_state.setdefault("streamlit_token", None)
    st.session_state.setdefault("streamlit_user", None)


def _headers(token: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _request_json(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> Any:
    response = requests.request(
        method=method,
        url=_build_url(base_url, path),
        headers=_headers(token),
        json=payload,
        timeout=25,
    )
    if response.status_code >= 400:
        detail = _read_error_detail(response)
        raise RuntimeError(detail or f"Request failed with status {response.status_code}.")
    if response.content:
        return response.json()
    return None


def _request_bytes(base_url: str, path: str, *, token: str | None = None) -> tuple[bytes, str]:
    response = requests.get(_build_url(base_url, path), headers=_headers(token), timeout=25)
    if response.status_code >= 400:
        detail = _read_error_detail(response)
        raise RuntimeError(detail or f"Request failed with status {response.status_code}.")

    filename = "watchlist-summary.csv"
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=", maxsplit=1)[1].strip().strip('"')

    return response.content, filename


def _read_error_detail(response: requests.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or None

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        messages: list[str] = []
        for item in detail:
            if not isinstance(item, dict):
                continue
            location = ".".join(str(part) for part in item.get("loc", [])[1:]) or "request"
            message = item.get("msg")
            if message:
                messages.append(f"{location}: {message}")
        return "; ".join(messages) or None
    if isinstance(detail, dict):
        return str(detail)
    return None


@st.cache_data(ttl=20, show_spinner=False)
def _cached_json(base_url: str, path: str, token: str) -> Any:
    return _request_json(base_url, path, token=token)


@st.cache_data(ttl=20, show_spinner=False)
def _cached_csv(base_url: str, path: str, token: str) -> tuple[bytes, str]:
    return _request_bytes(base_url, path, token=token)


def _login(email: str, password: str) -> None:
    payload = _request_json(
        st.session_state.streamlit_api_base_url,
        "auth/login",
        method="POST",
        payload={"email": email, "password": password},
    )
    st.session_state.streamlit_token = payload["access_token"]
    st.session_state.streamlit_user = payload["user"]
    _cached_json.clear()
    _cached_csv.clear()


def _logout() -> None:
    st.session_state.streamlit_token = None
    st.session_state.streamlit_user = None
    _cached_json.clear()
    _cached_csv.clear()


def _get(path: str) -> Any:
    return _cached_json(
        st.session_state.streamlit_api_base_url,
        path,
        st.session_state.streamlit_token or "",
    )


def _post(path: str, payload: dict[str, Any]) -> Any:
    result = _request_json(
        st.session_state.streamlit_api_base_url,
        path,
        token=st.session_state.streamlit_token,
        method="POST",
        payload=payload,
    )
    _cached_json.clear()
    _cached_csv.clear()
    return result


def _patch(path: str, payload: dict[str, Any]) -> Any:
    result = _request_json(
        st.session_state.streamlit_api_base_url,
        path,
        token=st.session_state.streamlit_token,
        method="PATCH",
        payload=payload,
    )
    _cached_json.clear()
    _cached_csv.clear()
    return result


def _render_login() -> None:
    st.markdown(
        """
        <div class="console-panel">
          <div class="console-chip">Streamlit Workspace</div>
          <h1>NEPSE Market Console</h1>
          <p>Sign in against the FastAPI backend to inspect watchlist coverage, news categorization, and crawl operations from a deployable Streamlit surface.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login-form", clear_on_submit=False):
        email = st.text_input("Email", value="admin@example.com")
        password = st.text_input("Password", type="password", value="admin123")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            try:
                _login(email, password)
                st.success("Session created.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_sidebar() -> str:
    role = st.session_state.streamlit_user["role"]

    with st.sidebar:
        st.caption("Backend")
        st.session_state.streamlit_api_base_url = st.text_input(
            "API base URL",
            value=st.session_state.streamlit_api_base_url,
            help="Use a public backend URL when deploying this app on Streamlit Community Cloud.",
        ).strip()

        st.divider()
        st.caption("Session")
        st.write(st.session_state.streamlit_user["full_name"])
        st.write(f"`{st.session_state.streamlit_user['email']}`")
        st.write(f"Role: `{ROLE_LABELS.get(role, role.title())}`")

        if st.button("Refresh cached data", use_container_width=True):
            _cached_json.clear()
            _cached_csv.clear()
            st.rerun()

        if st.button("Log Out", use_container_width=True):
            _logout()
            st.rerun()

        st.divider()
        pages = ["Dashboard", "Company Board", "Reports"]
        if role in {"admin", "analyst"}:
            pages.append("Review Desk")
        if role == "admin":
            pages.append("Admin Console")
        return st.radio("Workspace", options=pages, label_visibility="collapsed")


def _load_companies() -> list[dict[str, Any]]:
    payload = _get("companies")
    return payload.get("items", [])


def _behavior_summary(company_id: int) -> dict[str, Any]:
    return _get(f"companies/{company_id}/behavior-summary")


def _company_news(company_id: int) -> list[dict[str, Any]]:
    return _get(f"news?company_id={company_id}&limit=20").get("items", [])


def _render_dashboard() -> None:
    companies = _load_companies()
    summaries: list[dict[str, Any]] = []

    for company in companies:
        summary = _behavior_summary(company["id"])
        summaries.append(
            {
                "Symbol": company["symbol"],
                "Name": company["name"],
                "Sector": company["sector"],
                "Close": summary.get("close_price"),
                "VWAP": summary.get("vwap"),
                "Pressure": summary.get("pressure_indicator"),
                "Volume Anomaly": summary.get("is_volume_anomaly", False),
                "Tagged News": summary.get("news_count", 0),
                "Sentiment": summary.get("news_sentiment_score"),
            }
        )

    summary_df = pd.DataFrame(summaries)
    anomaly_count = int(summary_df["Volume Anomaly"].fillna(False).sum()) if not summary_df.empty else 0
    total_news = int(summary_df["Tagged News"].fillna(0).sum()) if not summary_df.empty else 0

    review_queue_count = None
    if st.session_state.streamlit_user["role"] in {"admin", "analyst"}:
        review_queue_count = len(_get("news/review-queue?limit=100").get("items", []))

    st.markdown(
        """
        <div class="console-panel">
          <div class="console-chip">Cross-Company View</div>
          <h1>Watchlist Situation Room</h1>
          <p>Streamlit companion dashboard for quick scanning, reporting, and review workflows backed by the same role-gated FastAPI APIs.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4 if review_queue_count is not None else 3)
    metric_columns[0].metric("Tracked Companies", len(companies))
    metric_columns[1].metric("Tagged News Signals", total_news)
    metric_columns[2].metric("Volume Anomalies", anomaly_count)
    if review_queue_count is not None:
        metric_columns[3].metric("Review Queue", review_queue_count)

    st.subheader("Coverage Snapshot")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    if not summary_df.empty:
        chart_df = summary_df[["Symbol", "Tagged News"]].set_index("Symbol")
        st.subheader("Tagged News by Company")
        st.bar_chart(chart_df)


def _render_company_board() -> None:
    companies = _load_companies()
    company_lookup = {f"{company['symbol']} | {company['name']}": company for company in companies}
    selected_label = st.selectbox("Tracked Company", options=list(company_lookup))
    company = company_lookup[selected_label]
    company_id = company["id"]

    prices = _get(f"companies/{company_id}/prices?range=30d").get("items", [])
    summary = _behavior_summary(company_id)
    news_items = _company_news(company_id)
    correlation_items = _get(f"companies/{company_id}/news-price-correlation").get("items", [])
    floorsheet_response = _get(f"companies/{company_id}/floorsheet")
    floorsheet_items = floorsheet_response.get("items", [])

    st.markdown(
        f"""
        <div class="console-panel">
          <div class="console-chip">{company['symbol']}</div>
          <h1>{company['name']}</h1>
          <p>{company['sector']} coverage with price trend, categorized news, correlation points, and broker activity from the current backend dataset.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(5)
    columns[0].metric("Close", summary.get("close_price") or "n/a")
    columns[1].metric("VWAP", summary.get("vwap") or "n/a")
    columns[2].metric("Pressure", (summary.get("pressure_indicator") or "n/a").replace("_", " "))
    columns[3].metric("Tagged News", summary.get("news_count", 0))
    columns[4].metric("Volume Anomaly", "Yes" if summary.get("is_volume_anomaly") else "No")

    price_df = pd.DataFrame(prices)
    if not price_df.empty:
        price_df["trading_date"] = pd.to_datetime(price_df["trading_date"])
        price_df["close_price"] = pd.to_numeric(price_df["close_price"])
        price_df["volume"] = pd.to_numeric(price_df["volume"])
        price_df = price_df.sort_values("trading_date")

        left, right = st.columns((2, 1))
        with left:
            st.subheader("30 Day Close Trend")
            st.line_chart(price_df.set_index("trading_date")["close_price"], use_container_width=True)
        with right:
            st.subheader("30 Day Volume Trend")
            st.bar_chart(price_df.set_index("trading_date")["volume"], use_container_width=True)
    else:
        st.info("No daily price rows are available for this company yet.")

    correlation_df = pd.DataFrame(correlation_items)
    if not correlation_df.empty:
        correlation_df["trading_date"] = pd.to_datetime(correlation_df["trading_date"])
        correlation_df = correlation_df.sort_values("trading_date")
        correlation_df["next_day_price_change_pct"] = pd.to_numeric(
            correlation_df["next_day_price_change_pct"],
            errors="coerce",
        )
        correlation_df["news_count"] = pd.to_numeric(correlation_df["news_count"], errors="coerce")
        st.subheader("News vs Next-Day Price Change")
        st.line_chart(
            correlation_df.set_index("trading_date")[["news_count", "next_day_price_change_pct"]],
            use_container_width=True,
        )

    broker_rows = summary.get("snapshot_payload", {}).get("top_brokers", [])
    news_df = pd.DataFrame(
        [
            {
                "Published": item.get("published_at"),
                "Headline": item.get("headline"),
                "Source": item.get("source_name"),
                "Sentiment": item.get("sentiment_label"),
                "Tags": ", ".join(tag["symbol"] for tag in item.get("tags", [])),
            }
            for item in news_items
        ]
    )

    left, right = st.columns((1, 1))
    with left:
        st.subheader("Recent Tagged News")
        if news_df.empty:
            st.info("No categorized news items are stored for this company yet.")
        else:
            st.dataframe(news_df, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Top Broker Net Positions")
        if broker_rows:
            st.dataframe(pd.DataFrame(broker_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No broker net-position summary is available in the latest snapshot.")

    st.subheader("Sample Floorsheet Rows")
    if floorsheet_items:
        st.dataframe(pd.DataFrame(floorsheet_items), use_container_width=True, hide_index=True)
    else:
        st.info("No floorsheet rows are available for the selected sample day.")


def _render_reports() -> None:
    st.markdown(
        """
        <div class="console-panel">
          <div class="console-chip">Export</div>
          <h1>Watchlist Report Pack</h1>
          <p>Download the server-generated CSV summary used for analyst handoff and assignment review.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    csv_bytes, filename = _cached_csv(
        st.session_state.streamlit_api_base_url,
        "reports/watchlist-summary.csv",
        st.session_state.streamlit_token or "",
    )
    preview_df = pd.read_csv(io.BytesIO(csv_bytes))
    st.download_button(
        "Download watchlist summary CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def _render_review_desk() -> None:
    queue_items = _get("news/review-queue?limit=50").get("items", [])
    companies = _load_companies()
    company_name_to_id = {f"{item['symbol']} | {item['name']}": item["id"] for item in companies}
    id_to_name = {value: key for key, value in company_name_to_id.items()}

    st.markdown(
        """
        <div class="console-panel">
          <div class="console-chip">Human Review</div>
          <h1>Low-Confidence Categorization Queue</h1>
          <p>Review ambiguous articles, override company tags, and persist the correction record into the backend.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not queue_items:
        st.success("The review queue is empty.")
        return

    option_lookup = {
        f"#{item['id']} | {item['headline']}": item
        for item in queue_items
    }
    selected_label = st.selectbox("Article", options=list(option_lookup))
    article = option_lookup[selected_label]

    st.write(f"**Source:** {article['source_name']}")
    st.write(f"**Published:** {article.get('published_at') or 'n/a'}")
    st.write(article.get("excerpt") or "No excerpt available.")
    st.write(f"[Open original article]({article['source_url']})")

    current_company_ids = [tag["company_id"] for tag in article.get("tags", [])]
    default_labels = [id_to_name[company_id] for company_id in current_company_ids if company_id in id_to_name]

    with st.form("recategorize-form"):
        selected_companies = st.multiselect(
            "Correct companies",
            options=list(company_name_to_id),
            default=default_labels,
        )
        notes = st.text_area("Review notes", placeholder="Why did you change the tags?")
        submitted = st.form_submit_button("Submit correction", use_container_width=True)
        if submitted:
            try:
                _post(
                    f"news/{article['id']}/recategorize",
                    {
                        "company_ids": [company_name_to_id[label] for label in selected_companies],
                        "notes": notes or None,
                    },
                )
                st.success("Correction saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.subheader("Queue Snapshot")
    queue_df = pd.DataFrame(
        [
            {
                "ID": item["id"],
                "Headline": item["headline"],
                "Source": item["source_name"],
                "Current Tags": ", ".join(tag["symbol"] for tag in item.get("tags", [])) or "none",
            }
            for item in queue_items
        ]
    )
    st.dataframe(queue_df, use_container_width=True, hide_index=True)


def _render_admin_console() -> None:
    st.markdown(
        """
        <div class="console-panel">
          <div class="console-chip">Admin Operations</div>
          <h1>Control Room</h1>
          <p>Trigger crawl runs, manage users, and maintain the tracked company watchlist from the Streamlit companion app.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    crawl_tab, users_tab, watchlist_tab = st.tabs(["Crawl Runs", "Users", "Watchlist"])

    with crawl_tab:
        with st.form("crawl-run-form"):
            run_kind = st.selectbox("Run kind", options=CRAWL_RUN_KINDS, index=0)
            sources = st.multiselect("Sources", options=CRAWL_SOURCES, default=CRAWL_SOURCES)
            execute_now = st.checkbox("Execute synchronously now", value=True)
            submitted = st.form_submit_button("Trigger crawl run", use_container_width=True)
            if submitted:
                try:
                    result = _post(
                        f"admin/crawl-runs?execute_now={'true' if execute_now else 'false'}",
                        {"run_kind": run_kind, "sources": sources},
                    )
                    st.success(f"Crawl run #{result['id']} created with status `{result['status']}`.")
                except Exception as exc:
                    st.error(str(exc))

        crawl_runs = _get("admin/crawl-runs").get("items", [])
        crawl_df = pd.DataFrame(crawl_runs)
        if crawl_df.empty:
            st.info("No crawl runs have been recorded yet.")
        else:
            st.dataframe(crawl_df, use_container_width=True, hide_index=True)

    with users_tab:
        with st.form("create-user-form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", options=["viewer", "analyst", "admin"], index=0)
            is_active = st.checkbox("Active", value=True)
            submitted = st.form_submit_button("Create user", use_container_width=True)
            if submitted:
                try:
                    _post(
                        "admin/users",
                        {
                            "full_name": full_name,
                            "email": email,
                            "password": password,
                            "role": role,
                            "is_active": is_active,
                        },
                    )
                    st.success("User created.")
                except Exception as exc:
                    st.error(str(exc))

        users = _get("admin/users").get("items", [])
        st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)

    with watchlist_tab:
        companies = _get("admin/companies").get("items", [])
        with st.form("create-company-form"):
            symbol = st.text_input("Symbol")
            name = st.text_input("Name")
            sector = st.text_input("Sector")
            aliases = st.text_input("Aliases", placeholder="Comma-separated aliases")
            description = st.text_area("Description")
            is_active = st.checkbox("Track company immediately", value=True)
            submitted = st.form_submit_button("Add tracked company", use_container_width=True)
            if submitted:
                try:
                    _post(
                        "admin/companies",
                        {
                            "symbol": symbol,
                            "name": name,
                            "sector": sector,
                            "aliases": [item.strip() for item in aliases.split(",") if item.strip()],
                            "description": description or None,
                            "is_active": is_active,
                        },
                    )
                    st.success("Company added to watchlist.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if companies:
            st.dataframe(pd.DataFrame(companies), use_container_width=True, hide_index=True)
            label_to_company = {f"{item['symbol']} | {item['name']}": item for item in companies}
            chosen_label = st.selectbox("Toggle tracked company status", options=list(label_to_company))
            chosen_company = label_to_company[chosen_label]
            toggle_label = "Deactivate" if chosen_company["is_active"] else "Activate"
            if st.button(toggle_label, use_container_width=True):
                try:
                    _patch(
                        f"admin/companies/{chosen_company['id']}",
                        {"is_active": not chosen_company["is_active"]},
                    )
                    st.success("Company status updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.info("No companies are in the watchlist yet.")


def main() -> None:
    _inject_theme()
    _init_state()

    if not st.session_state.streamlit_token or not st.session_state.streamlit_user:
        _render_login()
        return

    page = _render_sidebar()

    try:
        if page == "Dashboard":
            _render_dashboard()
        elif page == "Company Board":
            _render_company_board()
        elif page == "Reports":
            _render_reports()
        elif page == "Review Desk":
            _render_review_desk()
        elif page == "Admin Console":
            _render_admin_console()
    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
