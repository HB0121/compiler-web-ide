package com.huangbin.campushelperbackend.service;

import com.huangbin.campushelperbackend.dto.AiParsedTaskDTO;
import com.fasterxml.jackson.databind.ObjectMapper; // 注意：必须使用正确的 Jackson 包名
import org.springframework.ai.chat.ChatClient;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TaskAiService {

    private final ChatClient chatClient;
    private final ObjectMapper objectMapper;

    // 在 0.8.1 版本中，直接注入 ChatClient 即可，不需要 Builder
    public TaskAiService(ChatClient chatClient, ObjectMapper objectMapper) {
        this.chatClient = chatClient;
        this.objectMapper = objectMapper;
    }

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
            // 0.8.x 版本构建 Prompt 的方式
            SystemMessage systemMessage = new SystemMessage(SYSTEM_PROMPT);
            UserMessage userMessage = new UserMessage(userText);

            Prompt prompt = new Prompt(List.of(systemMessage, userMessage));

            // 调用大模型
            String aiResponse = chatClient.call(prompt).getResult().getOutput().getContent();

            // 清洗结果并转为对象
            String cleanJson = cleanMarkdown(aiResponse);
            return objectMapper.readValue(cleanJson, AiParsedTaskDTO.class);

        } catch (Exception e) {
            throw new RuntimeException("AI 解析任务需求失败", e);
        }
    }

    private String cleanMarkdown(String text) {
        if (text == null) return "";
        return text.replaceAll("```json", "")
                .replaceAll("
                        ```", "")
                                .trim();
    }
}