# OdooForge

Open-source deployment kit that provisions a production-grade Odoo instance on AWS, Azure, DigitalOcean, or a local Docker host, and ships with a Claude-powered customer support module installable from the Odoo Apps menu.

## Why

Small and mid-size businesses pick Odoo because the Community edition is free and the feature set rivals SaaS ERPs that charge per seat. The friction is everything around it: getting it onto a cloud you actually trust, keeping backups, plugging it into modern AI without paying for a second SaaS layer, and not getting locked into one vendor.

OdooForge solves that with one repo. Pick your cloud, run one command, and you have Odoo with a working AI customer support flow on a backup-friendly stack you fully own.

## What it does

### Cloud-portable deployment

One CLI command stands up the same stack on AWS, Azure, DigitalOcean, or a local Docker host. The Terraform interface is identical across providers, so swapping clouds is a config change, not a rewrite. An Oracle Cloud Always Free target is included for zero-cost hosted demos.

### AI customer support, native in Odoo

A custom Odoo module adds a "Draft AI reply" button to every Helpdesk ticket. The agent retrieves relevant knowledge base articles via pgvector, calls tools (`lookup_customer`, `search_kb`, `check_order_status`, `escalate_to_human`), and drafts a reply for human review. Every AI action is written to a filterable audit log inside Odoo.

### Pluggable LLM provider

Default provider is Groq (free tier, no API key cost). Anthropic Claude is supported when a key is provided. Ollama is supported for fully self-hosted deployments. Switching providers is a setting in Odoo, not a code change.

### Sensible SME defaults

Multi-currency, multi-language (English, Urdu, Arabic), Pakistan timezone, multi-tenant-friendly nginx and Let's Encrypt configs, daily pg_dump and filestore backup scripts.

## Who it's for

Owners and operators of small ERPs who want Odoo on their own cloud, not someone else's. Consultants who deploy Odoo for clients and want a repeatable, audit-friendly stack. Engineering teams evaluating Odoo against per-seat SaaS ERPs.

## Phases

| Phase | Scope | Status |
|---|---|---|
| 1 | docker-compose foundation: Odoo 18 + Postgres 16 + pgvector, OCA helpdesk_mgmt | Shipped |
| 2 | Custom addon scaffold + simple "Draft reply" ticket action using Groq | Shipped |
| 3 | Full support agent with tool use + pgvector RAG + audit log | Shipped |
| 4 | Terraform module for AWS, end-to-end deploy | Pending |
| 5 | Terraform modules for Azure and DigitalOcean, portability smoke test | Pending |
| 6 | Oracle Cloud Always Free deployment, live demo URL, walkthrough video | Pending |

Estimated total build time: 30 hours across two to three weekends.

## Positioning

OdooForge is a senior-engineer artifact for cloud-portable Odoo with AI baked in. Not an Odoo Enterprise replacement, not an indie SaaS, not a tutorial fork. The repo demonstrates infra discipline, Odoo module development, and production AI integration in one MIT-licensed package.
