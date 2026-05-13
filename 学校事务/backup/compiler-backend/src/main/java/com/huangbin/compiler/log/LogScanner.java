package com.huangbin.compiler.log;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 编译日志扫描器 - 记录编译流水线各阶段的输入/输出和时间信息
 *
 * @author 黄彬 (12303070250)
 */
public class LogScanner {

    private final List<StageLog> stages = new ArrayList<>();
    private final DateTimeFormatter fmt = DateTimeFormatter.ofPattern("HH:mm:ss.SSS");

    public void record(String stage, String input, String output, long durationMs) {
        stages.add(new StageLog(stage, input, output, durationMs, LocalDateTime.now().format(fmt)));
    }

    public List<StageLog> getStages() { return stages; }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new LinkedHashMap<>();
        List<Map<String, Object>> list = new ArrayList<>();
        int totalTokens = 0, totalQuads = 0, totalAsmLines = 0;
        long totalDuration = 0;
        for (StageLog s : stages) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("stage", s.stage);
            entry.put("time", s.timestamp);
            entry.put("input", s.input);
            entry.put("output", s.output);
            entry.put("durationMs", s.durationMs);
            list.add(entry);
            totalDuration += s.durationMs;
        }
        map.put("stages", list);
        map.put("totalStages", stages.size());
        map.put("totalDurationMs", totalDuration);
        return map;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("========== 编译流水线日志 ==========\n");
        sb.append(String.format("%-18s %-14s %-7s %s\n", "阶段", "时间", "耗时", "详情"));
        sb.append("--------------------------------------------------------------\n");
        for (StageLog s : stages) {
            sb.append(String.format("%-18s %-14s %4dms  %s -> %s\n",
                s.stage, s.timestamp, s.durationMs, s.input, s.output));
        }
        long total = stages.stream().mapToLong(s -> s.durationMs).sum();
        sb.append("--------------------------------------------------------------\n");
        sb.append("总耗时: ").append(total).append("ms, 阶段数: ").append(stages.size()).append("\n");
        return sb.toString();
    }

    public static class StageLog {
        public final String stage, input, output, timestamp;
        public final long durationMs;

        StageLog(String stage, String input, String output, long durationMs, String timestamp) {
            this.stage = stage;
            this.input = input;
            this.output = output;
            this.durationMs = durationMs;
            this.timestamp = timestamp;
        }
    }
}
