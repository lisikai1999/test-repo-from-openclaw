<template>
  <div class="resource-card">
    <div class="resource-header">
      <h4 class="resource-title">{{ getTitle() }}</h4>
      <span 
        v-if="getStatus()" 
        class="status-badge" 
        :class="getStatusClass()"
      >
        {{ getStatus() }}
      </span>
    </div>
    
    <div class="resource-details">
      <div 
        v-for="(detail, idx) in getDetails()" 
        :key="idx" 
        class="detail-item"
      >
        <span class="detail-label">{{ detail.label }}:</span>
        <span class="detail-value">{{ detail.value }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResourceCard',
  props: {
    item: {
      type: Object,
      required: true
    },
    type: {
      type: String,
      required: true
    }
  },
  methods: {
    getTitle() {
      switch (this.type) {
        case 'ec2':
        case 'ec2_instances':
          return this.item.InstanceId || 'Unknown Instance'
        case 's3':
        case 's3_buckets':
          return this.item.Name || 'Unknown Bucket'
        case 'rds':
        case 'rds_instances':
          return this.item.DBInstanceIdentifier || 'Unknown RDS'
        case 'lambda':
        case 'lambda_functions':
          return this.item.FunctionName || 'Unknown Lambda'
        case 'cloudwatch':
        case 'cloudwatch_alarms':
          return this.item.AlarmName || 'Unknown Alarm'
        case 'vpc':
        case 'vpcs':
          return this.item.VpcId || 'Unknown VPC'
        case 'security_group':
        case 'security_groups':
          return this.item.GroupName || this.item.GroupId || 'Unknown Security Group'
        case 'route53':
        case 'route53_zones':
          return this.item.Name || 'Unknown Zone'
        default:
          return 'Resource'
      }
    },
    getStatus() {
      switch (this.type) {
        case 'ec2':
        case 'ec2_instances':
          return this.item.State
        case 'rds':
        case 'rds_instances':
          return this.item.DBInstanceStatus
        case 'cloudwatch':
        case 'cloudwatch_alarms':
          return this.item.StateValue
        case 'vpc':
        case 'vpcs':
          return this.item.State
        default:
          return null
      }
    },
    getStatusClass() {
      const status = this.getStatus()
      if (!status) return 'status-info'
      
      const statusLower = status.toLowerCase()
      
      if (['running', 'available', 'ok'].includes(statusLower)) {
        return 'status-success'
      }
      if (['stopped', 'stopping', 'terminated', 'alarm'].includes(statusLower)) {
        return 'status-error'
      }
      if (['pending', 'insufficient_data'].includes(statusLower)) {
        return 'status-warning'
      }
      
      return 'status-info'
    },
    getDetails() {
      const details = []
      
      switch (this.type) {
        case 'ec2':
        case 'ec2_instances':
          details.push({ label: '类型', value: this.item.InstanceType || 'N/A' })
          if (this.item.PublicIpAddress) {
            details.push({ label: '公网IP', value: this.item.PublicIpAddress })
          }
          if (this.item.PrivateIpAddress) {
            details.push({ label: '私网IP', value: this.item.PrivateIpAddress })
          }
          if (this.item.LaunchTime) {
            details.push({ label: '启动时间', value: this.item.LaunchTime })
          }
          if (this.item.VpcId) {
            details.push({ label: 'VPC', value: this.item.VpcId })
          }
          break
          
        case 's3':
        case 's3_buckets':
          if (this.item.Region) {
            details.push({ label: '区域', value: this.item.Region })
          }
          if (this.item.CreationDate) {
            details.push({ label: '创建时间', value: this.item.CreationDate })
          }
          break
          
        case 'rds':
        case 'rds_instances':
          details.push({ label: '引擎', value: `${this.item.Engine || 'N/A'} ${this.item.EngineVersion || ''}` })
          details.push({ label: '类型', value: this.item.DBInstanceClass || 'N/A' })
          if (this.item.Endpoint) {
            details.push({ label: '端点', value: this.item.Endpoint })
          }
          if (this.item.AvailabilityZone) {
            details.push({ label: '可用区', value: this.item.AvailabilityZone })
          }
          if (this.item.MultiAZ !== undefined) {
            details.push({ label: '多AZ', value: this.item.MultiAZ ? '是' : '否' })
          }
          break
          
        case 'lambda':
        case 'lambda_functions':
          details.push({ label: '运行时', value: this.item.Runtime || 'N/A' })
          details.push({ label: '内存', value: `${this.item.MemorySize || 'N/A'} MB` })
          details.push({ label: '超时', value: `${this.item.Timeout || 'N/A'} 秒` })
          if (this.item.CodeSize) {
            details.push({ label: '代码大小', value: `${(this.item.CodeSize / 1024).toFixed(2)} KB` })
          }
          if (this.item.LastModified) {
            details.push({ label: '最后修改', value: this.item.LastModified })
          }
          break
          
        case 'cloudwatch':
        case 'cloudwatch_alarms':
          details.push({ label: '指标', value: this.item.MetricName || 'N/A' })
          details.push({ label: '命名空间', value: this.item.Namespace || 'N/A' })
          if (this.item.Threshold !== undefined) {
            details.push({ label: '阈值', value: this.item.Threshold.toString() })
          }
          if (this.item.StateReason) {
            details.push({ label: '状态原因', value: this.item.StateReason })
          }
          break
          
        case 'vpc':
        case 'vpcs':
          details.push({ label: 'CIDR', value: this.item.CidrBlock || 'N/A' })
          details.push({ label: '默认VPC', value: this.item.IsDefault ? '是' : '否' })
          break
          
        case 'security_group':
        case 'security_groups':
          details.push({ label: 'ID', value: this.item.GroupId || 'N/A' })
          details.push({ label: '描述', value: this.item.Description || 'N/A' })
          if (this.item.VpcId) {
            details.push({ label: 'VPC', value: this.item.VpcId })
          }
          break
          
        case 'route53':
        case 'route53_zones':
          details.push({ label: 'ID', value: this.item.Id || 'N/A' })
          if (this.item.ResourceRecordSetCount !== undefined) {
            details.push({ label: '记录数', value: this.item.ResourceRecordSetCount.toString() })
          }
          break
      }
      
      return details
    }
  }
}
</script>

<style scoped>
.resource-card {
  padding: 0;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.resource-title {
  margin: 0;
  color: #f1f5f9;
  font-size: 1rem;
  font-family: 'Fira Code', monospace;
}

.resource-details {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px 16px;
}

.detail-item {
  display: flex;
  gap: 8px;
  font-size: 0.9rem;
}

.detail-label {
  color: #94a3b8;
  font-weight: 500;
}

.detail-value {
  color: #e4e4e7;
  font-family: 'Fira Code', monospace;
  word-break: break-all;
}
</style>
