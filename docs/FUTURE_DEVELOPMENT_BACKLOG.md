# JotPop Future Development Backlog

These items are intentionally **not blockers for the MVP demo**, but they should be preserved for future development.

## Avatar polish

Current state: the avatar direction is now acceptable for MVP. It is visible, mysterious, and closer to the intended dark hooded traveler.

Future improvements:

- Make it slightly more character-like and less pure sigil/emblem.
- Add clearer shoulders, cloak folds, and hood depth.
- Add subtle asymmetry so it feels less like a static symbol.
- Keep it serious and premium, not childish RPG.
- Keep the base form visible from day one: `Undiscovered` must never mean invisible.

## Avatar growth wording

Current wording like `5/6 marks` can feel confusing.

Future wording candidates:

- `5 visible marks`
- `5 marks found`
- `Marked path`
- `Next mark unlocks after...`

Avoid making the user wonder whether `5/6` means level completion, avatar completion, or something else.

## Evolution clarity

Evolution should answer three questions quickly:

1. What shape is emerging?
2. What changed recently?
3. What can I unlock next?

Future improvements:

- Hide secondary details behind compact expandable cards.
- Keep Jot Trail and Next Insight in Evolution, not Feed.
- Make `Next visible change` obvious.
- Make the Pattern Map explanation shorter and more visual.
- Add enough bottom padding so the fixed footer never covers Evolution content.

## Feed personalization

Current MVP uses shuffle + anti-repetition.

Future goal:

- Rank cards by user patterns.
- Generate cards from Jots and signals.
- Avoid generic/popular deck feeling.
- Use Micro-Jots to create personalized follow-up cards.
- Keep Micro-Jots rare but high-value.

## Jot analysis engine

Future Jot analysis should detect:

- topic
- emotion
- intent
- action tendency
- growth area
- attribute signals
- repeated themes
- avoidance language
- commitment language
- self-image language

Example:

`I keep avoiding working on my portfolio, but I know it would help me leave this job.`

Could generate:

- Growth Area: Career / Software
- Pattern: avoidance + ambition conflict
- Suggested Promise: `Work 25 minutes on one portfolio section.`
- Suggested Feed card: `Would you rather spend 20 minutes improving your portfolio or researching jobs?`

## Forge evolution

Future improvements:

- Better distinction between required daily Promises and optional Feed challenges.
- Better recovery behavior after missed days.
- Clearer Forge Cooling copy.
- Weekly Forge recap.
- Promise difficulty learned per user.

## Technical debt

Before opening to many users:

- Add database migrations instead of automatic table creation.
- Replace MVP auth shortcuts with production-grade auth flow.
- Add rate limits.
- Add error tracking.
- Add automated tests for card gestures, promise selection, feed challenge insertion, and Jot saving.
- Add data export/delete features before serious public usage.
