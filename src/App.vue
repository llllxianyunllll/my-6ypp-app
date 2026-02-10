<script setup>
import { ref } from 'vue'

const guaData = ref(null)
const loading = ref(false)

// 核心函数：呼叫 Python 后端
const getGua = async () => {
  loading.value = true
  try {
    // 发送请求到 /api/index
    const res = await fetch('/api/index')
    const data = await res.json()
    guaData.value = data
  } catch (error) {
    console.error("连接失败:", error)
    alert("连接后端失败，请检查网络或部署状态")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>🔮 六爻排盘系统 (Vercel版)</h1>
    
    <button @click="getGua" :disabled="loading">
      {{ loading ? '正在排盘...' : '点击起卦' }}
    </button>

    <div v-if="guaData" class="result-box">
      <p><strong>状态：</strong> {{ guaData.message }}</p>
      <p><strong>时间：</strong> {{ guaData.time }}</p>
      <hr />
      <h2>卦名：{{ guaData.gua_name }}</h2>
      <h3>断语：{{ guaData.result }}</h3>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  font-family: Arial, sans-serif;
  padding-top: 50px;
}

button {
  padding: 10px 20px;
  font-size: 1.2em;
  cursor: pointer;
  background-color: #42b883;
  color: white;
  border: none;
  border-radius: 5px;
  margin-bottom: 20px;
}

button:disabled {
  background-color: #ccc;
}

.result-box {
  border: 1px solid #ddd;
  padding: 20px;
  border-radius: 8px;
  background-color: #f9f9f9;
  text-align: left;
}
</style>