# seppou

**seppou** (Japanese: "説法") is an abstraction system that uses LLMs to convert real-time system states into emotional expressions.

## engi ("縁起")

A reverse proxy server. It acts as a gateway, forwarding requests between the frontend and the `shiki` backend, and serves as an aggregation point for system logs.

### Usage

```bash
cd engi
go run main.go
```

## shiki ("識")

Generates emotional text using LLMs based on system data, transforming technical states into human-relatable expressions.

### Usage

```bash
cd shiki
uv sync
uv run src/main.py
```

## zen ("禅")

Provides an SNS-style interface that visualizes the generated emotional expressions in real-time, bridging technical data and human understanding.

### Usage

```bash
cd zen
bun install
bun start
```
