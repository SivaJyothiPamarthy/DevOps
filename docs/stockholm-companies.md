# Stockholm companies: stack and interview focus

> Based on public engineering blogs, conference talks, and job ads. Stacks
> change, so **check the company's current job ad and engineering blog before
> your interview** and tailor your examples.

## Overview

| Company | Domain | Cloud / platform (publicly known) | What they focus on |
|---------|--------|-----------------------------------|--------------------|
| **Spotify** | Music streaming | GCP (GKE, BigQuery, Pub/Sub), Backstage (they built it) | Developer experience, golden paths, fleet management, autonomy |
| **Klarna** | Fintech / bank | AWS, Kubernetes, Terraform | Security, compliance (Finansinspektionen, DORA, PCI DSS), reliability |
| **King** (Microsoft) | Mobile games | GCP, big data pipelines | Scale, data platform, cost |
| **Ericsson** | Telecom | Kubernetes (cloud-native 5G core), OpenStack, on-prem, Jenkins/Gerrit | Linux depth, networking, CI at huge scale, Helm |
| **H&M Group** | Retail / e-commerce | Azure (AKS), Terraform, GitHub/Azure DevOps | Platform engineering, Black-Friday scale, many teams |
| **Volvo Cars / Polestar** | Automotive | AWS + Azure, embedded + cloud | Hybrid, compliance, connected cars |
| **Mojang** (Microsoft) | Games (Minecraft) | Azure | Large-scale online services |
| **Epidemic Sound, Truecaller, Sinch, Voi, Kry/Livi, Einride** | Scale-ups | Mostly AWS or GCP + Kubernetes | Generalists who own the full stack, pragmatism, cost |
| **SEB, Swedbank, Nordea, Handelsbanken** | Banks | Hybrid: on-prem + OpenShift + Azure/AWS | Change management, security, regulation, legacy migration |
| **Consultancies** (Netlight, Knowit, Sopra Steria, Accenture, Devoteam, Tietoevry, Cygni) | Consulting | Whatever the client runs | Breadth, communication, certifications (CKA, AWS/Azure) |

## Company-specific prep

### Spotify
- Know **Backstage**: software catalog, templates (scaffolder), TechDocs, plugins. Why a developer portal?
- "Squads, tribes, chapters, guilds" model — and that Spotify itself says it evolved past the original.
- Expect questions on **platform as a product**: how do you measure developer productivity (DORA metrics, SPACE), how do you drive adoption without mandates?
- Fleet management: how would you upgrade a library or base image across 2,000 repos? (Automated PRs, Renovate-style bots, canaries, auto-merge with tests.)
- Practice: *"Design a golden path for a new backend service — from `create` button to production."*

### Klarna
- **Security first**: least privilege IAM, secrets management, encryption at rest/in transit, audit logs.
- Regulation: Klarna holds a Swedish banking licence. Know at a high level: **GDPR**, **PCI DSS** (card data), **DORA** (EU Digital Operational Resilience Act, applies from Jan 2025 — ICT risk, incident reporting, resilience testing, third-party risk).
- Expect: incident handling, postmortems, change approvals that still allow fast delivery.
- Practice: *"How would you give developers production access for debugging without breaking compliance?"* (Just-in-time access, break-glass with audit, read-only by default.)

### King
- Massive traffic spikes (game launches, events). Autoscaling, load testing, cost per player.
- Data pipelines: Pub/Sub / Kafka, BigQuery, Airflow.
- Practice: *"A new game launches tomorrow, expect 10x traffic. What do you do today?"*

### Ericsson
- Deep **Linux** and **networking** (TCP, DNS, routing, iptables, MTU), Kubernetes networking (CNI, Multus, SR-IOV for telecom).
- Helm charts at scale, CI with Jenkins/Spinnaker, Gerrit code review.
- Practice: *"Explain what happens from `kubectl apply` until a pod receives traffic."*

### H&M Group
- Azure: AKS, Azure AD / Entra ID workload identity, Key Vault, Azure Front Door.
- Many product teams → shared platform, Terraform modules, policy (Azure Policy / OPA Gatekeeper).
- Practice: *"Design a landing zone / multi-team Terraform setup."*

### Banks
- Change-Advisory-Board culture → show how CI/CD *improves* control (every change reviewed, traceable, reproducible).
- OpenShift, on-prem, air-gapped registries, Artifactory/Nexus.

## Swedish workplace culture: what interviewers listen for

- **Flat hierarchy & consensus** — show you seek input, don't dictate. "We decided as a team…"
- **Autonomy & trust** — you own outcomes without micromanagement.
- **Lagom** — right-sized solutions; avoid over-engineering (very relevant for the take-home!).
- **Blameless culture** — talk about systems, not people, in incident stories.
- **Work–life balance** — on-call should be sustainable; mention reducing toil and alert fatigue.
- **Fika** — relationship-building is part of the job. 🙂

## Practical notes

- **Salary** is discussed as **monthly gross in SEK**. Ballpark for DevOps/Platform/SRE in Stockholm
  (2025–2026 job-market reports, varies a lot): junior ~40–50k, mid ~50–65k, senior ~65–85k+,
  staff/lead higher. Check current sources (e.g. Levels.fyi, Glassdoor, Unionen's salary tool).
- **Notice period** is often 1–3 months; companies are used to waiting.
- **Benefits** to ask about: pension (tjänstepension, often ITP), friskvårdsbidrag (wellness allowance), vacation (25+ days), parental leave top-up.
- **Language**: most tech teams work in English. Swedish is a plus, rarely a requirement at product companies; banks and public sector may require it.
- **Certifications** valued (especially at consultancies): CKA/CKAD, AWS Solutions Architect / DevOps Pro, Azure AZ-104/AZ-400, HashiCorp Terraform Associate.
