from typing import List, Optional, Union

from .models import ASTNode, Diagnostic, Token


TYPE_NAMES = {"int", "float", "char", "void"}
IDENTIFIER_CODE = 700


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.diagnostics: List[Diagnostic] = []

    def current_token(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def previous_token(self) -> Optional[Token]:
        if self.pos > 0:
            return self.tokens[self.pos - 1]
        return None

    def peek(self, offset: int = 1) -> Optional[Token]:
        index = self.pos + offset
        if index < len(self.tokens):
            return self.tokens[index]
        return None

    def match_text(self, text: str) -> Optional[Token]:
        token = self.current_token()
        if token and token.text == text:
            self.pos += 1
            return token
        return None

    def expect_text(self, text: str) -> Optional[Token]:
        token = self.match_text(text)
        if token:
            return token

        current = self.current_token()
        previous = self.previous_token()
        line = current.line if current else (previous.line if previous else 0)
        self.diagnostics.append(Diagnostic("parser", line, "P001", f"expected {text!r}"))
        return None

    def parse(self) -> tuple[ASTNode, List[Diagnostic]]:
        return self.parse_program(), self.diagnostics

    def parse_program(self) -> ASTNode:
        node = ASTNode("Program")
        while self.current_token():
            token = self.current_token()
            if token.text == "const":
                for decl in self.parse_const_decl():
                    node.add_child(decl)
            elif token.text in TYPE_NAMES:
                next_token = self.peek(1)
                if next_token and next_token.text == "main":
                    node.add_child(self.parse_function())
                elif next_token and next_token.code == IDENTIFIER_CODE:
                    token_after_id = self.peek(2)
                    if token_after_id and token_after_id.text == "(":
                        node.add_child(self.parse_function())
                    else:
                        for decl in self.parse_var_decl():
                            node.add_child(decl)
                else:
                    self.pos += 1
            else:
                self.pos += 1
        return node

    def parse_const_decl(self) -> List[ASTNode]:
        self.match_text("const")
        type_token = self.current_token()
        if not type_token:
            return []
        self.pos += 1

        decls: List[ASTNode] = []
        while True:
            id_token = self.current_token()
            if not id_token:
                break
            self.pos += 1

            node = ASTNode("ConstDecl", line=id_token.line, value=f"{type_token.text} {id_token.text}")
            self.match_text("=")
            node.add_child(self.parse_expr_stmt())
            decls.append(node)

            if self.current_token() and self.current_token().text == ",":
                self.pos += 1
            else:
                break

        self.expect_text(";")
        return decls

    def parse_var_decl(self) -> List[ASTNode]:
        type_token = self.current_token()
        if not type_token:
            return []
        self.pos += 1

        decls: List[ASTNode] = []
        while True:
            id_token = self.current_token()
            if not id_token:
                break
            self.pos += 1

            node = ASTNode("VarDecl", line=id_token.line, value=f"{type_token.text} {id_token.text}")
            if self.current_token() and self.current_token().text == "=":
                self.pos += 1
                node.add_child(self.parse_expr_stmt())
            decls.append(node)

            if self.current_token() and self.current_token().text == ",":
                self.pos += 1
            else:
                break

        self.expect_text(";")
        return decls

    def parse_function(self) -> Optional[ASTNode]:
        type_token = self.current_token()
        if not type_token:
            return None
        self.pos += 1

        id_token = self.current_token()
        if not id_token:
            return None
        self.pos += 1

        self.match_text("(")
        params: List[ASTNode] = []
        if self.current_token() and self.current_token().text != ")":
            if self.current_token().text == "void" and self.peek(1) and self.peek(1).text == ")":
                self.pos += 1
            else:
                while True:
                    p_type = self.current_token()
                    if not p_type:
                        break
                    self.pos += 1

                    p_id = self.current_token()
                    if not p_id:
                        break
                    self.pos += 1
                    params.append(ASTNode("Param", line=p_id.line, value=f"{p_type.text} {p_id.text}"))

                    if self.current_token() and self.current_token().text == ",":
                        self.pos += 1
                    else:
                        break
        self.expect_text(")")

        if self.current_token() and self.current_token().text == ";":
            self.expect_text(";")
            node = ASTNode("FunctionDecl", line=id_token.line, value=f"{type_token.text} {id_token.text}")
            for param in params:
                node.add_child(param)
            return node

        if self.current_token() and self.current_token().text == "{":
            node = ASTNode("FunctionDef", line=id_token.line, value=f"{type_token.text} {id_token.text}")
            for param in params:
                node.add_child(param)
            node.add_child(self.parse_compound())
            return node

        return None

    def parse_compound(self) -> ASTNode:
        self.match_text("{")
        node = ASTNode("Compound")
        while self.current_token() and self.current_token().text != "}":
            stmt = self.parse_statement()
            self.add_statement(node, stmt)
        self.expect_text("}")
        return node

    def parse_statement(self) -> Optional[Union[ASTNode, List[ASTNode]]]:
        token = self.current_token()
        if not token:
            return None

        if token.text == "for":
            return self.parse_for_stmt()
        if token.text == "do":
            return self.parse_do_while_stmt()
        if token.text == "continue":
            return self.parse_continue_stmt()
        if token.text == "break":
            return self.parse_break_stmt()
        if token.text == "if":
            return self.parse_if_stmt()
        if token.text == "while":
            return self.parse_while_stmt()
        if token.text == "return":
            return self.parse_return_stmt()
        if token.text == "{":
            return self.parse_compound()
        if token.text in TYPE_NAMES:
            return self.parse_var_decl()
        if token.text == "const":
            return self.parse_const_decl()

        if token.text == ";":
            self.expect_text(";")
            return ASTNode("ExprStmt")

        expr_node = self.parse_expr_stmt()
        has_semi = self.expect_text(";") is not None

        if expr_node:
            stmt_node = ASTNode("ExprStmt")
            stmt_node.add_child(expr_node)
            return stmt_node

        if has_semi:
            return ASTNode("ExprStmt")

        if self.current_token():
            self.pos += 1
            if self.current_token() and self.current_token().text == ";":
                self.expect_text(";")
            return ASTNode("ExprStmt")

        return None

    def parse_if_stmt(self) -> ASTNode:
        self.match_text("if")
        self.match_text("(")
        node = ASTNode("IfStmt")
        node.add_child(self.parse_logical_expression())
        self.expect_text(")")

        stmt = self.parse_statement()
        self.add_statement(node, stmt)

        token = self.current_token()
        if token and token.text == "else":
            self.pos += 1
            self.add_statement(node, self.parse_statement())
        return node

    def parse_while_stmt(self) -> ASTNode:
        self.match_text("while")
        self.match_text("(")
        node = ASTNode("WhileStmt")
        node.add_child(self.parse_logical_expression())
        self.expect_text(")")

        stmt = self.parse_statement()
        self.add_statement(node, stmt)
        return node

    def parse_for_stmt(self) -> Union[ASTNode, List[ASTNode]]:
        self.match_text("for")
        self.match_text("(")

        if self.current_token() and self.current_token().text in TYPE_NAMES:
            node_list = [ASTNode("ExprStmt")]

            self.pos += 3
            expr1 = self.parse_expr_stmt()
            stmt1 = ASTNode("ExprStmt")
            if expr1:
                stmt1.add_child(expr1)
            node_list.append(stmt1)
            self.expect_text(";")

            expr2 = self.parse_logical_expression()
            stmt2 = ASTNode("ExprStmt")
            if expr2:
                stmt2.add_child(expr2)
            node_list.append(stmt2)
            self.expect_text(";")

            expr3 = self.parse_assignment_or_expr()
            stmt3 = ASTNode("ExprStmt")
            if expr3:
                stmt3.add_child(expr3)
            node_list.append(stmt3)
            self.expect_text(")")

            node_list.append(ASTNode("ExprStmt"))
            compound = self.parse_statement()
            if isinstance(compound, list):
                node_list.extend(compound)
            elif compound:
                node_list.append(compound)
            return node_list

        node = ASTNode("ForStmt")
        init_node = self.parse_assignment_or_expr()
        node.add_child(init_node)
        self.expect_text(";")

        cond_node = self.parse_logical_expression()
        node.add_child(cond_node)
        self.expect_text(";")

        step_node = self.parse_assignment_or_expr()
        node.add_child(step_node)
        self.expect_text(")")

        stmt = self.parse_statement()
        self.add_statement(node, stmt)
        return node

    def parse_do_while_stmt(self) -> ASTNode:
        self.match_text("do")
        node = ASTNode("DoWhileStmt")

        stmt = self.parse_statement()
        self.add_statement(node, stmt)

        self.match_text("while")
        self.match_text("(")
        node.add_child(self.parse_logical_expression())
        self.expect_text(")")
        self.expect_text(";")
        return node

    def parse_continue_stmt(self) -> ASTNode:
        token = self.match_text("continue")
        self.expect_text(";")
        return ASTNode("ContinueStmt", line=token.line if token else None)

    def parse_break_stmt(self) -> ASTNode:
        token = self.match_text("break")
        self.expect_text(";")
        return ASTNode("BreakStmt", line=token.line if token else None)

    def parse_return_stmt(self) -> ASTNode:
        token = self.match_text("return")
        node = ASTNode("ReturnStmt", line=token.line if token else None)
        if self.current_token() and self.current_token().text != ";":
            node.add_child(self.parse_expr_stmt())
        self.expect_text(";")
        return node

    def parse_expr_stmt(self) -> Optional[ASTNode]:
        return self.parse_assignment_or_expr()

    def parse_assignment_or_expr(self) -> Optional[ASTNode]:
        token = self.current_token()
        if token and token.code == IDENTIFIER_CODE and self.peek(1) and self.peek(1).text == "=":
            id_token = token
            self.pos += 1
            eq_token = self.current_token()
            self.pos += 1

            expr_node = self.parse_assignment_or_expr()
            assign_node = ASTNode("=", line=eq_token.line)
            assign_node.add_child(ASTNode(id_token.text, line=id_token.line))
            assign_node.add_child(expr_node)
            return assign_node
        return self.parse_logical_expression()

    def parse_assignment_expr(self) -> Optional[ASTNode]:
        return self.parse_assignment_or_expr()

    def parse_logical_expression(self) -> Optional[ASTNode]:
        node = self.parse_logical_term()
        token = self.current_token()
        while token and token.text == "||":
            op_token = token
            self.pos += 1
            right_node = self.parse_logical_term()
            parent_node = ASTNode("||", line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_logical_term(self) -> Optional[ASTNode]:
        node = self.parse_logical_factor()
        token = self.current_token()
        while token and token.text == "&&":
            op_token = token
            self.pos += 1
            right_node = self.parse_logical_factor()
            parent_node = ASTNode("&&", line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_logical_factor(self) -> Optional[ASTNode]:
        return self.parse_equality_expression()

    def parse_equality_expression(self) -> Optional[ASTNode]:
        node = self.parse_relational_expression()
        token = self.current_token()
        while token and token.text in {"==", "!="}:
            op_token = token
            self.pos += 1
            right_node = self.parse_relational_expression()
            parent_node = ASTNode(op_token.text, line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_relational_expression(self) -> Optional[ASTNode]:
        node = self.parse_arithmetic_expression()
        token = self.current_token()
        while token and token.text in {">", "<", ">=", "<="}:
            op_token = token
            self.pos += 1
            right_node = self.parse_arithmetic_expression()
            parent_node = ASTNode(op_token.text, line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_arithmetic_expression(self) -> Optional[ASTNode]:
        node = self.parse_term()
        token = self.current_token()
        while token and token.text in {"+", "-"}:
            op_token = token
            self.pos += 1
            right_node = self.parse_term()
            parent_node = ASTNode(op_token.text, line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_term(self) -> Optional[ASTNode]:
        node = self.parse_factor()
        token = self.current_token()
        while token and token.text in {"*", "/"}:
            op_token = token
            self.pos += 1
            right_node = self.parse_factor()
            parent_node = ASTNode(op_token.text, line=op_token.line)
            parent_node.add_child(node)
            parent_node.add_child(right_node)
            node = parent_node
            token = self.current_token()
        return node

    def parse_factor(self) -> Optional[ASTNode]:
        token = self.current_token()
        if not token:
            return None

        if token.text in {"-", "!"}:
            self.pos += 1
            node = ASTNode(token.text, line=token.line)
            node.add_child(self.parse_factor())
            return node

        if token.code == IDENTIFIER_CODE:
            next_token = self.peek(1)
            if next_token and next_token.text == "(":
                func_name_token = token
                self.pos += 1
                self.match_text("(")

                call_node = ASTNode("Call", line=func_name_token.line, value=func_name_token.text)
                if self.current_token() and self.current_token().text != ")":
                    arg_node = self.parse_expr_stmt()
                    call_node.add_child(arg_node)
                    while self.current_token() and self.current_token().text == ",":
                        self.pos += 1
                        arg_node = self.parse_expr_stmt()
                        call_node.add_child(arg_node)
                self.expect_text(")")
                return call_node

            self.pos += 1
            return ASTNode(token.text, line=token.line)

        if token.code >= 400 and token.code != IDENTIFIER_CODE:
            self.pos += 1
            return ASTNode(token.text, line=token.line)

        if token.text == "(":
            self.pos += 1
            node = self.parse_logical_expression()
            if self.current_token() and self.current_token().text == ")":
                self.expect_text(")")
            elif not node:
                while self.current_token() and self.current_token().text != ")":
                    self.pos += 1
                if self.current_token() and self.current_token().text == ")":
                    self.expect_text(")")
            else:
                self.expect_text(")")
            return node

        return None

    @staticmethod
    def add_statement(parent: ASTNode, stmt: Optional[Union[ASTNode, List[ASTNode]]]) -> None:
        if isinstance(stmt, list):
            for child in stmt:
                parent.add_child(child)
        else:
            parent.add_child(stmt)
