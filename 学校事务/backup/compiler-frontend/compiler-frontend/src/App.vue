<template>
  <div class="ide-container">
    <header class="header">
      <div class="logo">
        <span class="icon">💻</span> Compiler Web IDE
      </div>
      <div class="actions">
        <span v-if="compileStatus !== null" :class="['status-badge', compileStatus ? 'success' : 'error']">
          {{ compileStatus ? '✅ 编译成功' : '❌ 编译失败' }}
        </span>
        <button class="run-btn" @click="runCompile" :disabled="loading">
          {{ loading ? '编译中...' : '▶ 运行 (Run)' }}
        </button>
      </div>
    </header>

    <main class="main-content">
      <div class="editor-pane">
        <vue-monaco-editor
          v-model:value="sourceCode"
          theme="vs-dark"
          language="c"
          :options="editorOptions"
        />
      </div>

      <div class="result-pane">
        <div class="tabs-header">
          <button :class="['tab-btn', { active: activeTab === 'tokens' }]" @click="activeTab = 'tokens'">📦 Tokens</button>
          <button :class="['tab-btn', { active: activeTab === 'ast' }]" @click="activeTab = 'ast'">🌳 语法树 (AST)</button>
          <button :class="['tab-btn', { active: activeTab === 'errors' }]" @click="activeTab = 'errors'">⚠️ 诊断信息 ({{ diagnostics.length }})</button>
          <button :class="['tab-btn', { active: activeTab === 'raw' }]" @click="activeTab = 'raw'">📄 Raw JSON</button>
        </div>

        <div class="tabs-content">
          
          <div v-if="activeTab === 'tokens'" class="tab-panel">
            <table class="data-table" v-if="tokens.length > 0">
              <thead>
                <tr>
                  <th>Line</th>
                  <th>Col</th>
                  <th>Text (值)</th>
                  <th>Type (类型)</th>
                  <th>Code (种别码)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(token, index) in tokens" :key="index">
                  <td>{{ token.line }}</td>
                  <td>{{ token.column }}</td>
                  <td class="highlight-text">{{ token.text }}</td>
                  <td><span class="badge">{{ token.kind }}</span></td>
                  <td>{{ token.code }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">暂无 Token 数据</div>
          </div>

          <div v-if="activeTab === 'ast'" class="tab-panel ast-panel">
            <div v-if="flattenedAst.length > 0">
              <div 
                v-for="(node, index) in flattenedAst" 
                :key="index" 
                class="ast-node"
                :style="{ paddingLeft: (node.depth * 24) + 'px' }"
              >
                <span class="ast-line" v-if="node.depth > 0">└─</span>
                <span class="ast-name">{{ node.name }}</span>
                <span class="ast-value" v-if="node.value"> : "{{ node.value }}"</span>
                <span class="ast-linenum" v-if="node.line">(Line: {{ node.line }})</span>
              </div>
            </div>
            <div v-else class="empty-state">暂无 AST 数据</div>
          </div>

          <div v-if="activeTab === 'errors'" class="tab-panel">
            <div v-if="diagnostics.length > 0" class="error-list">
              <div v-for="(err, index) in diagnostics" :key="index" class="error-item">
                <strong>[{{ err.code }}]</strong> Line {{ err.line }}: {{ err.message }} 
                <span class="err-phase">({{ err.phase }})</span>
              </div>
            </div>
            <div v-else class="success-state">
              🎉 完美！没有发现任何语法或词法错误。
            </div>
          </div>

          <div v-if="activeTab === 'raw'" class="tab-panel">
            <pre class="raw-json">{{ rawJson }}</pre>
          </div>

        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

// === 状态定义 ===
const sourceCode = ref('int a = 10;\nb = a;\n')
const loading = ref(false)
const activeTab = ref('tokens') // 默认打开 tokens 选项卡

// 接收后端的数据
const tokens = ref([])
const rawAst = ref(null)
const diagnostics = ref([])
const rawJson = ref('点击运行获取结果...')
const compileStatus = ref(null)

// === 核心逻辑 ===
const editorOptions = {
  automaticLayout: true,
  fontSize: 16,
  minimap: { enabled: false },
  wordWrap: 'on'
}

// 扁平化 AST 树结构，方便在 HTML 中通过循环渲染并加缩进
const flattenedAst = computed(() => {
  const result = []
  const traverse = (node, depth) => {
    if (!node) return
    result.push({ ...node, depth })
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => traverse(child, depth + 1))
    }
  }
  traverse(rawAst.value, 0)
  return result
})

