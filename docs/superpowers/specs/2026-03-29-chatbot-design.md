# DPDP Kavach — Compliance Chatbot Design

**Date:** 2026-03-29
**Status:** Approved

## Overview

Add a floating chat widget to DPDP Kavach that lets users ask questions about their compliance scan results. The chatbot uses the Sarvam API (already integrated) with the scan's classified elements, obligations, conflicts, and metrics injected as context. Responses are generated in the user's selected output language (all 22 Indian scheduled languages supported).

## Architecture

```
Frontend (App.jsx)                 Backend (main.py)
─────────────────                 ─────────────────
ChatPanel (floating, bottom-right) → POST /api/chat
  - Message history (multi-turn)       - Build system prompt with scan_context
  - Suggested quick prompts            - Call Sarvam API (existing pattern)
  - Language from current selection    - Return { reply } in target language
  - Floating chat button
```

## Components

### 1. Backend — `POST /api/chat`

**Request body:**
```json
{
  "message": "What PII fields did you find?",
  "conversation_history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "scan_context": {
    "classified_elements": [...],
    "obligations": [...],
    "conflicts": [...],
    "sector": "fintech",
    "metrics": { "fields_scanned": 20, "penalty_exposure_current_crore": 5 }
  },
  "language": "Hindi"
}
```

**System prompt contains:**
- Role definition: "You are a DPDP Act compliance advisor for Indian businesses."
- Summary of the scan: sector, number of fields, PII categories found, obligation count, conflict count, penalty exposure
- Full lists of classified elements, obligations, and conflicts
- Language instruction: respond in the target language

**Response:**
```json
{ "reply": "आपके स्कीमा में 20 फ़ील्ड पाए गए..." }
```

**Error handling:** If Sarvam fails, return `{ "reply": "Sorry, I couldn't generate a response. Please try again." }` with HTTP 200 (don't crash the chat).

### 2. Frontend — Floating Chat Panel

**Button:** Fixed position, bottom-right corner (16px from edges). Shield icon or chat bubble icon. Small, circular. Dark background (#0f172a), white icon. Subtle pulse animation when new (unread) message.

**Panel:** Slides up from the button, ~360px wide, ~480px tall. Contains:
- Header: "Compliance Assistant" title, language badge showing current language, close (×) button
- Message list: scrollable, user messages right-aligned (blue bubble), bot messages left-aligned (gray bubble)
- Suggested prompts (shown only when chat is empty / no history):
  - "What PII fields did you find?"
  - "What are my key obligations?"
  - "What conflicts should I worry about?"
  - "How do I reduce my penalty exposure?"
  - (Dynamic: if 0 obligations → hide obligation prompt; if 0 conflicts → hide conflict prompt)
- Input area: text input + send button (or Enter to send)

**State:** `chatOpen` boolean, `chatMessages` array `[{role, content}]`, `chatLoading` boolean, `suggestedPrompts` array.

### 3. Suggested Prompts Logic

| Condition | Prompts to show |
|-----------|----------------|
| obligations > 0 AND conflicts > 0 | All 4 |
| obligations > 0 AND conflicts == 0 | 1, 2, 4 (skip conflict prompt) |
| obligations == 0 AND conflicts > 0 | 1, 3, 4 (skip obligation prompt) |
| obligations == 0 AND conflicts == 0 | 1, 4 (skip obligation/conflict) |

## Data Flow

1. User clicks floating button → panel opens, suggested prompts shown
2. User clicks a prompt or types a question → add to `chatMessages` as user message → show typing indicator → call `/api/chat`
3. Bot reply arrives → add to `chatMessages` as assistant message → scroll to bottom
4. Language switch → `switchLanguage()` already calls `/api/translate` for the whole result; chat uses `language` state which persists across sections

## Integration Points

- **Scan context:** Use `result` state (already populated after scan). Chat is only enabled after a scan exists.
- **Language:** Uses existing `language` state. Each chat message request sends current language.
- **Suggested prompts:** Dynamically filtered based on `result.obligations.length` and `result.conflicts.length`.

## Non-Goals (Out of Scope)

- No chat history persistence (per-session only, cleared on page refresh)
- No file/attachment support in chat
- No streaming responses (async request/response, show typing indicator)
- No separate chatbot endpoint for unauthenticated users (requires a scan result)

## File Changes

| File | Change |
|------|--------|
| `app/main.py` | Add `ChatRequest` model, `POST /api/chat` endpoint with system prompt builder and Sarvam call |
| `web/src/App.jsx` | Add floating chat button, `ChatPanel` component, `chatMessages`/`chatOpen`/`chatLoading` state, suggested prompts logic, integrate into main `App` layout |
