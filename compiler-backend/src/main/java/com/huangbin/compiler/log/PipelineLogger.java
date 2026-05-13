package com.huangbin.compiler.log;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 编译流水线日志 — 记录各阶段的输入/输出和耗时
 *
 * @author 黄彬 (12303070250)
 */
public class PipelineLogger {
    private final List<StageLog> stages = new ArrayList<>();

    public void record(String stage, String input, String output, long durationMs) {
        stages.add(new StageLog(stage, input, output, durationMs,
            LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"))));
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new LinkedHashMap<>();
        List<Map<String, Object>> list = new ArrayList<>();
        long total = 0;
        for (StageLog s : stages) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("stage", s.stage);
            entry.put("time", s.timestamp);
            entry.put("input", s.input);
            entry.put("output", s.output);
            entry.put("durationMs", s.durationMs);
            list.add(entry);
            total += s.durationMs;
        }
        map.put("stages", list);
        map.put("totalStages", stages.size());
        map.put("totalDurationMs", total);
        return map;
    }

    public static class StageLog {
        public final String stage, input, output, timestamp;
        public final long durationMs;
        StageLog(String stage, String input, String output, long durationMs, String timestamp) {
            this.stage = stage; this.input = input; this.output = output;
            this.durationMs = durationMs; this.timestamp = timestamp;
        }
    }
}
