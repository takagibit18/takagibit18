# Implementation status — 2026-09-16

## Delivered

- Repo-root README replacement; original project, retrieval-evaluation, experience, capability and Now sections retained. Those claims/numbers are inherited content, not newly revalidated results.
- Desktop and mobile photographic headers; exact Homepage contact image reused.
- Self-contained animated SVG calendar variants: dark/light, desktop/mobile; corresponding still fallbacks.
- Dependency-free static activity site: hover, pin/unpin, keyboard navigation, mobile tap/scroll, theme toggle, pause/replay and reduced-motion support.
- Atomic staged generation of data/JS/SVG outputs; no overwrite on fetch/validation failure. Workflow commits outputs together.
- Scheduled update workflow and optional Pages deployment workflow; downstream deployment explicitly handles GITHUB_TOKEN-generated commits.
- Explicit unavailable production state plus isolated, labeled demonstration values. Production publisher rejects demonstration snapshots.

## Verified in this environment

- 19 Python unit tests passed: week alignment, year boundary, leap day, contiguous coverage, duplicate/negative/bool counts, total reconciliation, zero-level consistency, demo publishing rejection, unavailable vs zero, all-zero calendars, SVG XML/date uniqueness, mobile full-year coverage, JSON/JS agreement, GraphQL normalization/errors, script-string escaping.
- 11 browser checks passed: unavailable state; demo disclosure; tooltip/count mapping; pin/Escape; keyboard week/day/end navigation; pause/replay; light theme; reduced motion; leaving demo; 390px touch behavior/no body overflow; no browser page errors.
- SVG verified as an `img` resource: captures at different times differed with animation on; captures were identical with the outer picture element selecting the still fallback in reduced-motion mode.
- Desktop dark/light and mobile renderings inspected. Browser tests used in-memory, self-contained page rendering. They do NOT constitute a deployed GitHub/Pages end-to-end test, nor a Windows file-open test.
- Original image SHA verified against the Homepage repository asset before recompression/cropping.

## Not yet verified / not performed

- No GitHub repository writes, commits, pushes, settings changes or Pages deployment were performed.
- Full current contribution history could not be retrieved in this authoring environment. The first successful Actions run must populate real data. No synthetic values were passed off as personal activity.
- Authentication, repository write permissions, branch protection, Actions execution and GitHub's hosted README image proxy are untested in the target repository. Check them after upload.
- The deployed URL is not known until Pages succeeds. The README therefore does not prematurely point at an unverified Pages URL.
- User's own-server hosting is supported as a static-file target but has not been configured or deployed.

## Source provenance

Original background repository path:
`takagibit18/Homepage/assets/contact-night-city.png`

Original Git blob SHA:
`59191fef217baf5907d747dfc65f72d491106835`

Recovered from the user's Library image “深夜都市窗前的静谧工作时光.png”. Verified 1,393,157 original bytes and exact Git blob SHA equality. This is the existing background asset, not a new generated scene or a person identified from an image.

README source reviewed:
`takagibit18/takagibit18/README.md`, blob `97c20e5a09a7c266d0df78611337dfd62b6831f1`.

Typography is baked into banner image pixels using installed fonts. No font files are redistributed. The website uses system fonts and no external font service.

## Design contract

One activity calendar on the page; CSS grid/HTML buttons own geometry and interaction. Original image is restricted to the header, not painted beneath quantitative data. Count-to-fill mapping is unchanged by animation; focus/pinning has a separate border treatment. Date, count and demo/source state remain accessible without hover via the persistent details and day list. Mobile uses an internal horizontally scrollable calendar with readable touch targets and preserves all dates. No analytics, runtime API calls, third-party chart bundle, backend or database.