// 调用后端 API
const runCompile = async () => {
  if (!sourceCode.value.trim()) return
  
  loading.value = true
  compileStatus.value = null
  
  try {
    const response = await axios.post('http://localhost:8080/api/compile', {
      sourceCode: sourceCode.value
    })
    
    const data = response.data
    
    // 解析并绑定数据
    tokens.value = data.tokens || []
    rawAst.value = data.ast || null
    diagnostics.value = data.diagnostics || []
    compileStatus.value = data.success
    
    rawJson.value = JSON.stringify(data, null, 2)
    
    // 如果有错误，自动切到错误面板
    if (!data.success) {
      activeTab.value = 'errors'
    } else if (activeTab.value === 'raw') {
      activeTab.value = 'tokens'
    }
    
  } catch (error) {
    console.error(error)
    rawJson.value = '请求失败: ' + error.message
    compileStatus.value = false
    diagnostics.value = [{ code: 'HTTP_ERR', line: 0, message: '无法连接到后端服务器', phase: 'network' }]
    activeTab.value = 'errors'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* === 全局布局 === */
.ide-container {
  display: flex; flex-direction: column; height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #1e1e1e;
}

.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 20px; background-color: #252526; color: white; height: 60px;
  border-bottom: 1px solid #3c3c3c;
}

.logo { font-size: 20px; font-weight: bold; }
.actions { display: flex; align-items: center; gap: 15px; }

.status-badge {
  padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 14px;
}
.status-badge.success { background-color: #2e7d32; color: #e8f5e9; }
.status-badge.error { background-color: #c62828; color: #ffebee; }

.run-btn {
  background-color: #0e639c; color: white; border: none;
  padding: 8px 24px; font-size: 15px; font-weight: bold; cursor: pointer; border-radius: 4px;
  transition: background 0.2s;
}
.run-btn:hover { background-color: #1177bb; }
.run-btn:disabled { background-color: #555; cursor: not-allowed; }

/* === 主体内容 === */
.main-content { display: flex; flex: 1; overflow: hidden; }
.editor-pane { flex: 5; border-right: 1px solid #3c3c3c; }
.result-pane { flex: 5; display: flex; flex-direction: column; background-color: #1e1e1e; color: #d4d4d4;}

/* === 选项卡样式 === */
.tabs-header {
  display: flex; background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c;
}
.tab-btn {
  background: none; border: none; color: #969696; padding: 12px 20px;
  font-size: 14px; cursor: pointer; border-right: 1px solid #3c3c3c;
  transition: all 0.2s;
}
.tab-btn:hover { color: #fff; background-color: #333; }
.tab-btn.active { color: #fff; background-color: #1e1e1e; border-top: 2px solid #0e639c; }

.tabs-content { flex: 1; overflow: auto; position: relative; }
.tab-panel { padding: 0; min-height: 100%; }

/* === 表格样式 (Tokens) === */
.data-table {
  width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;
}
.data-table th { background-color: #2d2d2d; padding: 10px 15px; font-weight: 600; border-bottom: 1px solid #3c3c3c; position: sticky; top: 0;}
.data-table td { padding: 8px 15px; border-bottom: 1px solid #333; }
.data-table tr:hover { background-color: #2a2d2e; }

.highlight-text { color: #ce9178; font-family: 'Consolas', monospace; font-weight: bold;}
.badge { background-color: #4d4d4d; padding: 2px 8px; border-radius: 10px; font-size: 12px; }

/* === AST 树样式 === */
.ast-panel { padding: 15px; font-family: 'Consolas', monospace; font-size: 15px; line-height: 1.8;}
.ast-line { color: #666; margin-right: 5px; }
.ast-name { color: #569cd6; font-weight: bold; }
.ast-value { color: #ce9178; }
.ast-linenum { color: #858585; font-size: 12px; margin-left: 10px;}

/* === 错误诊断样式 === */
.error-list { padding: 15px; }
.error-item {
  background-color: #3a1d1d; border-left: 4px solid #f48771; padding: 12px;
  margin-bottom: 10px; border-radius: 0 4px 4px 0; color: #f48771; font-family: 'Consolas', monospace;
}
.err-phase { color: #999; float: right; font-size: 12px;}
.success-state { padding: 30px; text-align: center; color: #4caf50; font-size: 16px; margin-top: 50px;}

/* === 通用空状态/RAW === */
.empty-state { padding: 50px; text-align: center; color: #666; }
.raw-json { padding: 15px; margin: 0; font-family: 'Consolas', monospace; font-size: 13px; color: #9cdcfe;}
</style>