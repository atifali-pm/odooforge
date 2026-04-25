# OdooForge Hands-On Guide

This is the kickoff guide for the next Claude session in `/home/atif/projects/odooforge/`. Read top to bottom before writing any code.

## Screenshots

When you hit a UI milestone (Odoo loads on local Docker, addon installs from Apps menu, "Draft reply" button works on a ticket, Terraform deploys to AWS, demo lives on Oracle Cloud), capture a screenshot and save it to `/screenshots/` at the repo root. Use descriptive filenames like `01-odoo-local-up.png`, `02-addon-installed.png`, `03-draft-reply-button.png`, `04-aws-deploy.png`, `05-oracle-live-demo.png`.

The portfolio-maintainer agent at `~/projects/portfolio/.claude/agents/portfolio-maintainer.md` looks in this directory when deciding whether to promote the project to atifali.pages.dev. No screenshots = the project does not qualify.

Do not put screenshots in `/docs/`, `/public/`, or the README. `/screenshots/` is the one canonical location.

## Locked decisions (do not relitigate)

These were settled in the portfolio session on 2026-04-25. Treat them as fixed inputs, not open questions.

1. **Ports.** Odoo on `8069`, Postgres on `5465`. Ollama is not in the default stack. Verified clear against running Docker stacks (zarpay 5450, n8n 5451, learnloop 5455, tracklane 5460) and host `ss -tlnp`.
2. **Odoo version is 18 Community.** Pivoted from 19 on 2026-04-25 because OCA `helpdesk_mgmt` has no 19.0 branch yet (only through 18.0). The full OCA addon ecosystem on 18 outweighs running on the latest core. Not chasing 19 or 20.
3. **Default LLM provider is Groq.** Free tier, no API key cost. Anthropic Claude is supported through the same adapter when a key is provided. Ollama is supported for self-hosted use. The user-facing setting in Odoo picks the active provider.
4. **Demo subdomain is deferred to Phase 6.** Default to a no-cost option (DuckDNS, sslip.io, or Cloudflare Tunnel pointing to the Oracle Cloud Always Free VM). No paid TLD.
5. **License is MIT.** Repo is public at `github.com/atifali-pm/odooforge`.
6. **MVP scope is the support agent only.** Sales copilot, inventory AI, accounting AI are post-v1. Ship one AI flow cleanly.

## Preflight

Before starting Phase 1, confirm:

- [ ] Docker and docker compose v2 are installed and the daemon is running
- [ ] Ports 8069 and 5465 are free on the host (`ss -tlnp | grep -E ':8069|:5465'` returns nothing)
- [ ] At least 8 GB of free RAM (Odoo 18 boots heavier than 17)
- [ ] At least 10 GB of free disk
- [ ] Terraform v1.7 or newer on PATH (needed from Phase 4 onward; Phase 1-3 are Docker-only)
- [ ] A Groq account with a free-tier API key in `.env` (needed from Phase 2 onward)
- [ ] An Oracle Cloud Always Free account (needed from Phase 6; create the account early since identity verification can take a day)

## Paste-ready kickoff prompt

Drop this verbatim into the next Claude session inside `/home/atif/projects/odooforge/` to start Phase 1.

```
Read HANDS-ON.md and the project memory at ~/.claude/projects/-home-atif-projects-odooforge/memory/.
Confirm the locked decisions block (ports 8069 + 5465, Odoo 18, Groq default, demo deferred to Phase 6).
Then start Phase 1: scaffold a docker-compose stack with Odoo 18 + Postgres 16 + pgvector, wire a single Odoo database, vendor OCA helpdesk_mgmt 18.0 into ./addons/, and install it.
The success criterion is: `docker compose up -d` works, http://localhost:8069 loads, and the Helpdesk app is installed.
Save a screenshot of the loaded Odoo UI to /screenshots/01-odoo-local-up.png when it works.
Commit Phase 1 as one commit. Do not start Phase 2 in the same commit.
```

## Phase plan

### Phase 1: docker-compose foundation (~4h)

- [ ] Create `docker-compose.yml` with `odoo:18` + `pgvector/pgvector:pg16` services
- [ ] Wire Odoo to Postgres on port 5465 host-side, 5432 container-side
- [ ] Map Odoo to host port 8069
- [ ] Mount `./addons` for custom modules and `./config/odoo.conf` for Odoo config
- [ ] Create `.env.example` with `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`, `ODOO_DB_NAME`
- [ ] Write a `make up` / `make down` / `make logs` Makefile
- [ ] Vendor OCA `helpdesk_mgmt` 18.0 into `./addons/helpdesk_mgmt`
- [ ] Verify the Helpdesk app installs cleanly from the Apps menu
- [ ] Save `screenshots/01-odoo-local-up.png` and `screenshots/02-helpdesk-installed.png`
- [ ] Commit: `Phase 1: local docker-compose stack`

### Phase 2: addon scaffold + simple AI ticket action (~4h)

