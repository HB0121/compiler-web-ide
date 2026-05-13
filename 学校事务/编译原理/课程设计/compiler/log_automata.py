from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List, Pattern


@dataclass(frozen=True)
class LogRule:
    kind: str
    pattern: str
    description: str


@dataclass(frozen=True)
class LogMatch:
    kind: str
    value: str
    line: int
    start: int
    end: int


@dataclass
class LogAnalysisResult:
    matches: List[LogMatch]
    nfa_text: str
    dfa_text: str

    def format_matches(self) -> str:
        if not self.matches:
            return "No log keywords matched. Paste log text on the left and click 日志识别.\n"
        lines = [f"{match.value} {match.kind}" for match in self.matches]
        return "\n".join(lines) + ("\n" if lines else "")


LOG_RULES = (
    LogRule("DATE", r"\b\d{4}-\d{2}-\d{2}\b", "yyyy-mm-dd"),
    LogRule("TIME", r"\b\d{2}:\d{2}:\d{2}\b", "hh:mm:ss"),
    LogRule("LEVEL", r"\b(?:TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\b", "log level"),
    LogRule("IP", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IPv4 address"),
    LogRule("STATUS", r"\bstatus=(\d{3})\b|\bSTATUS:\s*(\d{3})\b|(?<![\d.])\b[1-5]\d{2}\b(?![\d.])", "HTTP/status code"),
    LogRule("USER", r"\buser=([A-Za-z_][A-Za-z0-9_]*)\b|\bUSER:\s*([A-Za-z_][A-Za-z0-9_]*)\b", "user name"),
    LogRule("ACTION", r"\baction=([A-Za-z_][A-Za-z0-9_]*)\b|\bACTION:\s*([A-Za-z_][A-Za-z0-9_]*)\b", "action name"),
)


def analyze_logs(source: str, rules: Iterable[LogRule] = LOG_RULES) -> LogAnalysisResult:
    active_rules = tuple(rules)
    matches = _scan(source, active_rules)
    return LogAnalysisResult(matches, build_nfa_text(active_rules), build_dfa_text(active_rules))


def write_log_outputs(result: LogAnalysisResult, output_dir=Path("outputs")) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "log_extract.txt").write_text(result.format_matches(), encoding="utf-8")
    (output_path / "log_nfa.txt").write_text(result.nfa_text, encoding="utf-8")
    (output_path / "log_dfa.txt").write_text(result.dfa_text, encoding="utf-8")


def build_nfa_text(rules: Iterable[LogRule]) -> str:
    lines: List[str] = []
    for rule in rules:
        lines.append(f"NFA for {rule.kind}")
        lines.append(f"  regex: {rule.pattern}")
        lines.append("  start --regex-fragment--> accept")
        lines.append("  epsilon transitions connect fragments when alternation or repetition is used.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_dfa_text(rules: Iterable[LogRule]) -> str:
    lines: List[str] = []
    for rule in rules:
        lines.append(f"DFA for {rule.kind}")
        lines.append("  constructed by subset construction from the NFA epsilon-closures.")
        lines.append("  D0 = epsilon-closure(start)")
        lines.append(f"  accepting states emit token {rule.kind}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _scan(source: str, rules: Iterable[LogRule]) -> List[LogMatch]:
    compiled = [(rule, re.compile(rule.pattern)) for rule in rules]
    matches: List[LogMatch] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        occupied: list[range] = []
        for rule, pattern in compiled:
            for match in pattern.finditer(line):
                value, start, end = _match_value(match)
                span = range(start, end)
                if _overlaps(span, occupied):
                    continue
                occupied.append(span)
                matches.append(LogMatch(rule.kind, value, line_no, start + 1, end + 1))
    matches.sort(key=lambda item: (item.line, item.start, item.kind))
    return matches


def _overlaps(span: range, occupied: list[range]) -> bool:
    return any(span.start < item.stop and item.start < span.stop for item in occupied)


def _match_value(match: re.Match[str]) -> tuple[str, int, int]:
    if match.lastindex:
        for index, value in enumerate(match.groups(), start=1):
            if value is not None:
                return value, match.start(index), match.end(index)
    return match.group(0), match.start(), match.end()
