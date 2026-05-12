<template>
  <div class="ide-container">
    <header class="header">
      <h1>Compiler Web IDE</h1>
      <button class="run-btn" @click="runCompile" :disabled="loading">
        {{ loading ? '编译中...' : '▶ 运行 (Run)' }}
      </button>
    </header>

    <main class="main-content">
      <div class="editor-pane">
        <vue-monaco-editor
          v-model:value="sourceCode"
          theme="vs-dark"
          language="c"
          :options="editorOptions"
          @mount="handleEditorMount"
        />
      </div>

      <div class="result-pane">
        <div class="result-header">编译结果 (JSON)</div>
        <pre class="result-content">{{ compileResult }}</pre>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

// 1. 定义响应式状态
const sourceCode = ref('int a = 10;\nb = a;\n') // 默认代码
const compileResult = ref('点击上方 "运行" 按钮查看结果...')
const loading = ref(false)

// 2. 编辑器配置
const editorOptions = {
  automaticLayout: true,
  fontSize: 16,
  minimap: { enabled: false },
  wordWrap: 'on'
}

// 3. 编辑器加载完成的回调
const handleEditorMount = (editor) => {
  console.log('Monaco Editor 已挂载!')
}

// 4. 调用 Spring Boot 后端 API
const runCompile = async () => {
  if (!sourceCode.value.trim()) return
  
  loading.value = true
  compileResult.value = '正在请求后端...'
  
  try {
    // 这里的端口 8080 要和你 Spring Boot 启动的端口一致
    const response = await axios.post('http://localhost:8080/api/compile', {
      sourceCode: sourceCode.value
    })
    
    // 把后端返回的 JSON 格式化展示出来 (缩进为 2 个空格)
    compileResult.value = JSON.stringify(response.data, null, 2)
  } catch (error) {
    console.error(error)
    compileResult.value = '请求失败，请检查 Spring Boot 后端是否启动，以及跨域配置。\n' + error.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 极简 IDE 样式 */
.ide-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: system-ui, -apple-system, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #2d2d2d;
  color: white;
  height: 60px;
}

.run-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
}

.run-btn:hover { background-color: #45a049; }
.run-btn:disabled { background-color: #777; cursor: not-allowed; }

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-pane {
  flex: 1;
  border-right: 2px solid #ddd;
}

.result-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.result-header {
  padding: 10px;
  background-color: #e0e0e0;
  font-weight: bold;
  border-bottom: 1px solid #ccc;
}

.result-content {
  flex: 1;
  padding: 15px;
  margin: 0;
  overflow: auto;
  font-family: 'Consolas', monospace;
  font-size: 14px;
}
</style>