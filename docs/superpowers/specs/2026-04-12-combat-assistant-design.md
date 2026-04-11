# Combat Assistant Panel Design

## Overview

Extend the existing statsHelper object UI to include a combat resolution guide that walks new players through the 40K 10th Edition attack sequence: Hit Roll, Wound Roll, Save Roll.

The goal is educational — help new players understand the combat flow so they can transition to physical tabletop play.

## Scope

### In Scope
- Parse attacker weapon stats (already done by statsHelper)
- Parse defender stats (T, SV, W, invulnerable save) from model Description
- Calculate hit threshold from BS/WS
- Calculate wound threshold from S vs T table
- Calculate save threshold from SV + AP modification
- Display three-phase guide with dice counts and required rolls
- Show critical roll reminders (natural 6 on hit/wound, natural 1 on save)
- Warning that only basic stats are parsed; special abilities must be adjusted manually

### Out of Scope
- Automatic dice rolling or result tracking
- Special ability processing (rerolls, +1 modifiers, Sustained Hits, Lethal Hits, etc.)
- Damage allocation to specific models
- Multi-weapon combined attacks
- Phase system integration (no auto-trigger based on current game phase)

## User Flow

1. Player selects attacking models -> clicks existing "Show weapon stats" button -> weapon table appears
2. Player selects defending models -> clicks new "Set Target" button -> defender stats parsed and displayed
3. Each weapon row shows a new "Calc" button (only functional after target is set)
4. Player clicks "Calc" on a weapon -> three-phase combat guide appears below the table

## UI Changes to statsHelper

### Top Button Bar
Add one button to the existing row:

```
[Show weapon stats] [Range input] [Clean] [Set Target]  <- new button
```

### Weapon Table
Add one column:

```
| Name | Stats | Count | Attacks | Range | Calc |  <- new column
```

The "Calc" button is grayed out until a target is set.

### Target Info Bar (new)
Below the weapon table, show parsed defender info:

```
Target: [unit name] T:[value] SV:[value] W:[value] Inv:[value or none]
```

### Combat Guide Panel (new)
Below the target info bar, show three-phase breakdown when a weapon's "Calc" button is clicked:

```
Step 1: Hit Roll
  Roll [N] D6, need [BS/WS]+ to hit
  Natural 6 = Critical Hit (auto-hit)

Step 2: Wound Roll
  S:[value] vs T:[value] -> need [X]+ to wound
  Natural 6 = Critical Wound (auto-wound)

Step 3: Save Roll (defender rolls)
  SV:[value] + AP:[value] -> need [Y]+ to save
  Invulnerable Save [Z]+ (not affected by AP, use if better)
  Each failed save -> [D] damage

Warning: Basic stats only. Adjust manually for special abilities (rerolls, modifiers, etc.)
```

## Data Parsing

### Attacker Data (existing)
Already parsed by `parseFigureData()` in statsHelper:
- Weapon name, BS/WS (accuracy), A (attacks), S (strength), AP, D (damage)
- Melta, Devastating Wounds, Ignore Cover flags

### Defender Data (new)
Parsed from defender model Description using same `parseFigureData()`:
- `T` (toughness) — from stats line, index 2
- `SV` (save) — from stats line, index 3
- `W` (wounds) — from stats line, index 4
- Invulnerable save — **new parser** scanning Abilities text for patterns:
  - Chinese: `"invulnerable save"` or `"invul"` pattern with `(%d+%+)` capture
  - The text typically appears as: `"Invulnerable save — This model has a X+ invulnerable save."`
  - Chinese: `"Invulnerable save"` / `"invul"` typically appears as: `"Invulnerable Save X+"` or `"Invulnerable Save — This model has X+ invulnerable save."`

### Wound Table Logic
```lua
function getWoundThreshold(strength, toughness)
  if strength >= toughness * 2 then return 2 end
  if strength > toughness then return 3 end
  if strength == toughness then return 4 end
  if strength * 2 <= toughness then return 6 end
  return 5  -- strength < toughness
end
```

### Save Calculation
```lua
function getSaveThreshold(sv, ap)
  -- sv is like "2+", ap is like "-1"
  local saveVal = tonumber(sv:match("(%d+)"))
  local apVal = tonumber(ap) or 0
  local modified = saveVal - apVal  -- AP is negative, so subtracting makes save worse
  return math.min(modified, 7)  -- 7+ means impossible
end
```

### Invulnerable Save Parsing
```lua
function parseInvulnerableSave(description)
  -- Try Chinese pattern
  local inv = description:match("invulnerable save.*(%d+%+)")
  if inv then return inv end
  -- Try English pattern
  inv = description:match("invulnerable.*(%d+%+)")
  if inv then return inv end
  return nil
end
```

## Implementation Notes

### Files Modified
1. `TTSLUA/statsHelper.ttslua` — all Lua logic changes
2. `TTSJSON/ftc_base.json` — XmlUI string for both statsHelper objects (GUID 7c7c20 and b7ac7a)

### State Management
- `targetData` — stored in statsHelper script scope, holds parsed defender data `{name, t, sv, w, inv}`
- Cleared when "Clean" is clicked
- No persistence needed (not saved to script_state)

### XML UI Approach
The statsHelper uses object-level `XmlUI` (not global). The UI is defined as a string in `ftc_base.json` and also manipulated programmatically via `self.UI.setXmlTable()`. New elements:
- "Set Target" button added to the top HorizontalLayout
- "Calc" column added to table headers and weapon rows
- Target info and combat guide panels added as new elements below the existing TableLayout

### Sizing
The statsHelper VerticalLayout `width` may need to increase to accommodate the new column and combat guide panel. The position offset may need adjustment.
