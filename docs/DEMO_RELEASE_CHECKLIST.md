# JotPop Demo Release Checklist

Use this before sending the app to a friend/test user.

## Local sanity check

- [ ] `docker compose down`
- [ ] `docker compose up --build`
- [ ] Open `http://127.0.0.1:5173`
- [ ] Backend health returns `0.25.0`
- [ ] Sign in works with the demo/dev account
- [ ] Dev button appears only for dev user
- [ ] Dev > Smoke check passes

## Feed

- [ ] Feed is full-screen and mobile-first
- [ ] Feed page itself does not scroll like a document
- [ ] Header is light and fixed
- [ ] Footer is light and fixed
- [ ] No Jot Trail in Feed
- [ ] No Next Insight in Feed
- [ ] No Not now button
- [ ] No Back button
- [ ] No small Save rail
- [ ] Whole-card swipe right works
- [ ] Whole-card swipe left works
- [ ] Whole-card swipe up skips
- [ ] Whole-card swipe down returns to previous card
- [ ] Empty Micro-Jot + swipe up skips
- [ ] Empty Micro-Jot + swipe right says `Write a Jot first.`
- [ ] Written Micro-Jot + swipe right saves
- [ ] Saved message says `Jot saved. One step off the popular path.`

## Forge

- [ ] Daily Promises appear
- [ ] Accepted challenge from Feed appears in Forge
- [ ] Feed challenge counts toward first 3 if fewer than 3 are selected
- [ ] Feed challenge becomes optional extra if 3 already exist
- [ ] Swipe to Forge animation works
- [ ] No sound plays

## Evolution

- [ ] Avatar is visible immediately
- [ ] Avatar does not look invisible/collapsed
- [ ] Avatar Growth section is understandable
- [ ] Jot Trail is compact and expandable
- [ ] Next Insight is compact and expandable
- [ ] Footer does not hide important content

## Demo user experience

- [ ] The first 3 minutes feel understandable without explanation
- [ ] The user sees what to do in Feed
- [ ] The user understands Forge means action/completion
- [ ] The user understands Evolution is where signals become character/progress

## Known MVP limitations to say honestly

- Personalization is still early.
- The avatar is symbolic, not a fully dynamic 3D/persona system.
- Jot analysis is not yet intelligent; it is foundation-only.
- The feed is varied and shuffled, but not yet generated specifically for each user.
