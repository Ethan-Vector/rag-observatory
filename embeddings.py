from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Embedder:
    dim: int = 384

    def embed(self, text: str) -> list[float]:
        """
        Embedding deterministico senza ML:
        - tokenizza in modo grossolano
        - hashing in dim bucket
        - L2 normalize
        """
        vec = [0.0] * self.dim
        tokens = [t for t in _simple_tokens(text) if t]
        if not tokens:
            return vec

        for t in tokens:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # 2 bytes -> bucket
            b = int.from_bytes(h[:2], "big") % self.dim
            # signed-ish weight from next byte
            w = (h[2] / 255.0) * 2.0 - 1.0
            vec[b] += w

        # L2 norm
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


def _simple_tokens(text: str) -> list[str]:
    # cheap tokenizer: lowercase, split on non-alnum
    out = []
    cur = []
    for ch in text.lower():
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))
    return out
