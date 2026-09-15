# v52

- ICA Handla product search now uses the documented `maxPageSize=60`.
- Each anonymous search session bootstraps the selected Maxi ICA Växjö store page first.
- HTTP 200 responses with productGroups but empty decoratedProducts are treated as asynchronous/not-ready and retried, like ICA 202 responses, instead of being misclassified as a parser error.
- Reduced concurrency to avoid creating many simultaneous asynchronous ICA searches.
- Price step still fails hard if no real products are produced.
