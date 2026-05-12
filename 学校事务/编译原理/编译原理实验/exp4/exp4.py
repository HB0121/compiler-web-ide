import re
import sys

# ==========================================
# 1. 抽象语法树 (AST) 节点定义
# ==========================================
class ASTNode: pass
class Program(ASTNode):
    def __init__(self, nodes): self.nodes = nodes
class FuncDef(ASTNode):
    def __init__(self, name, body): self.name = name; self.body = body
class Block(ASTNode):
    def __init__(self, stmts): self.stmts = stmts
class VarDecl(ASTNode):
    def __init__(self, name, value): self.name = name; self.value = value
class Assign(ASTNode):
    def __init__(self, var, expr): self.var = var; self.expr = expr
class BinOp(ASTNode):
    def __init__(self, op, left, right): self.op = op; self.left = left; self.right = right
class UnaryOp(ASTNode):
    def __init__(self, op, expr): self.op = op; self.expr = expr
class RelOp(ASTNode):
    def __init__(self, op, left, right): self.op = op; self.left = left; self.right = right
class LogicalAnd(ASTNode):
    def __init__(self, left, right): self.left = left; self.right = right
class LogicalOr(ASTNode):
    def __init__(self, left, right): self.left = left; self.right = right
class LogicalNot(ASTNode):
    def __init__(self, expr): self.expr = expr
class Identifier(ASTNode):
    def __init__(self, name): self.name = name
class Constant(ASTNode):
    def __init__(self, val): self.val = str(val)
class Return(ASTNode):
    def __init__(self, expr): self.expr = expr
class Break(ASTNode): pass
class Continue(ASTNode): pass
class If(ASTNode):
    def __init__(self, cond, true_block, false_block=None):
        self.cond = cond; self.true_block = true_block; self.false_block = false_block
class While(ASTNode):
    def __init__(self, cond, body): self.cond = cond; self.body = body
class DoWhile(ASTNode):
    def __init__(self, body, cond): self.body = body; self.cond = cond
class For(ASTNode):
    def __init__(self, init, cond, step, body):
        self.init = init; self.cond = cond; self.step = step; self.body = body
class FuncCall(ASTNode):
    def __init__(self, name, args): self.name = name; self.args = args

