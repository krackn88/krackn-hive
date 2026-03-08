import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyViolation:
    code: str
    message: str


class PolicyEngine:
    def __init__(self) -> None:
        self._deny = [
            ("DANGEROUS_SHELL", re.compile(r"\brm\s+-rf\b", re.IGNORECASE)),
            ("NETWORK_EXFIL", re.compile(r"\bcurl\b|\bwget\b|\bnc\b", re.IGNORECASE)),
        ]

    def check_text(self, text: str) -> list[PolicyViolation]:
        out: list[PolicyViolation] = []
        for code, pattern in self._deny:
            if pattern.search(text):
                out.append(PolicyViolation(code=code, message=f"matched {code}"))
        return out
