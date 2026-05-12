package com.huangbin.compiler.controller;

import com.huangbin.compiler.lexer.Lexer;
import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.CompileRequest;
import com.huangbin.compiler.model.CompileResult;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.parser.Parser;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // 允许跨域请求，方便前端 Vue 本地调试调用
public class CompileController {

    @PostMapping("/compile")
    public CompileResult compile(@RequestBody CompileRequest request) {
        CompileResult finalResult = new CompileResult();
        String source = request.getSourceCode();

        if (source == null || source.trim().isEmpty()) {
            finalResult.setSuccess(false);
            return finalResult;
        }

        List<Diagnostic> allDiagnostics = new ArrayList<>();

        // 1. 词法分析
        Lexer lexer = new Lexer();
        Lexer.LexerResult lexResult = lexer.tokenize(source);
        finalResult.setTokens(lexResult.tokens);
        allDiagnostics.addAll(lexResult.diagnostics);

        // 2. 语法分析 (只要有 Token 就尝试解析)
        if (!lexResult.tokens.isEmpty()) {
            Parser parser = new Parser(lexResult.tokens);
            ASTNode astRoot = parser.parseProgram();
            finalResult.setAst(astRoot);
            allDiagnostics.addAll(parser.getDiagnostics());
        }

        // 3. 汇总错误信息并返回
        finalResult.setDiagnostics(allDiagnostics);
        finalResult.setSuccess(allDiagnostics.isEmpty()); // 如果没有任何报错，则判定为成功

        return finalResult;
    }
}