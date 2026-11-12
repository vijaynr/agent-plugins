# OKF Skills

After installing the OKF plugin, use `/okf-init` to create a catalog, `/okf-ingest` to propose knowledge from supplied content, and `/okf-validate` to check it. Review the diff before approving any write.

- `okf-toolkit` is the self-contained authoring, ingestion, validation, and
  export skill. It owns the portable CLI and shared helpers under `scripts/`.
- `using-okf-knowledge` teaches agents to consume a repository catalog.

The `/okf-init`, `/okf-ingest`, `/okf-validate`, and `/okf-export` commands map
to modes of `okf-toolkit` rather than separate script-owning skills.
