---
name: obs-setup
description: Guide osc installation, private credential setup, read-only OBS access checks, and optional workspace configuration for an internal OBS instance.
argument-hint: "[internal-api-url]"
---

# OBS Setup

Read [setup-obs](../skills/setup-obs/SKILL.md) explicitly before acting. Resolve the link from this command's installed plugin directory, not from the consuming workspace. Use its platform checks, approval gates, private-terminal handoff, and verification procedure.

Treat arguments as a proposed API URL only. Validate and confirm it before use. Never accept credentials in command arguments or chat. An empty argument starts the guided questions; it must not select a public server.

This command guides configuration on the user's system. It is not a login script and cannot receive secrets. Do not execute credential setup in an agent terminal. No package upload, submission, build, or OBS metadata change is part of setup.
