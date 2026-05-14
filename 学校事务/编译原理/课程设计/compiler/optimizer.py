from typing import Dict, Iterable, List, Optional, Tuple


Quad = Tuple[object, object, object, object]


ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}


def optimize_quads(quads: Iterable[Quad]) -> List[Quad]:
    return QuadOptimizer(list(quads)).optimize()


class QuadOptimizer:
    def __init__(self, quads: List[Quad]):
        self.quads = quads
        self.aliases: Dict[str, object] = {}

    def optimize(self) -> List[Quad]:
        optimized: List[Tuple[int, Quad]] = []

        for index, (op, arg1, arg2, result) in enumerate(self.quads):
            if self._is_function_label(op, arg1, arg2, result):
                self.aliases.clear()
                optimized.append((index, (op, arg1, arg2, result)))
                continue

            if op == "=":
                value = self._resolve(arg1)
                if self._is_temp(result):
                    self.aliases[str(result)] = value
                    continue
                self._forget(result)
                optimized.append((index, ("=", value, "_", result)))
                continue

            if op in ARITHMETIC_OPS:
                left = self._resolve(arg1)
                right = self._resolve(arg2)
                folded = self._fold(str(op), left, right)
                simplified = folded if folded is not None else self._simplify(str(op), left, right)
                if simplified is not None:
                    if self._is_temp(result):
                        self.aliases[str(result)] = simplified
                        continue
                    self._forget(result)
                    optimized.append((index, ("=", simplified, "_", result)))
                    continue
                self._forget(result)
                optimized.append((index, (op, left, right, result)))
                continue

            if str(op).startswith("J"):
                if op == "J":
                    optimized.append((index, (op, arg1, arg2, result)))
                else:
                    optimized.append((index, (op, self._resolve(arg1), self._resolve(arg2), result)))
                self.aliases.clear()
                continue

            if op in {"ret", "return", "para"}:
                optimized.append((index, (op, arg1, arg2, self._resolve(result) if op in {"ret", "return"} else result)))
                continue

            self._forget(result)
            optimized.append((index, (op, self._resolve(arg1), self._resolve(arg2), result)))

        return self._remap_jump_targets(optimized)

    def _remap_jump_targets(self, optimized: List[Tuple[int, Quad]]) -> List[Quad]:
        old_to_new = {old_index: new_index for new_index, (old_index, _quad) in enumerate(optimized)}
        surviving_old_indices = [old_index for old_index, _quad in optimized]
        remapped: List[Quad] = []

        for _old_index, (op, arg1, arg2, result) in optimized:
            if str(op).startswith("J") and isinstance(result, int):
                result = old_to_new.get(result, self._next_surviving_index(result, surviving_old_indices, old_to_new))
            remapped.append((op, arg1, arg2, result))
        return remapped

    def _next_surviving_index(self, old_target: int, surviving_old_indices: List[int], old_to_new: Dict[int, int]) -> int:
        for old_index in surviving_old_indices:
            if old_index >= old_target:
                return old_to_new[old_index]
        return len(surviving_old_indices)

    def _resolve(self, item):
        while isinstance(item, str) and item in self.aliases:
            next_item = self.aliases[item]
            if next_item == item:
                break
            item = next_item
        return item

    def _fold(self, op: str, left, right) -> Optional[str]:
        if not (self._is_integer(left) and self._is_integer(right)):
            return None
        left_value = int(str(left))
        right_value = int(str(right))
        if op == "+":
            return str(left_value + right_value)
        if op == "-":
            return str(left_value - right_value)
        if op == "*":
            return str(left_value * right_value)
        if op == "/" and right_value != 0:
            return str(int(left_value / right_value))
        if op == "%" and right_value != 0:
            return str(left_value % right_value)
        return None

    def _simplify(self, op: str, left, right):
        if op == "+" and right == "0":
            return left
        if op == "+" and left == "0":
            return right
        if op == "-" and right == "0":
            return left
        if op == "*" and right == "1":
            return left
        if op == "*" and left == "1":
            return right
        if op == "*" and (left == "0" or right == "0"):
            return "0"
        if op == "/" and right == "1":
            return left
        if op == "%" and right == "1":
            return "0"
        return None

    def _forget(self, item) -> None:
        if isinstance(item, str):
            self.aliases.pop(item, None)

    def _is_function_label(self, op, arg1, arg2, result) -> bool:
        return (
            isinstance(op, str)
            and arg1 == "_"
            and arg2 == "_"
            and result == "_"
            and op not in {"J", "sys", "ret", "return"}
        )

    def _is_temp(self, item) -> bool:
        return isinstance(item, str) and item.startswith("t") and item[1:].isdigit()

    def _is_integer(self, item) -> bool:
        return isinstance(item, (int, str)) and str(item).lstrip("-").isdigit()
