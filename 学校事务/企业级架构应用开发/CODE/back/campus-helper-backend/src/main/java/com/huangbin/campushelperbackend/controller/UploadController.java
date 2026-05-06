package com.huangbin.campushelperbackend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class UploadController {

    @PostMapping("/upload")
    public ResponseEntity<?> uploadImage(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "文件不能为空"));
        }

        try {
            // 1. 获取原文件名和后缀 (如 .jpg, .png)
            String originalFilename = file.getOriginalFilename();
            String extension = originalFilename.substring(originalFilename.lastIndexOf("."));

            // 2. 为了防止重名覆盖，用 UUID 生成新文件名
            String newFileName = UUID.randomUUID().toString() + extension;

            // 3. 确定保存目录（项目根目录下的 uploads 文件夹）
            File dir = new File("uploads/");
            if (!dir.exists()) {
                dir.mkdirs(); // 如果文件夹不存在就自动创建
            }

            // 4. 保存文件到本地硬盘
            File dest = new File(dir, newFileName);
            file.transferTo(dest);

            // 5. 拼装可以直接在浏览器访问的图片 URL (假设你的后端跑在 8080 端口)
            String imageUrl = "http://localhost:8080/uploads/" + newFileName;

            // 6. 返回给前端
            return ResponseEntity.ok(Map.of("code", 200, "data", Map.of("url", imageUrl)));

        } catch (IOException e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "图片上传失败"));
        }
    }
}