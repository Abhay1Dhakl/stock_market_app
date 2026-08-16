from app.categorization.entity_matcher import WatchlistEntityMatcher
from app.crawlers.market_data import MarketDataCrawler
from app.models import Company


def test_entity_matcher_does_not_treat_common_lowercase_word_as_symbol():
    company = Company(
        symbol="UPPER",
        name="Upper Tamakoshi Hydropower Limited",
        sector="Hydro Power",
        aliases=["Upper Tamakoshi", "Tamakoshi"],
        description="Hydropower company",
        is_active=True,
    )

    matcher = WatchlistEntityMatcher([company])
    matches = matcher.match(
        "NEPSE Falls 7.37 Points Today as Turnover Reaches NPR 4.27 Arba",
        "NEPSE remained confined within an upper range during trading.",
    )

    assert matches == []


def test_company_directory_parser_extracts_tradeable_companies_only():
    crawler = MarketDataCrawler()
    try:
        companies = crawler.parse_company_directory_payload(
            """
            <script>
              var cmpjson = [
                {"id": 1, "symbol": "HDL", "companyname": "Himalayan Distillery Limited"},
                {"id": 2, "symbol": "8NIB2078", "companyname": "8% NIB Debenture 2078"},
                {"id": 3, "symbol": "ACECAP", "companyname": "Ace Capital Limited"}
              ];
            </script>
            """
        )
    finally:
        crawler.close()

    assert [(company.symbol, company.name) for company in companies] == [
        ("HDL", "Himalayan Distillery Limited"),
    ]


def test_entity_matcher_prefers_more_specific_overlapping_company_name():
    companies = [
        Company(
            symbol="KSBBL",
            name="Kamana Sewa Bikas Bank Limited",
            sector="Development Bank",
            aliases=["Kamana Sewa Bikas Bank"],
            description="Development bank",
            is_active=True,
        ),
        Company(
            symbol="SEWA",
            name="Sewa Bikas Bank Limited",
            sector="Development Bank",
            aliases=["Sewa Bikas Bank"],
            description="Another development bank",
            is_active=True,
        ),
    ]

    matcher = WatchlistEntityMatcher(companies)
    matches = matcher.match(
        "Kamana Sewa Bikas Bank Integrates Mobile App with Government's Taxpayer Incentive Scheme",
        "Kamana Sewa Bikas Bank Limited has integrated a feature into its mobile banking application.",
    )

    assert [match.company_symbol for match in matches] == ["KSBBL"]
