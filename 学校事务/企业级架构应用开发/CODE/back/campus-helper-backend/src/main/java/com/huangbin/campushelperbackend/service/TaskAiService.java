package com.huangbin.campushelperbackend.service;

import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO;
import tools.jackson.databind.ObjectMapper;

public class TaskAiService {

    private final ChatClient chatClient;
    private final ObjectMapper objectMapper;

    // 注入 Spring AI 的 ChatClient 和 Jackson 的 ObjectMapper
    public TaskAiService(ChatClient.Builder chatClientBuilder, ObjectMapper objectMapper) {
        this.chatClient = chatClientBuilder.build();
        this.objectMapper = objectMapper;
    }

    // 将我们之前设计的 Few-Shot Prompt 定义为常量
    private static final String SYSTEM_PROMPT = """
        你是一个校园帮办平台的智能意图识别引擎。你的任务是从用户的自然语言输入中，精准提取关键任务实体，并严格输出为 JSON 格式。
        
        # Constraints
        1. 必须且只能输出合法的 JSON 字符串，绝对不要包含任何前缀、后缀、解释性文本，也不要使用 Markdown 的 ```json 代码块包裹。
        2. 如果用户没有提供某个字段的信息，请将该字段的值设为 null。
        3. "reward" 字段只能提取纯数字。
        
        # Output Schema
        {
          "time": "...",
          "location": "...",
          "action": "...",
          "reward": 数字,
          "tags": ["..."]
        }
        """;

    public AiParsedTaskDTO parseUserIntent(String userText) {
        try {
            // 1. 调用大模型进行意图识别
            String aiResponse = chatClient.prompt()
                    .system(SYSTEM_PROMPT)
                    .user(userText)
                    .call()
                    .content();

            // 2. 工程化鲁棒性处理：清理模型可能返回的 Markdown 标记
            String cleanJson = cleanMarkdown(aiResponse);

            // 3. 将 JSON 字符串反序列化为 Java 对象
            return objectMapper.readValue(cleanJson, AiParsedTaskDTO.class);

        } catch (Exception e) {
            // 记录日志，抛出自定义异常交由全局异常处理器处理
            throw new RuntimeException("AI 解析任务需求失败", e);
        }
    }

    // 辅助方法：去除 ```json 等无用字符
    private String cleanMarkdown(String text) {
        if (text == null) return "";
        return text.replaceAll("```json", "")
                .replaceAll("```", "")
                .trim();
    }
}
