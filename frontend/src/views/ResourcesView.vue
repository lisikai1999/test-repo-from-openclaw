<template>
  <div class="resources-view">
    <div class="card">
      <h2 class="card-title">📦 AWS资源列表</h2>
      
      <div class="form-group">
        <label for="resourceType">选择资源类型：</label>
        <select 
          id="resourceType" 
          v-model="selectedResourceType" 
          @change="loadResources"
          class="form-select"
        >
          <option value="all">全部资源</option>
          <option value="ec2">EC2 实例</option>
          <option value="s3">S3 存储桶</option>
          <option value="rds">RDS 数据库</option>
          <option value="lambda">Lambda 函数</option>
        </select>
      </div>
      
      <div class="form-group">
        <button class="btn btn-primary" @click="loadResources" :disabled="isLoading">
          <span v-if="isLoading">🔄 加载中...</span>
          <span v-else>🔄 刷新资源</span>
        </button>
      </div>
    </div>
    
    <div v-if="isLoading" class="card">
      <div class="loading">
        <div class="spinner"></div>
        <p>正在加载AWS资源信息...</p>
      </div>
    </div>
    
    <transition-group name="fade" tag="div">
      <div v-if="resources" key="resources" class="card">
        <h2 class="card-title">📋 资源信息</h2>
        
        <div v-if="selectedResourceType === 'all'">
          <div 
            v-for="(resourceData, resourceType) in resources" 
            :key="resourceType" 
            class="section"
          >
            <div class="section-header">
              <div class="section-icon">{{ getResourceIcon(resourceType) }}</div>
              <h3>{{ getResourceTypeName(resourceType) }}</h3>
              <span class="status-badge status-info">
                {{ getResourceCount(resourceData) }} 个资源
              </span>
            </div>
            
            <div v-if="isResourceError(resourceData)" class="list-group-item priority-high">
              <p style="color: #f87171;">❌ 错误: {{ resourceData.error }}</p>
            </div>
            
            <div v-else-if="resourceData && resourceData.length > 0">
              <div 
                v-for="(item, idx) in resourceData.slice(0, 5)" 
                :key="idx" 
                class="list-group-item"
              >
                <ResourceCard :item="item" :type="resourceType" />
              </div>
              <p v-if="resourceData.length > 5" style="text-align: center; color: #94a3b8; margin-top: 12px;">
                ... 还有 {{ resourceData.length - 5 }} 个资源
              </p>
            </div>
            
            <div v-else>
              <div class="list-group-item">
                <p style="color: #94a3b8; text-align: center;">暂无资源</p>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else>
          <div v-if="isResourceError(resources)" class="list-group-item priority-high">
            <p style="color: #f87171;">❌ 错误: {{ resources.error }}</p>
          </div>
          
          <div v-else-if="resources && resources.length > 0">
            <div 
              v-for="(item, idx) in resources" 
              :key="idx" 
              class="list-group-item"
            >
              <ResourceCard :item="item" :type="selectedResourceType" />
            </div>
          </div>
          
          <div v-else>
            <div class="list-group-item">
              <p style="color: #94a3b8; text-align: center;">暂无资源</p>
            </div>
          </div>
        </div>
      </div>
    </transition-group>
    
    <div v-if="error" class="card">
      <div class="list-group-item priority-high">
        <p style="color: #f87171;">❌ {{ error }}</p>
        <p style="color: #94a3b8; margin-top: 8px;">
          请确保您的AWS凭证已正确配置，并且具有相应的权限。
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ResourceCard from '../components/ResourceCard.vue'

export default {
  name: 'ResourcesView',
  components: {
    ResourceCard
  },
  data() {
    return {
      selectedResourceType: 'all',
      resources: null,
      isLoading: false,
      error: null
    }
  },
  mounted() {
    this.loadResources()
  },
  methods: {
    async loadResources() {
      this.isLoading = true
      this.error = null
      this.resources = null
      
      try {
        const params = { type: this.selectedResourceType }
        const response = await axios.get('/api/aws/resources', { params })
        
        this.resources = response.data.resources
      } catch (err) {
        console.error('加载资源失败:', err)
        this.error = err.response?.data?.error || '加载资源时发生错误'
      } finally {
        this.isLoading = false
      }
    },
    getResourceIcon(type) {
      const icons = {
        'ec2': '🖥️',
        's3': '💾',
        'rds': '🗄️',
        'lambda': '⚡',
        'cloudwatch': '📊',
        'vpc': '🌐',
        'security_group': '🔒',
        'route53': '🔗'
      }
      return icons[type] || '📦'
    },
    getResourceTypeName(type) {
      const names = {
        'ec2_instances': 'EC2 实例',
        's3_buckets': 'S3 存储桶',
        'rds_instances': 'RDS 数据库',
        'lambda_functions': 'Lambda 函数',
        'cloudwatch_alarms': 'CloudWatch 告警',
        'vpcs': 'VPC 网络',
        'security_groups': '安全组',
        'route53_zones': 'Route53 DNS',
        'ec2': 'EC2 实例',
        's3': 'S3 存储桶',
        'rds': 'RDS 数据库',
        'lambda': 'Lambda 函数'
      }
      return names[type] || type
    },
    getResourceCount(data) {
      if (this.isResourceError(data)) return 0
      if (Array.isArray(data)) return data.length
      return 0
    },
    isResourceError(data) {
      return data && typeof data === 'object' && 'error' in data
    }
  }
}
</script>

<style scoped>
.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.6);
  color: #e4e4e7;
  font-size: 1rem;
  cursor: pointer;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.form-select:focus {
  outline: none;
  border-color: #60a5fa;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
}

.form-select option {
  background: rgba(15, 23, 42, 0.9);
  color: #e4e4e7;
}
</style>
