# Design system: CPT Myth-Buster

A calm, chat-first interface inspired by modern AI assistants. One shell for every page, neutral surfaces, and color used only to carry meaning (verdicts, labels, status).

## Principles

1. **Source first.** Every answer shows where it came from before anything else decorative.
2. **Color means something.** Green = matches/fact, red = myth/contradicts, amber = not covered/caution, blue = official/new rule.
3. **One shell.** Sidebar + top bar + centered 780px column on every view.
4. **Honest states.** Loading, refused and "no official answer" states are designed, not hidden.

## Typography

| Role | Font | Size / weight |
|---|---|---|
| Greeting | General Sans | clamp(34px, 5vw, 52px) / 500 |
| Page title | General Sans | 32px / 500 |
| Card title | General Sans | 16.5–18px / 600 |
| Body | General Sans | 15.5–16px / 400, line-height 1.6 |
| Labels and pills | General Sans | 11–12.5px / 600–700, uppercase for verdicts |

Font source: Fontshare (`general-sans@400,500,600,700`), system-ui fallback.

## Color tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | #FFFFFF | #131314 | Page background |
| `--side` / `--surface` | #F0F4F9 | #1E1F20 | Sidebar, cards, composer |
| `--surface2` | #E9EEF6 | #282A2C | User bubbles, secondary surfaces |
| `--hover` | #E2E7EF | #333537 | Hover state |
| `--border` | #DDE3EA | #3C4043 | Dividers, outlines |
| `--text` | #1F1F1F | #E3E3E3 | Primary text |
| `--muted` | #5F6368 | #A8ABB0 | Secondary text |
| `--accent` / `--accent-soft` | #0B57D0 / #D3E3FD | #A8C7FA / #1F3760 | Links, active nav, official badges, new rule |
| `--ok` / `--ok-soft` | #146C2E / #DDF3E4 | #6DD58C / #173A24 | Fact, matches |
| `--warn` / `--warn-soft` | #8A4B00 / #FEEFC3 | #F6C35B / #3D2E0A | Not covered, caution, update banner |
| `--bad` / `--bad-soft` | #B3261E / #FCE8E6 | #F2B8B5 / #442726 | Myth, contradicts |
| Gradient (greeting, AI icon) | #4285F4 → #9B72CB → #D96570 | same | Brand moment only |

## Shape and spacing

- Radius: 28px composer, 24px bubbles, 20px panels/cards, 16px suggestion cards and source blocks, 999px pills.
- Spacing scale: 4, 8, 10, 12, 14, 16, 20, 24, 28px. Card gap 10–12px.
- Content column: max 780px; sidebar 272px (68px collapsed); top bar 64px.

## Components

| Component | Notes |
|---|---|
| Sidebar button | Pill, icon + label; active = `--accent-soft` fill + `--accent` text |
| Suggestion card | 132px tall, question text + round icon bottom-right |
| User bubble | `--surface2`, radius 24/4/24/24, right-aligned |
| Assistant message | Gradient sparkle avatar + body; typing dots while loading |
| Verdict pill | MYTH (red), FACT (green), NO OFFICIAL ANSWER (amber), AI ANSWER (soft gradient) |
| Source block | Quote with left rule + badge (Official source / School source / Career advice / Check with DSO / Quote verified) + link |
| Match line | "Matched by meaning · score 0.75" in `--faint` 12.5px |
| Action row | Copy, helpful, not helpful (34px icon buttons) |
| Related chips | Outlined pills with follow-up questions |
| Composer | Rounded 28px box, auto-growing textarea, send button turns solid when text is entered |
| Status pills | "Official sources", "Smart search on" (green), "Loading smart search…" (amber) |
| News card | Label pill + outlet + date, linked headline, note, "Compared with the official source" |
| Panel | `--surface`, 20px radius, 22px padding; used for tools, quality report, signup |
| Legal footer | 12.5px muted text with USCIS and Study in the States links on every page |

## Accessibility

- Text contrast meets WCAG AA in light and dark themes.
- Verdicts always use words, not color alone.
- `aria-live` on the chat thread and tool results; `aria-current` on active nav.
- `prefers-reduced-motion` disables animations.
- Mobile: sidebar becomes a slide-over with a scrim under 860px.
