# Производные файлы (assets/processed)

Здесь лежат только **производные** материалы, созданные из оригиналов скриптом `tools/generate_derived.py`
(задача issue #2). Оригиналы в `assets/source/`, `assets/portfolio/`, `assets/process/`, `assets/concepts/` не изменялись.

- `web/` — веб-копии JPEG (длинная сторона ≤1600 px, q80, progressive). Имена: `pNN-слаг.jpg`, связь с оригиналом — в `docs/assets-manifest.json`.
- `thumbs/` — миниатюры (≤480 px). Та же схема имён.
- `contact-sheets/` — контактные листы с ID P01–P46, именами файлов и статусами (как просматривать — в `docs/AUDIT_REPORT.md`).
- `heic-working/` — (по запросу) полноформатные JPEG-рабочие копии HEIC-исходников для редакторов, которые не открывают HEIC. В Git не коммитятся; создаются командой `python3 tools/generate_derived.py --heic-working`.

Пересборка: `python3 tools/generate_derived.py` (нужны `pillow` и `pillow-heif`).