# ==========================================
# 2. 中间代码生成器 (四元式与混合拉链回填)
# ==========================================
class QuadGenerator:
    def __init__(self):
        self.quads = []
        self.next_quad = 0
        self.temp_count = 1
        self.loops = [] # 维护多层循环的 break/continue 跳转列表

    def emit(self, op, arg1, arg2, result):
        self.quads.append([op, arg1, arg2, result])
        self.next_quad += 1
        return self.next_quad - 1

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def backpatch(self, idx_list, target_quad):
        for idx in idx_list:
            self.quads[idx][3] = target_quad

    def gen_cond(self, node):
        """专用于控制流的短路求值跳转 (If, While, For)"""
        if isinstance(node, RelOp):
            l = self.visit(node.left)
            r = self.visit(node.right)
            tj = self.emit(f"J{node.op}", l, r, "_")
            fj = self.emit("J", "_", "_", "_")
            return [tj], [fj]
        elif isinstance(node, LogicalAnd):
            t1, f1 = self.gen_cond(node.left)
            self.backpatch(t1, self.next_quad)
            t2, f2 = self.gen_cond(node.right)
            return t2, f1 + f2
        elif isinstance(node, LogicalOr):
            t1, f1 = self.gen_cond(node.left)
            self.backpatch(f1, self.next_quad)
            t2, f2 = self.gen_cond(node.right)
            return t1 + t2, f2
        elif isinstance(node, LogicalNot):
            t, f = self.gen_cond(node.expr)
            return f, t
        else:
            res = self.visit(node)
            tj = self.emit("J!=", res, "0", "_")
            fj = self.emit("J", "_", "_", "_")
            return [tj], [fj]

    def generate(self, node):
        self.visit(node)

    def visit(self, node):
        if isinstance(node, Program):
            for n in node.nodes: self.visit(n)
            
        elif isinstance(node, FuncDef):
            self.emit(node.name, "_", "_", "_")
            self.visit(node.body)
            if node.name == "main":
                self.emit("sys", "_", "_", "_")
            else:
                # 补齐无返回值函数的隐含返回
                if not self.quads or self.quads[-1][0] != "ret":
                    self.emit("ret", "_", "_", "_")
                    
        elif isinstance(node, Block):
            for stmt in node.stmts:
                if stmt: self.visit(stmt)
            
        elif isinstance(node, VarDecl):
            if node.value is not None:
                val = self.visit(node.value)
                self.emit("=", val, "_", node.name)
            
        elif isinstance(node, Assign):
            val = self.visit(node.expr)
            self.emit("=", val, "_", node.var)
            return node.var # 支持右结合连等 a = b = 0
            
        elif isinstance(node, BinOp):
            left_val = self.visit(node.left)
            right_val = self.visit(node.right)
            res = self.new_temp()
            self.emit(node.op, left_val, right_val, res)
            return res
            
        elif isinstance(node, UnaryOp):
            val = self.visit(node.expr)
            res = self.new_temp()
            self.emit(node.op, val, "_", res)
            return res
            
        # 当逻辑/关系运算符用于普通赋值时，作为常规四元式处理 (非跳转)
        elif isinstance(node, RelOp) or isinstance(node, LogicalAnd) or isinstance(node, LogicalOr):
            l = self.visit(node.left)
            r = self.visit(node.right)
            res = self.new_temp()
            op = node.op if hasattr(node, 'op') else ("&&" if isinstance(node, LogicalAnd) else "||")
            self.emit(op, l, r, res)
            return res
            
        elif isinstance(node, LogicalNot):
            val = self.visit(node.expr)
            res = self.new_temp()
            self.emit("!", val, "_", res)
            return res
            
        elif isinstance(node, Identifier):
            return node.name
            
        elif isinstance(node, Constant):
            return node.val
            
        elif isinstance(node, FuncCall):
            for arg in node.args:
                arg_val = self.visit(arg)
                self.emit("para", arg_val, "_", "_")
            res = self.new_temp()
            self.emit("call", node.name, "_", res)
            return res
            
        elif isinstance(node, Return):
            if node.expr is not None:
                val = self.visit(node.expr)
                self.emit("ret", "_", "_", val)
            else:
                self.emit("ret", "_", "_", "_")
                
        elif isinstance(node, Break):
            idx = self.emit("J", "_", "_", "_")
            if self.loops: self.loops[-1]['break'].append(idx)
            
        elif isinstance(node, Continue):
            idx = self.emit("J", "_", "_", "_")
            if self.loops: self.loops[-1]['continue'].append(idx)

        # ====== 循环与控制流 ======
        elif isinstance(node, If):
            truelist, falselist = self.gen_cond(node.cond)
            self.backpatch(truelist, self.next_quad)
            self.visit(node.true_block)
            if node.false_block:
                out_list = [self.emit("J", "_", "_", "_")]
                self.backpatch(falselist, self.next_quad)
                self.visit(node.false_block)
                self.backpatch(out_list, self.next_quad)
            else:
                self.backpatch(falselist, self.next_quad)

        elif isinstance(node, While):
            self.loops.append({'break': [], 'continue': []})
            start_idx = self.next_quad
            truelist, falselist = self.gen_cond(node.cond)
            self.backpatch(truelist, self.next_quad)
            self.visit(node.body)
            self.emit("J", "_", "_", start_idx)
            exit_idx = self.next_quad
            self.backpatch(falselist, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info['break'], exit_idx)
            self.backpatch(loop_info['continue'], start_idx)

        elif isinstance(node, DoWhile):
            self.loops.append({'break': [], 'continue': []})
            start_idx = self.next_quad
            self.visit(node.body)
            cont_idx = self.next_quad
            truelist, falselist = self.gen_cond(node.cond)
            self.backpatch(truelist, start_idx)
            exit_idx = self.next_quad
            self.backpatch(falselist, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info['break'], exit_idx)
            self.backpatch(loop_info['continue'], cont_idx)

        elif isinstance(node, For):
            self.loops.append({'break': [], 'continue': []})
            if node.init: self.visit(node.init)
            cond_idx = self.next_quad
            if node.cond:
                truelist, falselist = self.gen_cond(node.cond)
            else:
                tj = self.emit("J", "_", "_", "_")
                truelist, falselist = [tj], []
            
            step_idx = self.next_quad
            if node.step: self.visit(node.step)
            self.emit("J", "_", "_", cond_idx)
            
            body_idx = self.next_quad
            self.backpatch(truelist, body_idx)
            self.visit(node.body)
            self.emit("J", "_", "_", step_idx)
            
            exit_idx = self.next_quad
            self.backpatch(falselist, exit_idx)
            loop_info = self.loops.pop()
            self.backpatch(loop_info['break'], exit_idx)
            self.backpatch(loop_info['continue'], step_idx)

    def output(self, filename="output.txt"):
        with open(filename, 'w', encoding='utf-8') as f:
            for i, q in enumerate(self.quads):
                res = []
                for x in q:
                    # 跳转标号(int)不可加引号，字符串均加引号
                    if isinstance(x, int):
                        res.append(str(x))
                    elif x == '_':
                        res.append("'_'")
                    else:
                        res.append(f"'{str(x).strip()}'")
                f.write(f"{i}: ({res[0]}, {res[1]}, {res[2]}, {res[3]})\n")


