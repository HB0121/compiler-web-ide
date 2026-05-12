package com.huangbin.compiler.controller;

import com.huangbin.compiler.lexer.Lexer;
import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.CompileRequest;
import com.huangbin.compiler.model.CompileResult;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.parser.Parser;
import com.huangbin.compiler.ir.IRGenerator;
import com.huangbin.compiler.interpreter.Interpreter;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // 允许跨域请求，方便前端 Vue 调试调用
public class CompileController {

    @PostMapping("/compile")
    public CompileResult compile(@RequestBody CompileRequest request) {
        CompileResult finalResult = new CompileResult();
        String source = request.getSourceCode();

        // 1. 基础校验
        if (source == null || source.trim().isEmpty()) {
            finalResult.setSuccess(false);
            return finalResult;
        }

        List<Diagnostic> allDiagnostics = new ArrayList<>();

        // 2. 第一阶段：词法分析 (Lexical Analysis)
        Lexer lexer = new Lexer();
        Lexer.LexerResult lexResult = lexer.tokenize(source);
        finalResult.setTokens(lexResult.tokens);
        allDiagnostics.addAll(lexResult.diagnostics);

        // 3. 第二阶段：语法分析 (Syntax Analysis / Parsing)
        // 只要词法分析没有致命错误（有 Token 产出），就尝试解析
        if (!lexResult.tokens.isEmpty()) {
            Parser parser = new Parser(lexResult.tokens);
            ASTNode astRoot = parser.parseProgram();
            finalResult.setAst(astRoot);
            allDiagnostics.addAll(parser.getDiagnostics());

            // 4. 后续阶段：中间代码生成与解释执行
            // 只有当词法和语法分析都没有任何错误时，才继续运行
            if (allDiagnostics.isEmpty() && astRoot != null) {

                // 4.1 生成四元式 (IR Generation)
                IRGenerator irGen = new IRGenerator();
                List<IRGenerator.Quad> quadList = irGen.generate(astRoot);

                // 将四元式对象转换为易于前端展示的字符串列表
                List<String> quadStrings = new ArrayList<>();
                for (int i = 0; i < quadList.size(); i++) {
                    quadStrings.add(i + ": " + quadList.get(i).toString());
                }
                finalResult.setQuads(quadStrings);

                // 4.2 解释执行 (Interpretation)
                Interpreter interpreter = new Interpreter(quadList);
                List<String> runLogs = interpreter.run();
                finalResult.setInterpreterOutput(runLogs);
            }
        }

        // 5. 汇总结果
        finalResult.setDiagnostics(allDiagnostics);
        // 如果 diagnostics 列表为空，则 success 标记为 true
        finalResult.setSuccess(allDiagnostics.isEmpty());

        return finalResult;
    }
}