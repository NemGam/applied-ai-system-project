import re
from pathlib import Path
from typing import Dict, List


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _phrase_in_text(text: str, phrase: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, normalized) is not None


def _append_unique(items: List[str], value: str) -> None:
    normalized = value.strip().lower()
    if normalized and normalized not in items:
        items.append(normalized)


def _merge_targets(targets: Dict[str, List[float]], additions: Dict[str, float]) -> None:
    for key, value in additions.items():
        targets.setdefault(key, []).append(float(value))


def _average_targets(targets: Dict[str, List[float]]) -> Dict[str, float]:
    averaged: Dict[str, float] = {}
    for key, values in targets.items():
        if not values:
            continue
        averaged[key] = round(sum(values) / len(values), 3)
    return averaged


def _closeness(song_value: float, target_value: float, tolerance: float) -> float:
    return max(0.0, 1.0 - abs(song_value - target_value) / tolerance)


def load_lyrics_index(lyrics_dir: str | Path) -> Dict[int, str]:
    lyrics_root = Path(lyrics_dir)
    lyrics_by_song_id: Dict[int, str] = {}
    if not lyrics_root.exists():
        return lyrics_by_song_id

    for path in lyrics_root.glob("*.txt"):
        try:
            song_id = int(path.stem)
        except ValueError:
            continue
        lyrics_by_song_id[song_id] = path.read_text(encoding="utf-8")

    return lyrics_by_song_id
