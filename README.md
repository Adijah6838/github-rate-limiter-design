# GitHub Rate Limiter — System Design

A comprehensive system design document and proof-of-concept for a distributed rate limiter designed to sit in front of a service making outbound requests to the GitHub REST API.

## 📖 Design Documents
- **[01 — Requirements & Estimation](docs/01-requirements-estimation.md)**: Functional/non-functional requirements, back-of-the-envelope math, and algorithm selection.
- **[02 — High-Level Design](docs/02-high-level-design.md)**: System architecture, sidecar integration, and Mermaid diagrams.
- **[03 — Deep Dive & Trade-offs](docs/03-trade-offs.md)**: Failure modes (Fail-open vs Fail-closed), race conditions (Lua vs Transactions), and fairness.

## 🧠 Algorithm
This design utilizes the **Token Bucket** algorithm, allowing for controlled bursts while strictly enforcing long-term average limits to prevent API bans.

## 🚀 Proof of Concept
The `scripts/` directory contains a standard-library-only Python simulation of the Token Bucket algorithm handling concurrent requests.

To run the simulation:
```bash
python scripts/rate_limiter_demo.py