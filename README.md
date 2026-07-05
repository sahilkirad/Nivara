# Nivara

Nivara is an Agentic AI-powered digital adoption platform for helping customers discover, understand, and adopt relevant SBI digital services based on their life stage, financial goals, financial context, and preferences.

The goal is not to build a generic chatbot, banking dashboard, or blind recommendation engine. The goal is to reason from customer context and produce explainable, useful financial guidance.

## Product Flow

```text
Understand Customer Context
        ↓
Discover Financial Needs
        ↓
Explain Benefits
        ↓
Map Relevant SBI Services
        ↓
Create Personalized Adoption Journey
        ↓
Increase Digital Adoption
```

Every recommendation should clearly explain:

- what need was discovered
- why it matters for the customer
- which SBI service is relevant
- how that service helps
- what action the customer should take next

## Architecture Direction

Nivara is structured as a microservice-based system with event-driven communication.

```text
Frontend
  ↓ REST commands/reads
Context Service
  ↓ Kafka event
Agent Service
  ↓ Kafka event
Recommendation Service
  ↓ Kafka event
Journey Service
```

REST APIs are used for frontend commands and reads. Kafka is used for backend workflow progression between services.

Each backend service owns its own responsibility and will have its own PostgreSQL container through its service-specific Docker Compose file.

## Services

```text
frontend/
```

Next.js application for welcome, onboarding, dashboard, recommendations, journey tracker, and profile/consent settings.

```text
services/context-service/
```

FastAPI service responsible for customer profile, financial context, consent, goals, preferences, and context building.

```text
services/agent-service/
```

FastAPI service responsible for the agent workflow. It contains exactly four agents:

- Journey Orchestrator Agent
- Life Event Intelligence Agent
- Financial Advisor Agent
- SBI Service Mapper Agent

Agents communicate internally through orchestrated workflow state, not Kafka. Kafka is used only at service boundaries.

```text
services/recommendation-service/
```

FastAPI service responsible for SBI product knowledge, product mapping, recommendations, and recommendation history.

```text
services/journey-service/
```

FastAPI service responsible for personalized adoption roadmap generation, journey progress, completed steps, and next actions.

## Reliability Model

Nivara uses Kafka with the Outbox Pattern for reliable workflow processing.

Each service should follow this flow:

```text
Consume Kafka event
  ↓
Check idempotency
  ↓
Persist business result in service DB
  ↓
Persist next event in outbox table
  ↓
Commit DB transaction
  ↓
Publish outbox event to Kafka
  ↓
Commit Kafka offset
```

This supports:

- replayability through Kafka offsets
- retryability through controlled retries
- idempotency through processed event tracking
- auditability through event IDs and correlation IDs
- loose coupling between services
- recovery when services temporarily fail

## Agent Memory

The agent service uses two memory types:

```text
episodic memory
```

User-specific history such as recommendations shown, actions completed, ignored suggestions, feedback, and journey progress.

```text
semantic memory
```

Stable knowledge such as SBI product information, financial concepts, benefits, and need-to-service mappings.

Procedural memory is intentionally not modeled as a separate memory folder. Rules and policies can live as versioned backend logic/configuration later.

## Project Structure

```text
Nivara/
├─ frontend/
├─ services/
│  ├─ context-service/
│  ├─ agent-service/
│  ├─ recommendation-service/
│  └─ journey-service/
├─ infra/
├─ docs/
├─ docker-compose.yml
├─ docker-compose.frontend.yml
└─ docker-compose.backend.yml
```

Each backend service has its own empty Docker Compose file where the service container and its PostgreSQL container will be defined later.

## Product Quality Rule

Architecture supports the product. It must not replace the product.

Nivara outputs must remain:

- explainable
- detailed
- accurate
- valuable
- user-friendly

The final user experience should feel like a financial guidance platform, not a technical AI system.
