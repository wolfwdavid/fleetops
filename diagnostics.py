"""Decision-tree fault-isolation engine.

The tree lives in data/decision_tree.json so technicians can extend it
without touching code. Two modes:

  interactive — walks the tech through yes/no questions at the console
  auto        — replays a recorded answer sequence (e.g. "y,n,y") for
                scripting, testing, and documentation screenshots
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models import DATA_DIR

TREE_PATH = DATA_DIR / "decision_tree.json"


@dataclass
class DiagnosisResult:
    path: list[tuple[str, str]]  # (question, answer) pairs in order
    diagnosis: str
    category: str
    actions: list[str]


def load_tree(path: Path = TREE_PATH) -> dict:
    tree = json.loads(path.read_text(encoding="utf-8"))
    _validate(tree)
    return tree


def _validate(tree: dict) -> None:
    """Every branch must terminate at a leaf; fail loudly on a broken tree."""
    nodes = tree["nodes"]
    if tree["root"] not in nodes:
        raise ValueError(f"Root node '{tree['root']}' not found")
    for node_id, node in nodes.items():
        if "diagnosis" in node:
            continue
        for branch in ("yes", "no"):
            target = node.get(branch)
            if target not in nodes:
                raise ValueError(f"Node '{node_id}' branch '{branch}' -> missing node '{target}'")


def _walk(tree: dict, answer_fn) -> DiagnosisResult:
    nodes = tree["nodes"]
    node_id = tree["root"]
    path: list[tuple[str, str]] = []
    while True:
        node = nodes[node_id]
        if "diagnosis" in node:
            return DiagnosisResult(
                path=path,
                diagnosis=node["diagnosis"],
                category=node["category"],
                actions=list(node["actions"]),
            )
        answer = answer_fn(node["question"])
        path.append((node["question"], "yes" if answer else "no"))
        node_id = node["yes"] if answer else node["no"]


def run_auto(tree: dict, answers: list[bool]) -> DiagnosisResult:
    """Replay a recorded answer sequence. Raises if the sequence is too short."""
    it = iter(answers)

    def answer_fn(question: str) -> bool:
        try:
            return next(it)
        except StopIteration:
            raise ValueError(
                f"Answer sequence exhausted at question: {question!r}"
            ) from None

    return _walk(tree, answer_fn)


def run_interactive(tree: dict) -> DiagnosisResult:
    def answer_fn(question: str) -> bool:
        while True:
            reply = input(f"{question} [y/n] ").strip().lower()
            if reply in ("y", "yes"):
                return True
            if reply in ("n", "no"):
                return False
            print("Please answer y or n.")

    return _walk(tree, answer_fn)


def parse_answers(spec: str) -> list[bool]:
    """'y,n,y' -> [True, False, True]"""
    out = []
    for tok in spec.split(","):
        tok = tok.strip().lower()
        if tok in ("y", "yes"):
            out.append(True)
        elif tok in ("n", "no"):
            out.append(False)
        else:
            raise ValueError(f"Bad answer token {tok!r}; use y/n")
    return out
