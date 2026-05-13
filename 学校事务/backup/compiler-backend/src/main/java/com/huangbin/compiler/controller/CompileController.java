package com.huangbin.compiler.controller;

/** @author 黄彬 (12303070250) */

import com.huangbin.compiler.codegen.CodeGenerator;
import com.huangbin.compiler.interpreter.Interpreter;
import com.huangbin.compiler.ir.DAGOptimizer;
import com.huangbin.compiler.ir.IRGenerator;
import com.huangbin.compiler.ir.LLVMGenerator;
import com.huangbin.compiler.lexer.Lexer;
import com.huangbin.compiler.log.LogScanner;
import com.huangbin.compiler.log.PipelineLogger;
import com.huangbin.compiler.model.ASTNode;
import com.huangbin.compiler.model.Diagnostic;
import com.huangbin.compiler.model.Token;
import com.huangbin.compiler.parser.Parser;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
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
        LogScanner logScanner = new LogScanner();

        try {
            // ================= 1. 词法分析 (Lexer) =================
            long t1 = System.currentTimeMillis();
            Lexer lexer = new Lexer(sourceCode);
            lexer.tokenize();
            List<Token> tokens = lexer.getTokens();
            allDiagnostics.addAll(lexer.getDiagnostics());
            logScanner.record("1.词法分析", sourceCode.length() + " 字符",
                tokens.size() + " Token, " + lexer.getDiagnostics().size() + " 错误",
                System.currentTimeMillis() - t1);

            // ================= 2. 语法分析 (Parser) =================
            long t2 = System.currentTimeMillis();
            Parser parser = new Parser(tokens);
            ASTNode ast = parser.parseProgram();
            allDiagnostics.addAll(parser.getDiagnostics());
            logScanner.record("2.语法分析", tokens.size() + " Token",
                "AST 根节点: " + (ast != null ? ast.getName() : "null") + ", " + parser.getDiagnostics().size() + " 错误",
                System.currentTimeMillis() - t2);

            // ================= 3. 中间代码生成 (IR Generator) =================
            long t3 = System.currentTimeMillis();
            IRGenerator irGenerator = new IRGenerator();
            List<IRGenerator.Quad> quads = new ArrayList<>();
            if (allDiagnostics.isEmpty()) {
                quads = irGenerator.generate(ast);
            }
            logScanner.record("3.IR生成", ast != null ? ast.getName() : "null",
                quads.size() + " 四元式",
                System.currentTimeMillis() - t3);

            // ================= 3.1 汇编代码生成 (Code Generator) =================
            String assemblyCode = "";
            if (allDiagnostics.isEmpty() && !quads.isEmpty()) {
                long t31 = System.currentTimeMillis();
                CodeGenerator codeGen = new CodeGenerator(quads);
                assemblyCode = codeGen.generate();
                logScanner.record("3.1 MASM汇编生成", quads.size() + " 四元式",
                    assemblyCode.split("\n").length + " 行汇编",
                    System.currentTimeMillis() - t31);
            }

            // ================= 3.2 LLVM IR 生成 (选做 4.2) =================
            String llvmIR = "";
            if (allDiagnostics.isEmpty() && !quads.isEmpty()) {
                long t32 = System.currentTimeMillis();
                LLVMGenerator llvmGen = new LLVMGenerator(quads);
                llvmIR = llvmGen.generate();
                logScanner.record("3.2 LLVM IR 生成", quads.size() + " 四元式",
                    llvmIR.split("\n").length + " 行 IR",
                    System.currentTimeMillis() - t32);
            }

            // ================= 3.3 DAG 优化 + 流图分析 (选做 4.4) =================
            Map<String, Object> cfgAnalysis = null;
            if (allDiagnostics.isEmpty() && !quads.isEmpty()) {
                long t33 = System.currentTimeMillis();
                DAGOptimizer dagOpt = new DAGOptimizer(quads);
                DAGOptimizer.OptimizationResult optResult = dagOpt.optimize();
                cfgAnalysis = new LinkedHashMap<>();
                cfgAnalysis.put("flowGraph", optResult.flowGraph);
                cfgAnalysis.put("dagSummary", optResult.dagSummary);
                cfgAnalysis.put("blockCount", optResult.blocks.size());
                cfgAnalysis.put("eliminatedCount", optResult.eliminatedCount);
                logScanner.record("3.3 DAG优化+流图", quads.size() + " 四元式",
                    optResult.blocks.size() + " 基本块, 消除 " + optResult.eliminatedCount + " 公共子表达式",
                    System.currentTimeMillis() - t33);
            }

            // ================= 4. 解释执行 (Interpreter) =================
            List<String> interpreterOutput = new ArrayList<>();
            if (allDiagnostics.isEmpty() && !quads.isEmpty()) {
                long t4 = System.currentTimeMillis();
                Interpreter interpreter = new Interpreter(quads);
                interpreterOutput = interpreter.run();
                logScanner.record("4.解释执行", quads.size() + " 四元式",
                    interpreterOutput.size() + " 行输出",
                    System.currentTimeMillis() - t4);
            }

            // ================= 5. 组装发给前端的数据 =================
            response.put("tokens", tokens);
            response.put("ast", ast);
            response.put("quads", quads);
            response.put("assemblyCode", assemblyCode);
            response.put("llvmIR", llvmIR);
            response.put("compileLog", logScanner.toMap());
            response.put("cfgAnalysis", cfgAnalysis);
            response.put("interpreterOutput", interpreterOutput);
            response.put("diagnostics", allDiagnostics);

            response.put("success", allDiagnostics.isEmpty());

        } catch (Exception e) {
            e.printStackTrace();
            response.put("success", false);
            allDiagnostics.add(new Diagnostic("system", 0, "SYS500", "系统内部异常: " + e.getMessage()));
            response.put("diagnostics", allDiagnostics);
        }

        return response;
    }
}