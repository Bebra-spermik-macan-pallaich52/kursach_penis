# Пересборка пояснительной записки

Основной текст редактируется в REPORT_TEXT.md, реквизиты — report_metadata.json.
Дополнительные таблицы берутся из DATA_DICTIONARY.md, TESTING.md и test-cases.json;
схемы и снимки уже включены в комплект. Листинги берутся из текущих исходников.
Markdown Пояснительная_записка.md содержит развёрнутый текст основной части;
приложения и титульный лист добавляются генератором.

Из корня проекта с установленными requirements-lock.txt:

```bash
python -m scripts.build_report
soffice --headless --convert-to pdf --outdir docs docs/Пояснительная_записка.docx
python -m scripts.paginate_report
python -m scripts.build_report --page-map docs/evidence/page_map.json
soffice --headless --convert-to pdf --outdir docs docs/Пояснительная_записка.docx
```

LibreOffice и Poppler (pdftotext) — внешние инструменты пересборки, для работы API
они не нужны. Для окончательной печати предпочтительно открыть DOCX в Word
с установленным Times New Roman и экспортировать PDF. При изменении вёрстки
повторно проверьте карту страниц и содержание. Обычное обновление поля PAGE
в Word сохраняет сквозную нумерацию листов; содержание в комплекте заполняется
по фактическому экспортированному PDF, а не является полем автоматического TOC.

Снимки Swagger сделаны на работающем сервере, сведения тестов — из pytest/JUnit.
При новом прогоне обновляйте также metrics.json и тестовый раздел записки;
не переносите старую статистику на изменённую версию без повторной проверки.
