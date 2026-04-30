<template>
  <div class="home-view">
    <div class="card">
      <h2 class="card-title">💬 请描述您的AWS问题</h2>
      
      <div class="form-group">
        <label for="question">用自然语言描述您遇到的问题：</label>
        <textarea 
          id="question" 
          v-model="question" 
          placeholder="例如：我的EC2实例无法连接，可能是什么原因？或者：我的RDS数据库性能很慢..."
          :disabled="isAnalyzing"
        ></textarea>
      </div>
      
      <div class="form-group">
        <button 
          class="btn btn-primary" 
          @click="analyzeQuestion" 
          :disabled="!question.trim() || isAnalyzing"
        >
          <span v-if="isAnalyzing">🔄 分析中...</span>
          <span v-else>🚀 开始分析</span>
        </button>
      </div>
    </div>
    
    <div v-if="isAnalyzing" class="card">
      <div class="loading">
        <div class="spinner"></div>
        <p>{{ currentStatus }}</p>
      </div>
    </div>
    
    <transition-group name="slide" tag="div">
      <div v-if="analysisResult" key="result" class="card">
        <h2 class="card-title">📋 分析结果</h2>
        
        <div class="section">
          <div class="section-header">
            <div class="section-icon">📝</div>
            <h3>问题信息</h3>
          </div>
          <div class="list-group-item">
            <p><strong>原始问题：</strong>{{ analysisResult.question }}</p>
            <div class="tags">
              <span 
                v-for="service in analysisResult.analysis_history[0]?.analysis?.relevant_services || []" 
                :key="service" 
                class="tag"
              >
                {{ service.toUpperCase() }}
              </span>
              <span 
                v-for="problem in analysisResult.analysis_history[0]?.analysis?.problem_type || []" 
                :key="problem" 
                class="tag"
              >
                {{ problem }}
              </span>
            </div>
          </div>
        </div>
        
        <div class="section">
          <div class="section-header">
            <div class="section-icon">🔍</div>
            <h3>根因分析</h3>
          </div>
          
          <div class="list-group-item" :class="'priority-' + (analysisResult.root_cause_analysis.identified ? 'high' : 'medium')">
            <p>
              <span class="status-badge" :class="analysisResult.root_cause_analysis.identified ? 'status-warning' : 'status-info'">
                {{ analysisResult.root_cause_analysis.identified ? '⚠️ 已识别问题' : 'ℹ️ 一般分析' }}
              </span>
            </p>
            
            <div v-if="analysisResult.root_cause_analysis.categories.length > 0" style="margin-top: 12px;">
              <h4 style="margin-bottom: 8px; color: #f1f5f9;">问题分类：</h4>
              <div class="tags">
                <span v-for="cat in analysisResult.root_cause_analysis.categories" :key="cat" class="tag">
                  {{ cat }}
                </span>
              </div>
            </div>
            
            <div v-if="analysisResult.root_cause_analysis.specific_issues.length > 0" style="margin-top: 16px;">
              <h4 style="margin-bottom: 8px; color: #f1f5f9;">具体问题：</h4>
              <ul style="margin-left: 24px; color: #e4e4e7;">
                <li v-for="(issue, idx) in analysisResult.root_cause_analysis.specific_issues" :key="idx">
                  {{ issue }}
                </li>
              </ul>
            </div>
            
            <div style="margin-top: 16px;">
              <h4 style="margin-bottom: 8px; color: #f1f5f9;">分析置信度：</h4>
              <div class="confidence-bar">
                <div 
                  class="confidence-fill" 
                  :style="{ width: (analysisResult.confidence * 100) + '%' }"
                ></div>
              </div>
              <p class="confidence-text">{{ Math.round(analysisResult.confidence * 100) }}%</p>
            </div>
          </div>
        </div>
        
        <div class="section">
          <div class="section-header">
            <div class="section-icon">📊</div>
            <h3>分析过程</h3>
          </div>
          
          <div class="timeline">
            <div 
              v-for="(step, idx) in analysisResult.analysis_process" 
              :key="idx" 
              class="timeline-item"
            >
              <div class="timeline-step">步骤 {{ step.step }}</div>
              <div class="timeline-action">{{ step.action }}</div>
              <div class="timeline-description">{{ step.description }}</div>
            </div>
          </div>
        </div>
        
        <div class="section">
          <div class="section-header">
            <div class="section-icon">💡</div>
            <h3>解决方案</h3>
          </div>
          
          <div v-if="analysisResult.solutions.length === 0" class="list-group-item">
            <p style="color: #94a3b8;">暂无特定的解决方案建议。</p>
          </div>
          
          <div 
            v-for="(solution, idx) in analysisResult.solutions" 
            :key="idx" 
            class="list-group-item"
            :class="'priority-' + solution.priority"
          >
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h4 style="color: #f1f5f9; margin: 0;">{{ solution.action }}</h4>
              <span class="status-badge" :class="getStatusClass(solution.priority)">
                {{ solution.priority === 'high' ? '🔴 高优先级' : solution.priority === 'medium' ? '🟡 中优先级' : '🟢 低优先级' }}
              </span>
            </div>
            
            <p style="color: #94a3b8; margin-bottom: 12px;">{{ solution.description }}</p>
            
            <div v-if="solution.steps && solution.steps.length > 0">
              <h5 style="color: #cbd5e1; margin-bottom: 8px;">操作步骤：</h5>
              <ol style="margin-left: 24px; color: #e4e4e7;">
                <li v-for="(step, stepIdx) in solution.steps" :key="stepIdx" style="margin-bottom: 6px;">
                  {{ step }}
                </li>
              </ol>
            </div>
          </div>
        </div>
        
        <div class="section">
          <div class="section-header">
            <div class="section-icon">📦</div>
            <h3>收集的数据摘要</h3>
          </div>
          
          <div class="data-grid">
            <div 
              v-for="(data, resourceType) in analysisResult.collected_data_summary" 
              :key="resourceType" 
              class="data-card"
            >
              <h4>{{ getResourceTypeName(resourceType) }}</h4>
              <p v-if="data.error" style="color: #f87171;">错误: {{ data.error }}</p>
              <p v-else-if="data.count !== undefined">
                发现 {{ data.count }} 个资源
              </p>
              <p v-else>数据已收集</p>
            </div>
          </div>
        </div>
        
        <div v-if="analysisResult.follow_up_questions && analysisResult.follow_up_questions.length > 0" class="follow-up">
          <h4>❓ 建议提供更多信息</h4>
          <ul>
            <li v-for="(q, idx) in analysisResult.follow_up_questions" :key="idx">{{ q }}</li>
          </ul>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'HomeView',
  data() {
    return {
      question: '',
      isAnalyzing: false,
      analysisResult: null,
      currentStatus: ''
    }
  },
  methods: {
    async analyzeQuestion() {
      if (!this.question.trim()) return
      
      this.isAnalyzing = true
      this.analysisResult = null
      this.currentStatus = '正在解析您的问题...'
      
      try {
        this.currentStatus = '正在收集AWS资源信息...'
        
        const response = await axios.post('/api/analyze', {
          question: this.question
        })
        
        this.currentStatus = '正在进行根因分析...'
        await this.delay(500)
        
        this.currentStatus = '正在生成解决方案...'
        await this.delay(300)
        
        this.analysisResult = response.data
      } catch (error) {
        console.error('分析失败:', error)
        alert('分析过程中发生错误: ' + (error.response?.data?.error || error.message))
      } finally {
        this.isAnalyzing = false
        this.currentStatus = ''
      }
    },
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    },
    getStatusClass(priority) {
      switch (priority) {
        case 'high': return 'status-error'
        case 'medium': return 'status-warning'
        case 'low': return 'status-success'
        default: return 'status-info'
      }
    },
    getResourceTypeName(type) {
      const names = {
        'ec2': 'EC2 实例',
        's3': 'S3 存储桶',
        'rds': 'RDS 数据库',
        'lambda': 'Lambda 函数',
        'cloudwatch': 'CloudWatch 告警',
        'vpc': 'VPC 网络',
        'security_group': '安全组',
        'route53': 'Route53 DNS'
      }
      return names[type] || type
    }
  }
}
</script>
