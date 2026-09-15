# v50

- ICA product parser no longer requires price to be a direct sibling of product identity.
- Traverses all product-shaped dictionaries inside productGroups and lets normalization read nested prices.
- GitHub Actions now fails hard if zero fresh products are parsed; a green run therefore means price data was actually produced.
- Retains v49 shopping-list, branding, duplicate and non-purchase fixes.
