"""Собрать передаваемый комплект без среды, ключей и пользовательских данных."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
excluded_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", "htmlcov"}
files = []
for path in sorted(ROOT.rglob("*")):
    relative = path.relative_to(ROOT)
    if not path.is_file() or any(part in excluded_dirs for part in relative.parts):
        continue
    if path.name in {".env", ".coverage", "MANIFEST.sha256"}:
        continue
    if path.name.startswith(".~lock.") or path.suffix in {".tmp", ".log", ".pyc"}:
        continue
    if relative.parts[0] == "storage" and path.name != ".gitkeep":
        continue
    files.append(path)

manifest = ROOT / "MANIFEST.sha256"
manifest.write_text("\n".join(sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(ROOT).as_posix()
                              for p in files) + "\n", encoding="utf-8")
files.append(manifest)
target = ROOT / "dist"
target.mkdir(exist_ok=True)
archive_path = target / "Курсовой_проект_Пеннер_FastAPI_этап_1.zip"
with ZipFile(archive_path, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        archive.write(path, "kursach_fastapi/" + path.relative_to(ROOT).as_posix())

with ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert not any(Path(name).name == ".env" for name in names)
    assert not any("/.venv/" in name or "/.git/" in name for name in names)
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        assert sha256(archive.read("kursach_fastapi/" + name)).hexdigest() == digest, name

digest = sha256(archive_path.read_bytes()).hexdigest()
archive_path.with_suffix(".zip.sha256").write_text(digest + "  " + archive_path.name + "\n", encoding="utf-8")
print("Архив:", archive_path)
print("Файлов:", len(files), "Размер:", archive_path.stat().st_size, "байт")
print("Проверены ZIP и все контрольные суммы")

