package com.huangbin.compiler.controller;

import com.huangbin.compiler.interpreter.Interpreter;
import com.huangbin.compiler.ir.IRGenerator;
import com.huangbin.compiler.lexer.Lexer;
import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;
import com.huangbin.compiler.parser.Parser;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin // 允许跨域请求
public class CompileController {

    @PostMapping("/compile")
    public Map<String, Object> compile(@RequestBody Map<String, String> request) {
        String sourceCode = request.getOrDefault("sourceCode", "");
        Map<String, Object> response = new HashMap<>();
        List<Diagnostic> allDiagnostics = new ArrayList<>();

        try {
            // ================= 1. 词法分析 (Lexer) =================
            Lexer lexer = new Lexer(sourceCode);
            lexer.tokenize(); // 执行词法扫描
            List<Token> tokens = lexer.getTokens();
            allDiagnostics.addAll(lexer.getDiagnostics());

            // ================= 2. 语法分析 (Parser) =================
            Parser parser = new Parser(tokens);
            ASTNode ast = parser.parseProgram(); // 生成抽象语法树
            allDiagnostics.addAll(parser.getDiagnostics());

            // ================= 3. 中间代码生成 (IR Generator) =================
            IRGenerator irGenerator = new IRGenerator();
            List<IRGenerator.Quad> quads = new ArrayList<>();
            // 只有当没有严重的词法和语法错误时，才生成中间代码
            if (allDiagnostics.isEmpty()) {
                quads = irGenerator.generate(ast);
            }

            // ================= 4. 解释执行 (Interpreter) =================
            List<String> interpreterOutput = new ArrayList<>();
            if (allDiagnostics.isEmpty() && !quads.isEmpty()) {
                Interpreter interpreter = new Interpreter(quads);
                interpreterOutput = interpreter.run();
            }

            // ================= 5. 组装发给前端的数据 =================
            response.put("tokens", tokens);
            response.put("ast", ast);
            response.put("quads", quads);
            response.put("interpreterOutput", interpreterOutput);
            response.put("diagnostics", allDiagnostics);

            // 如果所有的 diagnostics 报错列表为空，说明编译完美成功！
            response.put("success", allDiagnostics.isEmpty());

        } catch (Exception e) {
            // 兜底容错，防止后端崩溃死机
            e.printStackTrace();
            response.put("success", false);
            allDiagnostics.add(new Diagnostic("system", 0, "SYS500", "系统内部异常: " + e.getMessage()));
            response.put("diagnostics", allDiagnostics);
        }

        return response;
    }
}