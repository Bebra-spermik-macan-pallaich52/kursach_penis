"""Извлечь фактические страницы разделов из экспортированного PDF.

python -m scripts.paginate_report
python -m scripts.build_report --page-map docs/evidence/page_map.json
Затем повторно экспортировать DOCX в PDF и проверить неизменность карты.
Нужен системный pdftotext (Poppler).
"""
from pathlib import Path
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
text=subprocess.check_output(['pdftotext','-layout',str(DOCS/'Пояснительная_записка.pdf'),'-'],text=True)
pages=text.split('\f')
if not pages[-1].strip():pages.pop()
titles=[line.lstrip('# ').strip() for line in (DOCS/'REPORT_TEXT.md').read_text(encoding='utf-8').splitlines() if line.startswith('#')]
titles += ['Приложение 1 — Реестр дефектов и ограничений','Приложение 2 — Тестовые сценарии',
           'Приложение 3 — Матрица трассировки','Приложение 4 — Основные листинги',
           'Приложение 5 — Запросы и примеры результатов','Приложение 6 — Рекомендуемая литература']
def normalize(value):
    return re.sub(r'[^0-9a-zа-я]','',value.casefold().replace('ё','е'))
page_map={}
for title in titles:
    match=next((i for i,page in enumerate(pages,1) if i>=4 and normalize(title) in normalize(page)),None)
    if match is None:raise RuntimeError('Не найден раздел: '+title)
    page_map[title]=match
(DOCS/'evidence/page_map.json').write_text(json.dumps(page_map,ensure_ascii=False,indent=2),encoding='utf-8')
print('Страниц:',len(pages),'Разделов в содержании:',len(page_map))
