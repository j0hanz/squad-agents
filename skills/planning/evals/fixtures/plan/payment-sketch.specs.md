# payment-sketch

## 1. Goal

- Enable users to make payments via credit card.
- Completion signal: A user can submit a payment and receive a confirmation.

## 2. Requirements

- `REQ-001`: The system MUST process credit card payments via the Stripe API.
- `REQ-002`: The system MUST store a payment record with status and timestamp on success.

## 3. Interfaces

- HTTP POST /payments accepting card token, amount, and currency
- Returns payment ID and status on success
