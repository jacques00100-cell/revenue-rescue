# Multi-Tenant State Architecture (Future)

## Current (Single Tenant)
All data in `/builds/revenue-rescue/state.json`

## Future (Multi-Tenant) - When We Hit 5+ Clients

### File Structure
```
builds/
├── revenue-rescue/          # Product template
│   ├── state.json
│   └── handoff-schema.json
├── clients/                 # Per-client isolation
│   ├── acme-hvac/
│   │   ├── state.json       # Client-specific state
│   │   ├── handoffs/        # Client handoff history
│   │   └── appointments.db  # SQLite per client
│   ├── smith-plumbing/
│   │   ├── state.json
│   │   ├── handoffs/
│   │   └── appointments.db
│   └── ...
└── shared/                  # Cross-client data
    ├── agent-knowledge/     # Learnings across all clients
    └── benchmarks.json      # Industry averages
```

### State Isolation
Each client gets:
- Independent `state.json` (no data bleeding)
- Independent handoff history
- Isolated database (SQLite or Postgres schema)

### Shared Resources (Safe)
- Agent training/knowledge
- Industry benchmarks
- System-wide metrics (anonymized)

### Postgres Migration Trigger
**When:** 500+ tokens in state.json OR 10+ clients

```sql
-- Per-client schema
CREATE SCHEMA client_acme_hvac;

CREATE TABLE client_acme_hvac.appointments (
    id UUID PRIMARY KEY,
    client_phone TEXT,
    scheduled_at TIMESTAMP,
    service_type TEXT,
    status TEXT
);

CREATE TABLE client_acme_hvac.handoffs (
    id UUID PRIMARY KEY,
    from_agent TEXT,
    to_agent TEXT,
    version INTEGER,
    summary JSONB,
    created_at TIMESTAMP
);

-- Indexed for agent queries
CREATE INDEX idx_handoffs_agents ON client_acme_hvac.handoffs(from_agent, to_agent);
CREATE INDEX idx_handoffs_date ON client_acme_hvac.handoffs(created_at);
```

### Agent Concurrency Model
```
Agent A (Acme HVAC) ──┐
                       ├──→ Shared Agent Pool ──→ Isolated DB Writes
Agent B (Smith Plumbing) ┘

Each agent:
1. Receives: client_id + task
2. Loads: client-specific state
3. Works: in isolated context
4. Writes: to client schema only
```

### Data Retention
- **Active clients:** Full history in Postgres
- **Churned clients:** Archive to S3 after 90 days
- **Handoffs:** Keep 90 days hot, rest in cold storage

### Migration Path
1. **Now:** Single JSON file
2. **5 clients:** Directory per client, still JSON
3. **10 clients:** Postgres with schema per client
4. **50+ clients:** Sharded Postgres or DynamoDB

## Key Principle
Context window = reasoning (shared agents)
Database = memory (isolated per client)