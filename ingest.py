from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .types import Document
from .util import read_text_file


def iter_corpus(root_dir: str, globs: list[str], encoding: str) -> Iterable[Document]:
    root = Path(root_dir)
    for g in globs:
        for p in root.glob(g):
            if p.is_dir():
                continue
            rel = p.relative_to(root)
            text = read_text_file(str(p), encoding=encoding)
            yield Document(doc_id=str(rel), source_path=str(p), text=text)
