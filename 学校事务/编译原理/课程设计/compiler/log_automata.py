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
        fragments = _rule_fragments(rule.kind)
        states = [f"{rule.kind}_N{index}" for index in range(len(fragments) + 1)]
        lines.append(f"NFA for {rule.kind}")
        lines.append(f"  regex: {rule.pattern}")
        lines.append(f"  States: {', '.join(states)}")
        lines.append(f"  Start: {states[0]}")
        lines.append(f"  Accept: {states[-1]}")
        lines.append("  Transitions:")
        for index, fragment in enumerate(fragments):
            lines.append(f"    {states[index]} -- {fragment} --> {states[index + 1]}")
        lines.append("  Construction:")
        lines.append("    regular expression fragments are linked by Thompson-style NFA transitions.")
        lines.append("    alternatives are represented by character-class or keyword-set edges.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_dfa_text(rules: Iterable[LogRule]) -> str:
    lines: List[str] = []
    for rule in rules:
        fragments = _rule_fragments(rule.kind)
        lines.append(f"DFA for {rule.kind}")
        lines.append("  DFA states from NFA subsets:")
        for index in range(len(fragments) + 1):
            lines.append(f"    D{index} = {{{rule.kind}_N{index}}}")
        lines.append("  Start: D0")
        lines.append(f"  Accept: D{len(fragments)} emits {rule.kind}")
        lines.append("  Transitions:")
        for index, fragment in enumerate(fragments):
            lines.append(f"    D{index} -- {fragment} --> D{index + 1}")
        lines.append("  Construction:")
        lines.append("    each DFA state is the epsilon-closure subset reached from the previous NFA fragment.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _rule_fragments(kind: str) -> List[str]:
    fragments = {
        "DATE": ["DIGIT{4}", "'-'", "DIGIT{2}", "'-'", "DIGIT{2}"],
        "TIME": ["DIGIT{2}", "':'", "DIGIT{2}", "':'", "DIGIT{2}"],
        "LEVEL": ["TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL"],
        "IP": ["DIGIT{1,3}", "'.'", "DIGIT{1,3}", "'.'", "DIGIT{1,3}", "'.'", "DIGIT{1,3}"],
        "STATUS": ["status=|STATUS:|epsilon", "STATUS_DIGIT{3}"],
        "USER": ["user=|USER:", "LETTER|_", "(LETTER|DIGIT|_)*"],
        "ACTION": ["action=|ACTION:", "LETTER|_", "(LETTER|DIGIT|_)*"],
    }
    return fragments.get(kind, [kind])


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
