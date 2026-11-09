# FunPay Component

The component that connects the app to FunPay.

## Structure

- `expressions/` — FunPay-related expressions and their context classes.
- `properties/` — the component's property declarations.
- `routers/` — routers and handlers for FunPay events.
- `component.py` — the FunPay component definition.
- `session.py` — a custom FunPayBotEngine session.
- `first_response_cache.py` — a cache of chats that aren't new, used to decide when to send the first-message auto-response.