# Vision

WP Core Radar is intended to become a practical portfolio-quality contribution intelligence tool.

The long-term goal is not to replace human judgment. The goal is to make contribution discovery faster, more explainable, and easier to repeat.

## Product direction

Radar should make it easy to:

- find contribution opportunities that match available time and skill level
- understand why a ticket ranked highly
- avoid repeatedly reviewing tickets that have already been rejected, watched, tested, or completed
- record props after contributor credit appears on WordPress.org
- copy useful review context for deeper human evaluation
- keep a visible record of contribution intent, follow-through, and outcomes

## Technical direction

The project should remain:

- deterministic before any AI-assisted review
- transparent about scoring reasons
- small enough to understand quickly
- safe by default
- respectful of WordPress.org resources and contribution norms

## Public/private split

The public dashboard should be a polished, read-only artifact. The public contribution-history page should summarize safe review and props outcomes without exposing admin notes or write access.

The admin console should remain protected because it writes review state and supports the human review workflow. The public dashboard should stay read-only, while `/admin/` should remain narrowly scoped to authenticated review metadata and historical props updates.

## Portfolio domain direction

`radar.james.bregenzer.dev` is the dedicated production host for WP Core Radar. The same Worker-router pattern can later be reused on `james.bregenzer.dev` if that broader portfolio domain mounts multiple projects under paths such as `/radar/`, `/darkrai/`, or `/tools/`.

This lets Radar remain its own focused repository while still fitting into a broader personal portfolio architecture later.
