# Architecture Decision Guide

Compiled from claude-skills senior-architect skill. Decision frameworks for system design, database selection, and architecture patterns.

---

## Database Selection

### Step 1: Data Characteristics

| Characteristic | Points to SQL | Points to NoSQL |
|----------------|---------------|-----------------|
| Structured with relationships | ✓ | |
| ACID transactions required | ✓ | |
| Flexible/evolving schema | | ✓ |
| Document-oriented data | | ✓ |
| Time-series data | | ✓ (specialized) |

### Step 2: Scale Requirements

- <1M records, single region → PostgreSQL or MySQL
- 1M-100M records, read-heavy → PostgreSQL with read replicas
- >100M records, global distribution → CockroachDB, Spanner, or DynamoDB
- High write throughput (>10K/sec) → Cassandra or ScyllaDB

### Step 3: Consistency Requirements

- Strong consistency required → SQL or CockroachDB
- Eventual consistency acceptable → DynamoDB, Cassandra, MongoDB

### Quick Reference

```
PostgreSQL  → Default choice for most applications
MongoDB     → Document store, flexible schema
Redis       → Caching, sessions, real-time features
DynamoDB    → Serverless, auto-scaling, AWS-native
TimescaleDB → Time-series data with SQL interface
```

---

## Architecture Pattern Selection

### Step 1: Team & Project Size

| Team Size | Recommended Starting Point |
|-----------|---------------------------|
| 1-3 developers | Modular monolith |
| 4-10 developers | Modular monolith or service-oriented |
| 10+ developers | Consider microservices |

### Step 2: Deployment Requirements

- Single deployment unit acceptable → Monolith
- Independent scaling needed → Microservices
- Mixed scaling needs → Hybrid

### Step 3: Data Boundaries

- Shared database acceptable → Monolith or modular monolith
- Strict data isolation required → Microservices with separate DBs
- Event-driven communication fits → Event-sourcing/CQRS

### Step 4: Match Pattern to Requirements

| Requirement | Recommended Pattern |
|-------------|-------------------|
| Rapid MVP development | Modular Monolith |
| Independent team deployment | Microservices |
| Complex domain logic | Domain-Driven Design |
| High read/write ratio difference | CQRS |
| Audit trail required | Event Sourcing |
| Third-party integrations | Hexagonal/Ports & Adapters |

---

## Monolith vs Microservices

**Choose Monolith when:**
- Team is small (<10 developers)
- Domain boundaries are unclear
- Rapid iteration is priority
- Operational complexity must be minimized

**Choose Microservices when:**
- Teams can own services end-to-end
- Independent deployment is critical
- Different scaling requirements per component
- Domain boundaries are well understood

**Hybrid approach:** Start with modular monolith. Extract services only when:
1. A module has significantly different scaling needs
2. A team needs independent deployment
3. Technology constraints require separation

---

## Architecture Decision Records (ADR)

Document every significant architecture decision:

```markdown
# ADR-001: [Decision Title]

## Status
Accepted | Proposed | Deprecated | Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?

### Positive
- [benefit]

### Negative
- [trade-off]

### Risks
- [risk and mitigation]
```

---

## Architecture Assessment Checklist

### Layer Violations
- [ ] Controllers don't contain business logic
- [ ] Services don't import from presentation layer
- [ ] Data access layer doesn't leak to business logic
- [ ] Domain models separated from DTOs

### Dependency Health
- [ ] No circular dependencies between modules
- [ ] Coupling score acceptable (<70/100)
- [ ] No outdated packages with known CVEs
- [ ] Transitive dependencies audited

### Scalability
- [ ] Horizontal scaling path identified
- [ ] Bottlenecks documented
- [ ] Caching strategy defined
- [ ] Database connection pooling configured
- [ ] Async processing for long operations

### Resilience
- [ ] Circuit breakers for external calls
- [ ] Retry with exponential backoff
- [ ] Graceful degradation paths
- [ ] Health check endpoints
- [ ] Timeout configuration for all external calls

---

## Tech Stack Quick Reference

| Category | Options |
|----------|---------|
| **Frontend** | React, Next.js, Vue, Angular, React Native, Flutter |
| **Backend** | Node.js/Express, FastAPI, Go, Django, Spring Boot |
| **Databases** | PostgreSQL, MySQL, MongoDB, Redis, DynamoDB |
| **Infrastructure** | Docker, Kubernetes, Terraform, AWS/GCP/Azure |
| **CI/CD** | GitHub Actions, GitLab CI, CircleCI, Jenkins |
| **Monitoring** | Prometheus+Grafana, Datadog, New Relic |
| **Message Queues** | RabbitMQ, Kafka, SQS, Redis Streams |
