# Theme, contrast, and job progress

## Goals

- **One consistent look** for the first-run wizard, unlock dialog, `QMessageBox`, and main window.
- **Readable contrast** for text fields, titles, and buttons on Windows (Fusion + explicit QSS).
- **Visible feedback** for long-running work without forcing users to watch only the job dock table.

## Theme pipeline

| Step | Location | Behavior |
|------|----------|----------|
| Palette / style | `crawlix.ui.theme.apply_application_palette` | Sets **Fusion** for predictable cross-platform styling. |
| Stylesheet | `crawlix.ui.theme.apply_application_theme` | Loads **`app_dark.qss`** or **`app_light.qss`** onto **`QApplication`**. |
| Entry point | `crawlix.main.main` | Applies palette + theme **before** `MainWindow()` so early dialogs inherit QSS. |
| Persistence | DB `settings.ui_theme` + `QSettings` | `sync_theme_to_qsettings` keeps OS-level settings aligned when the user changes theme in **Settings**. |

Stylesheets live under `src/crawlix/ui/styles/`. **`MainWindow._reload_styles`** reapplies the theme to the whole application when the user toggles dark/light.

## Labels and rich text

Page titles use **plain `QLabel` text** with a bold font instead of embedding **HTML** (`<h2>`), because Qt treats HTML labels as rich text with its own color rules that can clash with dark QSS.

## Job progress

### Persisted jobs (`jobs` table)

- **Crawl** and **audit** workers run on **`QThreadPool`** as **`QRunnable`** implementations.
- They emit **`JobBus.progress(job_id, pct, message)`** for live updates (audit already stepped per page; crawl uses **`on_progress`** from `run_crawl_job`).
- **`JobBus.finished`** / **`JobBus.failed`** drive completion and error handling on the GUI thread.

### SERP snapshots

- **SERP** runs in **`SerpWorker`**, which creates/updates a **`Job`** with `type="serp"` and payload `keyword_id`, then emits the same **`progress` / `finished` / `failed`** signals as other workers.

### Ephemeral UI tasks

- **Markdown export** and **Help → Check for updates** use **`SimpleTaskWorker`** with **`JobBus.task_*`** signals so the UI does not block on network or disk I/O.
- **Convention:** `task_progress(task_id, pct, msg)` — if **`pct < 0`**, the UI treats the bar as **indeterminate** (`QProgressBar` range `0..0`).

### On-page widgets

The **Crawl**, **Audit**, and **Keywords → SERP** pages each expose a **`QProgressBar`** and status **`QLabel`**. While a job started from that page is active, the primary action button is **disabled**; it is re-enabled when the job completes or fails.

`QProgressBar` is styled in both dark and light QSS files for visible chunk and border colors.
