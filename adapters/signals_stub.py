"""A fake signal source so the loop runs on day one.

Replace this with the real thing. A signal source is anything that can answer
"what moved this week": an intent vendor, your CRM, a scraper, product usage, a
webhook, a CSV. The only contract is `fetch() -> list[Signal]`.

Real-world wiring examples (each is a few lines in fetch()):
    - poll an intent API and map each hit to a bucket
    - read CRM stage changes since the last run
    - tail a webhook log of website visits
    - diff a watchlist of companies against a news/funding feed
"""

from brain.models import Signal


class StubSignals:
    """Returns a handful of made-up but realistic signals across all four buckets."""

    def fetch(self):
        return [
            Signal(account="northwind.io", bucket="job",
                   summary="opened a Head of RevOps role, second ops hire this quarter",
                   contact="VP Sales", url="https://example.com/job/123"),
            Signal(account="northwind.io", bucket="funding",
                   summary="raised a 12M Series A two weeks ago",
                   url="https://example.com/funding/nw"),
            Signal(account="acme-labs.com", bucket="social",
                   summary="their VP Growth posted about cold email reply rates falling",
                   contact="VP Growth"),
            Signal(account="cendar.co", bucket="company",
                   summary="announced expansion into the DACH region",
                   contact="Country Lead DACH"),
            Signal(account="quietbrook.com", bucket="social",
                   summary="liked three posts from a direct competitor of ours"),
        ]