# ==========================================
# 3. 完整特性词法与语法解析器
# ==========================================
class MiniParser:
    def __init__(self, code):
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        token_pattern = r'\b(?:const|char|void|int|float|return|if|else|while|do|for|break|continue)\b|[a-zA-Z_]\w*|\d+(?:\.\d+)?|\'[^\']+\'|==|!=|<=|>=|&&|\|\||>|<|\+|-|\*|/|=|!|;|,|\(|\)|\{|\}'
        self.tokens = re.findall(token_pattern, code)
        self.pos = 0

    def match(self, expected):
        if self.pos < len(self.tokens) and self.tokens[self.pos] == expected:
            self.pos += 1
            return True
        return False

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok
        return None

    def parse(self):
        nodes = []
        while self.peek():
            stmt = self.parse_global()
            if stmt: nodes.append(stmt)
        return Program(nodes)

    def parse_global(self):
        if self.peek() in ('int', 'float', 'void', 'const', 'char'):
            if self.peek() == 'const': self.consume()
            self.consume() # type
            name = self.consume()
            if self.match('('):
                while self.peek() and self.peek() != ')': self.consume()
                self.match(')')
                if self.match(';'): return None # 函数原型跳过
                if self.match('{'): return FuncDef(name, Block(self.parse_stmts()))
            else:
                decls = []
                if self.match('='): decls.append(VarDecl(name, self.parse_assign_expr()))
                else: decls.append(VarDecl(name, None))
                while self.match(','):
                    var = self.consume()
                    if self.match('='): decls.append(VarDecl(var, self.parse_assign_expr()))
                    else: decls.append(VarDecl(var, None))
                self.match(';')
                return Block(decls)
        else:
            self.consume()
            return None

    def parse_stmts(self):
        stmts = []
        while self.peek() and self.peek() != '}':
            stmt = self.parse_stmt()
            if stmt: stmts.append(stmt)
        return stmts

    def parse_stmt(self):
        if self.peek() == ';':
            self.consume()
            return None
            
        if self.peek() in ('int', 'float', 'void', 'const', 'char'):
            if self.peek() == 'const': self.consume()
            self.consume() # type
            decls = []
            while True:
                var = self.consume()
                if self.match('='):
                    decls.append(VarDecl(var, self.parse_assign_expr()))
                else:
                    decls.append(VarDecl(var, None))
                if self.match(','): continue
                elif self.match(';'): break
                else: break
            return Block(decls)
            
        elif self.peek() == 'if':
            self.consume()
            self.match('(')
            cond = self.parse_assign_expr()
            self.match(')')
            true_stmt = self.parse_stmt()
            false_stmt = None
            if self.peek() == 'else':
                self.consume()
                false_stmt = self.parse_stmt()
            return If(cond, true_stmt, false_stmt)
            
        elif self.peek() == 'while':
            self.consume()
            self.match('(')
            cond = self.parse_assign_expr()
            self.match(')')
            body = self.parse_stmt()
            return While(cond, body)
            
        elif self.peek() == 'do':
            self.consume()
            body = self.parse_stmt()
            self.match('while')
            self.match('(')
            cond = self.parse_assign_expr()
            self.match(')')
            self.match(';')
            return DoWhile(body, cond)
            
        elif self.peek() == 'for':
            self.consume()
            self.match('(')
            init = None
            if self.peek() != ';': init = self.parse_assign_expr()
            self.match(';')
            cond = None
            if self.peek() != ';': cond = self.parse_assign_expr()
            self.match(';')
            step = None
            if self.peek() != ')': step = self.parse_assign_expr()
            self.match(')')
            body = self.parse_stmt()
            return For(init, cond, step, body)
            
        elif self.peek() == 'return':
            self.consume()
            if self.match(';'): return Return(None)
            ret = Return(self.parse_assign_expr())
            self.match(';')
            return ret
            
        elif self.peek() == 'break':
            self.consume()
            self.match(';')
            return Break()
            
        elif self.peek() == 'continue':
            self.consume()
            self.match(';')
            return Continue()
            
        elif self.match('{'):
            stmts = self.parse_stmts()
            self.match('}')
            return Block(stmts)
            
        else:
            expr = self.parse_assign_expr()
            self.match(';')
            return expr

    # --- 严格遵循结合性与优先级的表达式解析 ---
    def parse_assign_expr(self):
        node = self.parse_logical_or()
        if self.match('='):
            right = self.parse_assign_expr() # 右结合
            return Assign(node.name, right)
        return node

    def parse_logical_or(self):
        node = self.parse_logical_and()
        while self.peek() == '||':
            self.consume() # 修复核心Bug：必须吃掉操作符
            node = LogicalOr(node, self.parse_logical_and())
        return node

    def parse_logical_and(self):
        node = self.parse_equality()
        while self.peek() == '&&':
            self.consume() # 修复核心Bug：必须吃掉操作符
            node = LogicalAnd(node, self.parse_equality())
        return node

    def parse_equality(self):
        node = self.parse_relational()
        while self.peek() in ('==', '!='):
            op = self.consume()
            node = RelOp(op, node, self.parse_relational())
        return node

    def parse_relational(self):
        node = self.parse_math_expr()
        while self.peek() in ('>', '<', '>=', '<='):
            op = self.consume()
            node = RelOp(op, node, self.parse_math_expr())
        return node

    def parse_math_expr(self):
        node = self.parse_term()
        while self.peek() in ('+', '-'):
            op = self.consume()
            node = BinOp(op, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() in ('*', '/'):
            op = self.consume()
            node = BinOp(op, node, self.parse_factor())
        return node

    def parse_factor(self):
        if self.peek() == '!':
            self.consume()
            return LogicalNot(self.parse_factor())
        elif self.peek() == '-':
            return UnaryOp(self.consume(), self.parse_factor())
        elif self.match('('):
            node = self.parse_assign_expr()
            self.match(')')
            return node
        elif self.peek() and (self.peek().isdigit() or '.' in self.peek()):
            return Constant(self.consume())
        elif self.peek() and self.peek().startswith("'"):
            val = self.consume()
            return Constant(val.strip("'")) # 处理字符常量
        else:
            name = self.consume()
            if self.match('('):
                args = []
                if self.peek() != ')':
                    args.append(self.parse_assign_expr())
                    while self.match(','):
                        args.append(self.parse_assign_expr())
                self.match(')')
                return FuncCall(name, args)
            return Identifier(name)

# ==========================================
# 4. 主程序入口 (适配 OJ 测试平台)
# ==========================================
if __name__ == "__main__":
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            code = f.read()
    except Exception:
        sys.exit(1)

    parser = MiniParser(code)
    ast_root = parser.parse()

    generator = QuadGenerator()
    generator.generate(ast_root)

    generator.output("output.txt")