- [ ] Generate the `odooforge_ai` addon skeleton (`__manifest__.py`, `models/`, `views/`, `security/`)
- [ ] Add the addon to the Apps menu and install it
- [ ] Add a "Draft AI reply" button to the Helpdesk ticket form view
- [ ] Add a `groq_provider.py` that calls Groq's free-tier Llama 3 model
- [ ] On click, send the ticket subject + body to Groq, write the reply to a draft field on the ticket
- [ ] Save `screenshots/02-addon-installed.png` and `screenshots/03-draft-reply-button.png`
- [ ] Commit: `Phase 2: AI addon scaffold and Groq ticket action`

### Phase 3: full support agent with tool use + RAG + audit log (~8h)

- [ ] Add a `kb.article` Odoo model for knowledge base articles, with a pgvector embedding column populated via raw SQL
- [ ] Add an embedding pipeline (Groq or a small local model) that runs on KB article create/update
- [ ] Replace the Phase 2 single-shot prompt with a tool-using agent loop
- [ ] Implement four tools: `lookup_customer`, `search_kb` (pgvector top-k), `check_order_status`, `escalate_to_human`
- [ ] Add an `odooforge_ai.audit_log` model that captures provider, model, prompt, tools called, tokens, latency, and outcome
- [ ] Add a backend list view for the audit log with filters
- [ ] Add a provider abstraction so the same agent runs on Groq, Claude, or Ollama based on settings
- [ ] Save `screenshots/04-agent-tool-call.png` and `screenshots/05-audit-log.png`
- [ ] Commit: `Phase 3: tool-using support agent with RAG and audit log`

### Phase 4: Terraform module for AWS (~6h)

- [ ] Create `terraform/aws/` with VPC, subnets, security group, EC2 host, EBS volume, EIP, Route53 stub
- [ ] Provision the same docker-compose stack on the EC2 host via cloud-init
- [ ] Add nginx + Let's Encrypt automation
- [ ] Add `bin/odooforge up --target=aws` shim that wraps `terraform apply`
- [ ] Add backup script: pg_dump + filestore rsync to S3
- [ ] Verify a clean deploy on a brand-new AWS account
- [ ] Save `screenshots/06-aws-deploy.png`
- [ ] Commit: `Phase 4: AWS Terraform module + deploy CLI`

### Phase 5: Azure + DigitalOcean modules (~4h)

- [ ] Create `terraform/azure/` mirroring the AWS interface (VM + managed disk + NSG + public IP)
- [ ] Create `terraform/digitalocean/` mirroring the AWS interface (Droplet + reserved IP + firewall)
- [ ] Verify `--target=azure` and `--target=do` both produce a working Odoo URL
- [ ] Document the portable interface in `terraform/README.md`
- [ ] Save `screenshots/07-azure-deploy.png` and `screenshots/08-do-deploy.png`
- [ ] Commit: `Phase 5: Azure and DigitalOcean modules`

### Phase 6: Oracle Cloud Always Free demo + polish (~4h)

- [ ] Provision the Oracle Cloud Always Free VM (manual via console; document the steps in `docs/oracle-cloud.md`)
- [ ] Deploy OdooForge to the VM
- [ ] Pick the demo subdomain (DuckDNS, sslip.io, or Cloudflare Tunnel; not a paid TLD)
- [ ] Wire HTTPS via Let's Encrypt or Cloudflare Tunnel
- [ ] Seed the demo with realistic KB articles and a few sample tickets
- [ ] Record a 5-minute Loom walking through the agent flow
- [ ] Update README with the live demo URL and Loom link
- [ ] Save `screenshots/09-oracle-live-demo.png`
- [ ] Commit: `Phase 6: live demo and walkthrough`
- [ ] Run `@portfolio-maintainer dry-run` from the portfolio session

## Known gotchas

- **Odoo memory footprint.** A loaded Odoo 18 worker plus Postgres comfortably fits in 4 GB but feels snappy at 8 GB+. The Always Free Oracle VM at 24 GB RAM has plenty of headroom; a 2 GB laptop will struggle.
- **Odoo's ORM does not natively know pgvector.** Use raw SQL from the addon for vector inserts and similarity search. Document the pattern with comments in the search method so future readers see why it's raw SQL.
- **Terraform multi-cloud discipline is the trap.** It's tempting to ship AWS-only and claim the stack is portable. Phase 5 must actually deploy on Azure or DigitalOcean before the project is presentable. Screenshots from a real second-cloud deploy are non-negotiable.
- **Groq free-tier rate limits.** TPM caps will hit during demo traffic spikes. Cache KB retrieval embeddings, cache tool-call responses where it makes sense, and add a graceful "AI temporarily rate-limited, please try again" fallback on the ticket view.
- **Oracle Cloud account verification.** Identity verification can take 24 hours and may require a credit card hold. Create the account at the start of Phase 4, not Phase 6, so it's ready when you need it.
- **Bandwidth caps on Always Free.** Fine for portfolio demo traffic. Frame the demo URL in the README as "demo, not production." Do not let strangers run load tests against it.
- **Odoo addon installation cache.** If a manifest change is not picked up, Apps menu may need an "Update Apps List" plus a server restart. Document this in `docs/development.md` for future contributors.

## Related memory

Per-project memory lives at `~/.claude/projects/-home-atif-projects-odooforge/memory/`. Read `MEMORY.md` there for the index. The portfolio idea memory (the source of truth that authorized this scaffold) is at `~/.claude/projects/-home-atif-projects-portfolio/memory/project_odooforge.md`.
