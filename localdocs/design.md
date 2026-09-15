# Design — F1 2026 Strategy Oracle

---

## 1. Current Design State

The app currently uses Streamlit's **default theme** with no custom CSS. The UI is functional and clean but lacks the premium F1 aesthetic it deserves.

This document records the intended design direction for future UI polish (Phase 7).

---

## 2. Colour Palette

### Primary Brand Colours
| Name | Hex | Usage |
|---|---|---|
| **F1 Red** | `#E10600` | Primary accents, headers, key metrics |
| **Carbon Black** | `#0F0F0F` | Page background |
| **Pit Lane Grey** | `#1A1A2E` | Card/container backgrounds |
| **Telemetry Blue** | `#00D2FF` | Active states, links, data highlights |
| **Podium Gold** | `#FFD700` | P1 winner highlight |
| **Silver** | `#C0C0C0` | P2 / secondary text |
| **Bronze** | `#CD7F32` | P3 |

### Tyre Compound Colours (Official F1)
| Compound | Hex | |
|---|---|---|
| SOFT | `#FF0000` | Red |
| MEDIUM | `#FFD700` | Yellow |
| HARD | `#FFFFFF` | White |
| INTERMEDIATE | `#00CC00` | Green |
| WET | `#0000FF` | Blue |

### Status / Indicator Colours
| State | Hex |
|---|---|
| Success / Fastest | `#00E676` |
| Warning / Used Tyre | `#FFC107` |
| Error / DNF | `#FF5252` |
| Neutral / Text | `#B0BEC5` |

---

## 3. Typography

### Fonts
- **Primary Font:** [Inter](https://fonts.google.com/specimen/Inter) — Clean, modern, technical. Used for all body text and UI labels.
- **Display Font:** [Orbitron](https://fonts.google.com/specimen/Orbitron) — Futuristic, motorsport aesthetic. Used for main title, lap times, and large metric displays.
- **Monospace Font:** `Roboto Mono` or `Courier New` — Used for raw simulation output, strategy sequences (e.g. `SOFT -> MEDIUM -> HARD`)

### Type Scale
| Element | Font | Size | Weight |
|---|---|---|---|
| Page Title | Orbitron | 2.5rem | 700 |
| Tab Headers | Inter | 1.2rem | 600 |
| Section Headers (h3) | Inter | 1.0rem | 600 |
| Body Text | Inter | 0.9rem | 400 |
| Metric Values (st.metric) | Orbitron | 1.5rem | 700 |
| Captions / Sub-labels | Inter | 0.75rem | 300 |
| Code / Strategy Sequence | Roboto Mono | 0.85rem | 400 |

---

## 4. Layout Principles

- **Dark mode by default** — Background is near-black (#0F0F0F), cards in dark grey (#1A1A2E)
- **3-column podium display** — P1 in centre (larger), P2 left, P3 right — mirrors a real podium
- **Data-first** — Tables and metrics are prominent; decorative elements are subtle
- **Minimum whitespace** — F1 dashboards are dense. Do not leave excessive blank space.
- **Progress indicators** — Always show a progress bar or spinner during any simulation

---

## 5. Component Design Patterns

### Podium Cards
```
+------------------+   +--------------------+   +------------------+
|   P2             |   |   P1 (centre)      |   |   P3             |
|   Driver Name    |   |   Driver Name      |   |   Driver Name    |
|   +X.XXXs        |   |   1h 32m 14.50s   |   |   +X.XXXs        |
+------------------+   +--------------------+   +------------------+
     Silver                  Gold                    Bronze
```

### Strategy Badges
- 1-Stop strategies: display with a single tyre icon
- 2-Stop strategies: display with two tyre icons
- Compound sequence shown as coloured dots: [RED] -> [YELLOW] for SOFT -> MEDIUM

### Chat Interface (AI Engineer Tab)
- Dark chat bubbles with rounded corners
- User messages: right-aligned, Telemetry Blue border
- Assistant messages: left-aligned, Carbon Black background, F1 Red left border
- Status spinner shows "Thinking & Simulating..." with animated dots

---

## 6. Streamlit Configuration

```toml
# .streamlit/config.toml (to be created)
[theme]
base = "dark"
primaryColor = "#E10600"
backgroundColor = "#0F0F0F"
secondaryBackgroundColor = "#1A1A2E"
textColor = "#FFFFFF"
font = "sans serif"
```

---

## 7. Design Inspiration

- **Official F1 website** (formula1.com) — timing screens, strategy panels
- **McLaren + Mercedes team dashboards** — dense telemetry UI with neon accents
- **Motorsport.com** lap chart design — compound colour coding
