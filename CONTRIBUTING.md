# Contributing

Documentation map (overview + all doc links): **[INDEX.md](INDEX.md)**.

## Dev setup

```bash
pip install -e ".[dev]"
ruff check src tests
pytest tests/ -q
```

## Database migrations

1. Edit SQLAlchemy models in `src/crawlix/db/models.py`.
2. Generate a revision (or hand-write for clarity):

   ```bash
   python -m alembic revision --autogenerate -m "describe change"
   ```

3. Review the migration; **never** edit applied migrations in production.
4. CI runs `alembic upgrade head` against a temporary SQLite file.

## i18n

User-visible strings should use `self.tr()` in widgets. Glossary: [docs/ui/glossary.md](docs/ui/glossary.md).

## Citation YAML packs

Placeholders must match [docs/citation-placeholders.md](docs/citation-placeholders.md). Validate in CI when adding rows to `resources/citation_sources_default.yaml`.

## PR checklist

- [ ] Tests or rationale for omission
- [ ] No `verify=False` / no secrets in code
- [ ] README or docs updated if behavior changed
