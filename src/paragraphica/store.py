"""The history store: every generation becomes an image file plus one JSON line.

`output/history.jsonl` is append-only; the images sit next to it. Nothing here
talks to a model, so it is fully testable with a temporary directory."""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from paragraphica.core import Request, Result

EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
HISTORY = "history.jsonl"


@dataclass(frozen=True)
class Record:
    timestamp: str  # ISO 8601, local time
    location: str  # what the user typed, or "" when lat/lon were given
    address: str
    lat: float
    lon: float
    style: str
    context: str
    position: str
    quality: str
    time_of_day: str
    weather: str
    description: str
    prompt: str
    revised_prompt: str | None
    backend: str
    text_model: str
    image_model: str
    image: str  # file name relative to the store root
    duration_s: float
    wander_m: float = 0.0
    caption: bool = False
    cost: float | None = None  # USD per image, when the backend reports it (#38)
    era: str = ""  # the age dial, "" = today (#47)
    nickname: str = ""  # who took it (#48)
    source: str = ""  # cli | wall | phone (#48)
    extra: dict = field(default_factory=dict)


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "image"


class Store:
    def __init__(self, root: Path = Path("output")):
        self.root = Path(root)

    @property
    def history_path(self) -> Path:
        return self.root / HISTORY

    def _image_path(self, stamp: datetime, slug: str, ext: str) -> Path:
        base = f"{stamp:%Y%m%d-%H%M%S}-{slug}"
        path = self.root / f"{base}{ext}"
        n = 2
        while path.exists():
            path = self.root / f"{base}-{n}{ext}"
            n += 1
        return path

    def save(
        self,
        req: Request,
        result: Result,
        *,
        backend: str,
        text_model: str,
        image_model: str,
        location: str = "",
        now: datetime | None = None,
    ) -> Record:
        """Write the image and append the record. Returns the record."""
        if result.image is None:
            raise ValueError("nothing to store: result has no image (dry run?)")
        stamp = now or datetime.now().astimezone()
        self.root.mkdir(parents=True, exist_ok=True)
        ext = EXTENSIONS.get(result.mime_type, ".bin")
        path = self._image_path(stamp, slugify(f"{result.context.address.split(',')[0]}-{req.style}"), ext)
        path.write_bytes(result.image)
        rec = Record(
            timestamp=stamp.isoformat(timespec="seconds"),
            location=location,
            address=result.context.address,
            lat=result.context.lat or req.lat,
            lon=result.context.lon or req.lon,
            style=req.style,
            context=req.context,
            position=req.position,
            quality=req.quality,
            time_of_day=result.context.time_of_day,
            weather=result.context.weather,
            description=result.description,
            prompt=result.prompt,
            revised_prompt=result.revised_prompt,
            backend=backend,
            text_model=text_model,
            image_model=image_model,
            image=path.name,
            duration_s=round(result.duration_s, 1),
            wander_m=req.wander_m,
            caption=req.caption,
            cost=result.cost,
            era=req.era or "",
            nickname=req.nickname,
            source=req.source,
        )
        with self.history_path.open("a", encoding="utf-8") as f:
            data = asdict(rec)
            data.pop("extra")  # read-side only: holds keys a newer version may add
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return rec

    def records(self) -> list[Record]:
        """All records, oldest first. Unknown keys from future versions land in `extra`."""
        if not self.history_path.exists():
            return []
        known = set(Record.__dataclass_fields__) - {"extra"}
        out = []
        for line in self.history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            extra = {k: raw.pop(k) for k in list(raw) if k not in known}
            out.append(Record(**raw, extra=extra))
        return out
