# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Teluka** is a Vertical Micro-SaaS for the Philippines market that combats "bait-and-switch" scams on Facebook Marketplace. It implements a "Hold-and-Release" escrow payment model (GCash/Maya via PayMongo) backed by an evidence chain (photo EXIF verification, unboxing video, delivery tracking).

## Commands

```bash
# Setup
uv venv && source .venv/bin/activate
uv sync

# Run
python main.py   # FastHTML dev server

# Add dependencies
uv add <package>
```

## Planned Architecture

The codebase will follow this structure (not yet built):

```
main.py                  # FastHTML app entry, routes
components/              # FastHTML/Lucide UI components
core/
  escrow.py              # Maya/GCash hold & capture via PayMongo
  forensics.py           # Polars-based Seller Trust Score & risk scoring
  verification.py        # Evidence chain: EXIF checks, unboxing logic
schemas/
  transaction.py         # Pydantic V2 models for deals
  user.py                # Pydantic V2 models for KYC/Trust
lib/
  supabase_client.py     # Shared Supabase client
  paymongo_client.py     # Shared PayMongo client
```

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | `fasthtml` (FastAPI-based, HTMX-native) |
| Validation | `pydantic` V2 |
| Data engine | `polars` (LazyFrame for risk log processing) |
| Database/Auth | `supabase-py` |
| Payments | `paymongo-python` |
| Logistics | Lalamove / Grab API |

## Anti-Scam Escrow Flow

1. **Initiate** — Buyer creates a `Transaction` (Pydantic model)
2. **Escrow** — `paymongo.create_payment_intent()` holds GCash/Maya funds
3. **Evidence** — Seller uploads live photos to Supabase Storage; backend validates EXIF metadata
4. **Logistics** — App polls Lalamove/Grab API until `DELIVERED`
5. **Release** — Buyer uploads unboxing video + confirms → `capture_payment()` fires

## Code Standards

- **FastHTML UI**: Use `Group`, `Card`, `Table` components; all state changes via HTMX (`hx-post`, `hx-target`)
- **Type safety**: All functions must have type hints; Pydantic for all data entering/leaving the system
- **Async**: All Supabase and PayMongo calls must use `async/await`
- **Custom exceptions**: `InsufficientFunds`, `VerificationFailed`, `ScamDetected`
- **Polars**: Use `LazyFrame` for processing blacklisted phone numbers or large activity logs

## PH-Specific Rules

- **Currency**: All monetary `int` values in **centavos** (₱1,000 = `100000`)
- **Timezone**: Always `Asia/Manila` for transaction expiry and delivery windows
- **KYC**: Prioritize GCash/Maya-verified phone numbers
