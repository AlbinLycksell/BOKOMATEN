# Akutnotis UI kit — Alex's lock screen + Magnus's watch

The single most important surface in the system. The akutnotis must be unmistakable, single-thumb-operable, and never cry wolf.

## Files

- `index.html` — three-up stage: quiet phone, akut phone (pulse + tap-to-expand), Apple Watch
- `PhoneFrame.jsx` — minimal iPhone bezel + status bar
- `LockScreen.jsx` — wallpaper + big clock + notification stack (quiet variant + akut variant + expanded variant)
- `WatchFace.jsx` — Apple Watch akutnotis with two action buttons

## Behavior

- The phone bezel pulses once when mounted (the brief's "single attention pulse, then stillness")
- Tap the akut card to expand and reveal "Ta jobbet" / "Skicka tillbaka"
- "Replay pulse" remounts the bezel to re-fire the animation

## Iconography

The phone-frame status icons (signal, wifi, battery) are drawn inline — they belong to the iOS frame, not Verkstad. The brand mark (S + dot) appears in the notification chrome at small sizes.
