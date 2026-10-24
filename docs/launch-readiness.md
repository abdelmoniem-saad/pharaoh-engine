# Launch readiness — 24 October 2026

Recommendation: private single-player playtest; do not announce a public release yet.
This is a scoped code and interface review, not certification of every game system.

## Fixed in this pass

- Inbox rows and message details now translate known stored English templates into Arabic at display time. Existing careers benefit without rewriting their archive or transfer payloads. Daily, medical, training, standard match reports, board, finance and negotiation templates are covered. Unrecognized prose remains visible with an explicit original-language notice. User-entered names remain intact.
- Settings now prioritize language, appearance and match playback, save speed immediately, show persistence failures, and offer a real backup for active careers. Destructive career management is separated and collapsed.
- Removed misleading difficulty and autosave controls from the screen. Difficulty had no simulation consumer; the calendar already saves state every advance. Legacy fields remain compatible with existing saves.
- Transfer execution now rejects an outdated seller/player relationship before changing any balances. The inbox displays an unavailable-offer message instead of crashing. This prevents accepting the same completed offer twice while the player belongs to the buyer; it is not a complete persistent offer-lifecycle solution.

## Release gates

| Priority | Gap | Evidence / required completion |
|---|---|---|
| Must fix | Complete bilingual editorial content | The inbox uses a reviewed template catalog, not a complete bilingual event model. Unmatched random-event/cup/derby/objective text can remain English. Inventory every message producer and test generated content in both languages. A template ID plus structured parameters is the long-term solution. |
| Must fix | Durable transfer-offer lifecycle | Inbox offers embed actions in stored text (`src/ui/screens/inbox.py`). Read/unread is not accepted/declined/expired. Persist offer status and expiry, revalidate ownership and funds, and make acceptance atomic. The ownership guard in this pass fixes the immediate repeated-payment path only. |
| Must verify | Career reliability | Run multiple complete seasons, promotion/relegation, cup progression, expiring contracts, financial stress and reloads. Verify interrupted writes, backup restore and save migration on the release build. Existing unit tests do not establish these guarantees. |
| Must verify | Actual target-device experience | Test the packaged application on intended devices: small screens, Arabic long names, text scaling, keyboard navigation, resume after interruption and performance during simulation. Browser rendering is not packaging/device validation. |
| Conditional blocker | Shared web hosting | `src/ui/app.py` holds module-global app_state; locale/theme and database connections also use shared process state. Do not host independent users in one process without per-session state/storage isolation. Local single-player distribution has a different risk profile. |

## Why the experience still feels unfinished

This is a product-design judgment, not a claim that these features are entirely absent. The screens now have a shared visual system, but the next pass should strengthen the manager's decision loop:

1. A clear daily briefing: the next fixture, the most urgent squad issue, the board expectation, and one obvious next action.
2. Better decision feedback: explain why a negotiation failed, what a training change affects, and what a result means for the season. Link a relevant message directly to its task.
3. A guided first week, so a new player can select a lineup, understand tactics, play, and interpret the result without needing outside explanations.
4. A meaningful season arc: escalating objectives, visible consequences, and satisfying milestones. Validate balance with people playing complete careers before adding more menus.

Do not replace Flet merely to resolve these issues: translation coverage, durable decisions, onboarding and playtesting are product/architecture work regardless of UI framework. Reconsider it only against measured target-device performance and interaction requirements.

## Validation

152 automated tests passed after the settings, inbox and transfer guard changes. Regression coverage includes existing-message translation, English restoration, action-payload preservation, unsupported-text notices, immediate setting persistence, write failure recovery and repeat-transfer rejection. Existing all-screen theme/RTL checks remain green. Actual Arabic settings and inbox were rendered using a disposable career; screenshots are supplied separately. No official logo or endorsement is included, and the default branch remains unchanged.
