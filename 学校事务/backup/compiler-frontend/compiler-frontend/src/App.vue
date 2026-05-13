<!-- @author 黄彬 (12303070250) -->
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
          <button :class="['tab-btn', { active: activeTab === 'tokens' }]" @click="activeTab = 'tokens'">Tokens</button>
          <button :class="['tab-btn', { active: activeTab === 'ast' }]" @click="activeTab = 'ast'">AST</button>
          <button :class="['tab-btn', { active: activeTab === 'quads' }]" @click="activeTab = 'quads'">IR</button>
          <button :class="['tab-btn', { active: activeTab === 'output' }]" @click="activeTab = 'output'">Output</button>
          <button :class="['tab-btn', { active: activeTab === 'asm' }]" @click="activeTab = 'asm'">MASM</button>
          <button :class="['tab-btn', { active: activeTab === 'llvm' }]" @click="activeTab = 'llvm'">LLVM</button>
          <button :class="['tab-btn', { active: activeTab === 'cfg' }]" @click="activeTab = 'cfg'">CFG</button>
          <button :class="['tab-btn', { active: activeTab === 'log' }]" @click="activeTab = 'log'">Log</button>
          <button :class="['tab-btn', { active: activeTab === 'errors' }]" @click="activeTab = 'errors'">Err({{ diagnostics.length }})</button>
          <button :class="['tab-btn', { active: activeTab === 'raw' }]" @click="activeTab = 'raw'">JSON</button>
        </div>

        <div class="tabs-content">
          
          <div v-if="activeTab === 'tokens'" class="tab-panel">
            <table class="data-table" v-if="tokens.length > 0">
              <thead><tr><th>Line</th><th>Col</th><th>Text</th><th>Type</th><th>Code</th></tr></thead>
              <tbody>
                <tr v-for="(token, index) in tokens" :key="index">
                  <td>{{ token.line }}</td><td>{{ token.column }}</td>
                  <td class="highlight-text">{{ token.text }}</td>
                  <td><span class="badge">{{ token.kind }}</span></td><td>{{ token.code }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">暂无 Token 数据</div>
          </div>

          <div v-if="activeTab === 'ast'" class="tab-panel ast-panel">
            <div v-if="flattenedAst.length > 0">
              <div v-for="(node, index) in flattenedAst" :key="index" class="ast-node" :style="{ paddingLeft: (node.depth * 24) + 'px' }">
                <span class="ast-line" v-if="node.depth > 0">└─</span>
                <span class="ast-name">{{ node.name }}</span>
                <span class="ast-value" v-if="node.value"> : "{{ node.value }}"</span>
              </div>
            </div>
            <div v-else class="empty-state">暂无 AST 数据</div>
          </div>

          <div v-if="activeTab === 'quads'" class="tab-panel quad-panel">
            <div v-if="quads && quads.length > 0">
              <div v-for="(quad, index) in quads" :key="index" class="quad-item">
                {{ quad }}
              </div>
            </div>
            <div v-else class="empty-state">暂无四元式数据 (请检查语法是否完全正确)</div>
          </div>

          <div v-if="activeTab === 'output'" class="tab-panel output-panel">
            <div v-if="interpreterOutput && interpreterOutput.length > 0" class="console-box">
              <div v-for="(log, index) in interpreterOutput" :key="index" class="console-line">
                > {{ log }}
              </div>
            </div>
            <div v-else class="empty-state">解释器未运行或无输出</div>
          </div>

          <div v-if="activeTab === 'asm'" class="tab-panel asm-panel">
            <div v-if="assemblyCode" class="asm-toolbar">
              <button class="copy-btn" @click="copyAssemblyCode">{{ copied ? '✅ 已复制' : '📋 复制汇编代码' }}</button>
            </div>
            <pre class="asm-code" v-if="assemblyCode">{{ assemblyCode }}</pre>
            <div v-else class="empty-state">暂无汇编代码 (请检查语法是否完全正确)</div>
          </div>

          <div v-if="activeTab === 'llvm'" class="tab-panel asm-panel">
            <div v-if="llvmIR" class="asm-toolbar">
              <button class="copy-btn" @click="copyLLVMIR">{{ llvmCopied ? '✅ 已复制' : '📋 复制 LLVM IR' }}</button>
            </div>
            <pre class="asm-code" v-if="llvmIR">{{ llvmIR }}</pre>
            <div v-else class="empty-state">暂无 LLVM IR 代码</div>
          </div>

          <div v-if="activeTab === 'cfg'" class="tab-panel cfg-panel">
            <div v-if="cfgAnalysis">
              <div class="cfg-section">
                <h3 class="cfg-title">控制流图 (CFG)</h3>
                <pre class="cfg-code">{{ cfgAnalysis.flowGraph }}</pre>
              </div>
              <div class="cfg-section">
                <h3 class="cfg-title">DAG 局部优化</h3>
                <div class="cfg-stats">
                  <span class="cfg-stat">基本块: {{ cfgAnalysis.blockCount }}</span>
                  <span class="cfg-stat">消除公共子表达式: {{ cfgAnalysis.eliminatedCount }} 条</span>
                </div>
                <pre class="cfg-code">{{ cfgAnalysis.dagSummary }}</pre>
              </div>
            </div>
            <div v-else class="empty-state">暂无流图/DAG 分析数据</div>
          </div>

          <div v-if="activeTab === 'log'" class="tab-panel log-panel">
            <div v-if="compileLog && compileLog.stages">
              <table class="log-table">
                <thead><tr><th>阶段</th><th>时间</th><th>耗时</th><th>输入</th><th>输出</th></tr></thead>
                <tbody>
                  <tr v-for="(stage, index) in compileLog.stages" :key="index">
                    <td class="log-stage">{{ stage.stage }}</td>
                    <td>{{ stage.time }}</td>
                    <td>{{ stage.durationMs }}ms</td>
                    <td>{{ stage.input }}</td>
                    <td>{{ stage.output }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="log-summary">
                总阶段: {{ compileLog.totalStages }} | 总耗时: {{ compileLog.totalDurationMs }}ms
              </div>
            </div>
            <div v-else class="empty-state">暂无编译日志</div>
          </div>

          <div v-if="activeTab === 'errors'" class="tab-panel">
            <div v-if="diagnostics.length > 0" class="error-list">
              <div v-for="(err, index) in diagnostics" :key="index" class="error-item">
                <strong>[{{ err.code }}]</strong>
                <span v-if="err.line && err.line > 0"> Line {{ err.line }}: </span>
                <span v-else> </span>
                {{ err.message }} 
              </div>
            </div>
            <div v-else class="success-state">🎉 完美！没有发现任何语法或词法错误。</div>
          </div>

          <div v-if="activeTab === 'raw'" class="tab-panel"><pre class="raw-json">{{ rawJson }}</pre></div>

        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

const sourceCode = ref('//IDE test\nconst int x;\nvoid main()\n')
const loading = ref(false)
const activeTab = ref('output')

const tokens = ref([])
const rawAst = ref(null)
const diagnostics = ref([])
const quads = ref([])
const interpreterOutput = ref([])
const assemblyCode = ref('')
const rawJson = ref('点击运行获取结果...')
const compileStatus = ref(null)
const copied = ref(false)
const llvmCopied = ref(false)
const llvmIR = ref('')
const compileLog = ref(null)
const cfgAnalysis = ref(null)

const editorOptions = { automaticLayout: true, fontSize: 16, minimap: { enabled: false } }

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

const runCompile = async () => {
  if (!sourceCode.value.trim()) return
  loading.value = true
  compileStatus.value = null
  
  try {
    const response = await axios.post('http://localhost:8080/api/compile', { sourceCode: sourceCode.value })
    const data = response.data
    
    tokens.value = data.tokens || []
    rawAst.value = data.ast || null
    diagnostics.value = data.diagnostics || []
    quads.value = data.quads || []
    interpreterOutput.value = data.interpreterOutput || []
    assemblyCode.value = data.assemblyCode || ''
    llvmIR.value = data.llvmIR || ''
    compileLog.value = data.compileLog || null
    cfgAnalysis.value = data.cfgAnalysis || null
    compileStatus.value = data.success
    rawJson.value = JSON.stringify(data, null, 2)
    
    if (!data.success) {
      activeTab.value = 'errors'
    } else {
      activeTab.value = 'output' 
    }
  } catch (error) {
    rawJson.value = '请求失败: ' + error.message
    compileStatus.value = false
    activeTab.value = 'errors'
  } finally {
    loading.value = false
  }
}

const copyAssemblyCode = async () => {
  try {
    await navigator.clipboard.writeText(assemblyCode.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = assemblyCode.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

const copyLLVMIR = async () => {
  try {
    await navigator.clipboard.writeText(llvmIR.value)
    llvmCopied.value = true
    setTimeout(() => { llvmCopied.value = false }, 2000)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = llvmIR.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    llvmCopied.value = true
    setTimeout(() => { llvmCopied.value = false }, 2000)
  }
}
</script>

<style scoped>
.ide-container { display: flex; flex-direction: column; height: 100vh; font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #1e1e1e; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 0 20px; background-color: #252526; color: white; height: 60px; border-bottom: 1px solid #3c3c3c; }
.logo { font-size: 20px; font-weight: bold; }
.actions { display: flex; align-items: center; gap: 15px; }
.status-badge { padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 14px; }
.status-badge.success { background-color: #2e7d32; color: #e8f5e9; }
.status-badge.error { background-color: #c62828; color: #ffebee; }
.run-btn { background-color: #0e639c; color: white; border: none; padding: 8px 24px; font-size: 15px; font-weight: bold; cursor: pointer; border-radius: 4px; transition: background 0.2s; }
.run-btn:hover { background-color: #1177bb; }
.main-content { display: flex; flex: 1; overflow: hidden; }
.editor-pane { flex: 6; border-right: 1px solid #3c3c3c; }
.result-pane { flex: 4; display: flex; flex-direction: column; background-color: #1e1e1e; color: #d4d4d4;}
.tabs-header { display: flex; background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c; overflow-x: auto; flex-shrink: 0; }
.tab-btn { background: none; border: none; color: #969696; padding: 8px 10px; font-size: 12px; cursor: pointer; border-right: 1px solid #3c3c3c; white-space: nowrap; flex-shrink: 0; }
.tab-btn:hover { color: #fff; background-color: #333; }
.tab-btn.active { color: #fff; background-color: #1e1e1e; border-bottom: 2px solid #0e639c; }
.tabs-content { flex: 1; overflow: auto; position: relative; }
.tab-panel { padding: 0; min-height: 100%; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }
.data-table th { background-color: #2d2d2d; padding: 10px 15px; font-weight: 600; border-bottom: 1px solid #3c3c3c; position: sticky; top: 0;}
.data-table td { padding: 8px 15px; border-bottom: 1px solid #333; }
.highlight-text { color: #ce9178; font-family: 'Consolas', monospace; font-weight: bold;}
.badge { background-color: #4d4d4d; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.ast-panel { padding: 15px; font-family: 'Consolas', monospace; font-size: 15px; line-height: 1.8;}
.ast-line { color: #666; margin-right: 5px; }
.ast-name { color: #569cd6; font-weight: bold; }
.ast-value { color: #ce9178; }
.error-list { padding: 15px; }
.error-item { background-color: #3a1d1d; border-left: 4px solid #f48771; padding: 12px; margin-bottom: 10px; color: #f48771; font-family: 'Consolas', monospace; }
.success-state { padding: 30px; text-align: center; color: #4caf50; font-size: 16px; margin-top: 50px;}
.empty-state { padding: 50px; text-align: center; color: #666; }
.raw-json { padding: 15px; margin: 0; font-family: 'Consolas', monospace; font-size: 13px; color: #9cdcfe;}

.quad-panel { padding: 15px; font-family: 'Consolas', monospace; font-size: 16px; color: #dcdcaa; line-height: 1.8;}
.quad-item { background-color: #2d2d2d; padding: 8px 12px; margin-bottom: 5px; border-radius: 4px; border-left: 3px solid #dcdcaa;}
.output-panel { padding: 15px; }
.console-box { background-color: #000; padding: 20px; border-radius: 6px; font-family: 'Consolas', monospace; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); min-height: 300px;}
.console-line { color: #4af626; font-size: 15px; line-height: 1.6; margin-bottom: 8px; text-shadow: 0 0 5px rgba(74, 246, 38, 0.3);}
.asm-panel { padding: 0; display: flex; flex-direction: column; height: 100%; }
.asm-toolbar { display: flex; justify-content: flex-end; padding: 8px 12px; background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c; }
.copy-btn { background-color: #3c3c3c; color: #d4d4d4; border: 1px solid #555; padding: 5px 14px; font-size: 13px; cursor: pointer; border-radius: 4px; transition: background 0.2s; }
.copy-btn:hover { background-color: #4d4d4d; color: #fff; }
.asm-code { margin: 0; padding: 15px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.5; color: #d4d4d4; background-color: #1e1e1e; white-space: pre; overflow: auto; flex: 1; }
.cfg-panel { padding: 15px; overflow: auto; height: 100%; }
.cfg-section { margin-bottom: 20px; }
.cfg-title { font-size: 15px; color: #569cd6; margin: 0 0 10px 0; padding-bottom: 6px; border-bottom: 1px solid #3c3c3c; }
.cfg-stats { display: flex; gap: 24px; margin-bottom: 12px; }
.cfg-stat { background-color: #2d2d2d; padding: 4px 14px; border-radius: 4px; font-size: 13px; color: #dcdcaa; }
.cfg-code { margin: 0; padding: 12px; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; color: #9cdcfe; background-color: #252526; border-radius: 4px; white-space: pre; overflow: auto; max-height: 400px; }
.log-panel { padding: 15px; overflow: auto; }
.log-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.log-table th { background-color: #2d2d2d; padding: 10px 12px; text-align: left; border-bottom: 1px solid #3c3c3c; position: sticky; top: 0; }
.log-table td { padding: 8px 12px; border-bottom: 1px solid #333; }
.log-stage { color: #569cd6; font-weight: bold; white-space: nowrap; }
.log-summary { margin-top: 14px; padding: 10px 14px; background-color: #2d2d2d; border-radius: 4px; font-size: 14px; color: #4ec9b0; text-align: right; }
</style>