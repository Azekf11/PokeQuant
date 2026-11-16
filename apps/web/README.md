# Web demo

A static page that shows the results in six steps for fourteen sets: the three
main sets (main run), the seven sets added by the ten-set extension and the four
Mega Evolution sets (central layout). It
has no backend and no third-party script ([ADR 0013](../../docs/decisions/0013-static-web-demo.md)).

| File | Role |
|---|---|
| `index.html`, `style.css`, `app.js` | The page. |
| `data/results.json` | Aggregates written by `scripts/export_web.py`; no per-card price (ADR 0009). |
| `data/results.js` | The same data as a script, loaded by the page (no request at run time). |

Regenerate the data after a new run, then open the page:

```bash
uv run python scripts/export_web.py results/main-94de09e8-k200-m20000 \
  results/extension_sets-f3420df5-k200-m20000 results/mega_sets-64f9087d-k200-m20000
python3 -m http.server 8000 --directory apps/web
```

The page is deployed to GitHub Pages by `.github/workflows/pages.yml` on every
push to `main` that changes `apps/web/`.
