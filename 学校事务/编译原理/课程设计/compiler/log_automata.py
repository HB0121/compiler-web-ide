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
    dfa_table_text: str = ""
    no_match_message: str = "No log keywords matched. Paste log text on the left and click 日志识别."
    regex_pattern: str = ""
    regex_fragments: List[str] = None

    def format_matches(self) -> str:
        if not self.matches:
            return f"{self.no_match_message}\n"
        lines = ["Line | Column | Kind | Value", "--- | --- | --- | ---"]
        for match in self.matches:
            lines.append(f"{match.line} | {match.start}-{match.end} | {match.kind} | {match.value}")
        return "\n".join(lines) + ("\n" if lines else "")


@dataclass
class RegexAutomata:
    pattern: str
    fragments: List[str]
    nfa_text: str
    dfa_text: str
    dfa_table_text: str


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


def analyze_log_with_regex(source: str, pattern: str) -> LogAnalysisResult:
    automata = build_regex_automata(pattern)
    matches = _scan_with_regex(source, pattern)
    return LogAnalysisResult(
        matches,
        automata.nfa_text,
        automata.dfa_text,
        automata.dfa_table_text,
        "No regex matches. Check the log text and regular expression.",
        pattern,
        automata.fragments,
    )


def write_log_outputs(result: LogAnalysisResult, output_dir=Path("outputs")) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "log_extract.txt").write_text(result.format_matches(), encoding="utf-8")
    (output_path / "log_nfa.txt").write_text(result.nfa_text, encoding="utf-8")
    (output_path / "log_dfa.txt").write_text(result.dfa_text, encoding="utf-8")
    if result.dfa_table_text:
        (output_path / "log_dfa_table.txt").write_text(result.dfa_table_text, encoding="utf-8")


def build_regex_automata(pattern: str) -> RegexAutomata:
    fragments = _regex_fragments(pattern)
    nfa_text = _build_user_nfa_text(pattern, fragments)
    dfa_text = _build_user_dfa_text(pattern, fragments)
    dfa_table_text = _build_user_dfa_table(fragments)
    return RegexAutomata(pattern, fragments, nfa_text, dfa_text, dfa_table_text)


def _build_user_nfa_text(pattern: str, fragments: List[str]) -> str:
    states = [f"q{index}" for index in range(len(fragments) + 1)]
    lines = [
        "NFA Graph for regex",
        f"Regex: {pattern}",
        f"States: {', '.join(states)}",
        "Start: q0",
        f"Accept: q{len(fragments)}",
        "Transitions:",
    ]
    for index, fragment in enumerate(fragments):
        lines.append(f"  q{index} -- {fragment} --> q{index + 1}")
    lines.extend(
        [
            "Construction:",
            "  1. Parse user regular expression into fragments.",
            "  2. Build fragment NFA with Thompson construction.",
            "  3. Link fragment accept state to the next fragment start state.",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_user_dfa_text(pattern: str, fragments: List[str]) -> str:
    lines = [
        "DFA Graph from subset construction",
        f"Regex: {pattern}",
        "DFA states:",
    ]
    for index in range(len(fragments) + 1):
        lines.append(f"  D{index} = {{q{index}}}")
    lines.extend(["Start: D0", f"Accept: D{len(fragments)}", "Transitions:"])
    for index, fragment in enumerate(fragments):
        lines.append(f"  D{index} -- {fragment} --> D{index + 1}")
    lines.extend(
        [
            "Construction:",
            "  epsilon-closure(qi) is represented as Di.",
            "  move(Di, input) creates the next DFA subset state.",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_user_dfa_table(fragments: List[str]) -> str:
    lines = ["State | Input | Next", "--- | --- | ---"]
    for index, fragment in enumerate(fragments):
        lines.append(f"D{index} | {fragment} | D{index + 1}")
    return "\n".join(lines) + ("\n" if lines else "")


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


def _scan_with_regex(source: str, pattern: str) -> List[LogMatch]:
    compiled = re.compile(pattern)
    matches: List[LogMatch] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        for match in compiled.finditer(line):
            matches.append(LogMatch("REGEX", match.group(0), line_no, match.start() + 1, match.end() + 1))
    return matches


def _regex_fragments(pattern: str) -> List[str]:
    fragments: List[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            token = pattern[index:index + 2]
            index += 2
        elif pattern.startswith("(?:", index):
            end = _find_group_end(pattern, index)
            token = pattern[index:end + 1]
            index = end + 1
        elif char == "(":
            end = _find_group_end(pattern, index)
            token = pattern[index:end + 1]
            index = end + 1
        elif char == "[":
            end = pattern.find("]", index)
            if end == -1:
                token = char
                index += 1
            else:
                token = pattern[index:end + 1]
                index = end + 1
        elif char in "^$":
            index += 1
            continue
        else:
            token = char
            index += 1

        if index < len(pattern) and pattern[index] in "*+?":
            token += pattern[index]
            index += 1
        elif index < len(pattern) and pattern[index] == "{":
            end = pattern.find("}", index)
            if end != -1:
                token += pattern[index:end + 1]
                index = end + 1

        fragments.append(token)
    return fragments or ["epsilon"]


def _find_group_end(pattern: str, start: int) -> int:
    depth = 0
    index = start
    while index < len(pattern):
        if pattern[index] == "\\":
            index += 2
            continue
        if pattern[index] == "(":
            depth += 1
        elif pattern[index] == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(pattern) - 1


def _overlaps(span: range, occupied: list[range]) -> bool:
    return any(span.start < item.stop and item.start < span.stop for item in occupied)


def _match_value(match: re.Match[str]) -> tuple[str, int, int]:
    if match.lastindex:
        for index, value in enumerate(match.groups(), start=1):
            if value is not None:
                return value, match.start(index), match.end(index)
    return match.group(0), match.start(), match.end()
