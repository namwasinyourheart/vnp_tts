from pathlib import Path


def parse_existing(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    if not path.exists():
        return entries

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if " | " not in line:
            continue
        key, value = line.split(" | ", 1)
        key = key.strip()
        value = value.strip()
        if key and value and key not in entries:
            entries[key] = value
    return entries


def normalize_phrase(text: str) -> str:
    text = " ".join(text.split())
    if not text:
        return text
    return text[0].upper() + text[1:]


def parse_acronyms(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" not in line:
            continue

        key, value = line.split("#", 1)
        key = key.strip()
        value = normalize_phrase(value.strip())
        if not key or not value:
            continue

        key = key.upper()
        entries.setdefault(key, value)
    return entries


def write_output(path: Path, entries: dict[str, str]) -> None:
    lines = [f"{key} | {entries[key]}" for key in sorted(entries)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = Path(__file__).resolve().parent
    src = base / "Acronyms.txt"
    dst = base / "abbreviation.txt"

    merged = parse_acronyms(src)

    existing = parse_existing(dst)
    for key, value in existing.items():
        merged[key] = value

    write_output(dst, merged)
    print(f"Wrote {len(merged)} entries to {dst}")


if __name__ == "__main__":
    main()
