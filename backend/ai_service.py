import os
import json
import re
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class BaseAIService(ABC):
    @abstractmethod
    def analyze_question(self, question: str, context: Dict = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def decide_data_collection(self, question: str, current_data: Dict, 
                                previous_analysis: Dict = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def perform_root_cause_analysis(self, question: str, collected_data: Dict,
                                     analysis_history: List = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def check_data_sufficiency(self, question: str, collected_data: Dict,
                                analysis_history: List = None) -> Dict[str, Any]:
        pass


class MockAIService(BaseAIService):
    def __init__(self):
        self.service_keywords = {
            'ec2': ['ec2', 'virtual machine', 'vm', 'instance', 'server', 'compute', 'ssh', '远程连接'],
            's3': ['s3', 'bucket', 'storage', 'object storage', '存储桶', '文件存储'],
            'rds': ['rds', 'database', 'db', 'mysql', 'postgres', 'aurora', 'sql', '数据库'],
            'lambda': ['lambda', 'serverless', 'function', 'faas', '无服务器', '函数'],
            'cloudwatch': ['cloudwatch', 'monitoring', 'metrics', 'alarms', 'logs', '监控', '日志', '告警'],
            'vpc': ['vpc', 'network', 'subnet', 'security group', 'route table', '网络', '子网'],
            'security_group': ['security group', '安全组', 'firewall', '防火墙', 'sg', '端口'],
            'route53': ['route53', 'dns', 'domain', 'hosted zone', '域名', 'dns解析'],
            'elb': ['elb', 'load balancer', 'alb', 'nlb', '负载均衡'],
            'cloudfront': ['cloudfront', 'cdn', 'content delivery', '内容分发'],
            'iam': ['iam', 'identity', 'permission', 'role', 'policy', '权限', '角色'],
            'auto_scaling': ['autoscaling', 'auto scaling', 'asg', '自动扩缩容']
        }
        
        self.problem_keywords = {
            'connectivity': ['cannot connect', 'unable to connect', 'connection failed', 'timeout', 
                            '网络问题', '无法连接', '连接失败', '超时', "can't connect", 'no connection',
                            'connection refused', 'ping'],
            'performance': ['slow', 'performance', 'high latency', 'slow response', 'high cpu', 
                           'high memory', 'lag', 'slow down', 'bottleneck', 'throughput',
                           '慢', '性能', '延迟高', '响应慢', 'CPU高', '内存高', '卡顿'],
            'error': ['error', 'failed', 'exception', 'issue', 'problem', 'not working', 
                     'broken', 'crash', 'crashed', 'failure',
                     '错误', '失败', '异常', '问题', '不工作', '崩溃', '500', '404'],
            'cost': ['cost', 'bill', 'expense', 'price', 'too expensive', 'high cost',
                    '费用', '账单', '太贵', '成本高', '扣费'],
            'security': ['security', 'vulnerable', 'hack', 'attack', 'breach', 'unauthorized',
                        'permission', 'access denied', 'forbidden', '403',
                        '安全', '漏洞', '攻击', '未授权', '权限', '拒绝访问'],
            'availability': ['down', 'offline', 'unavailable', 'not running', 'stopped',
                            'high availability', 'downtime', 'outage',
                            '宕机', '离线', '不可用', '停止', '停机', '维护']
        }
        
        self.instance_id_pattern = re.compile(r'i-[0-9a-f]{17}')
        self.arn_pattern = re.compile(r'arn:aws:[\w-]+:[a-z0-9-]*:\d{12}:[\w/:-]+')
    
    def analyze_question(self, question: str, context: Dict = None) -> Dict[str, Any]:
        question_lower = question.lower()
        
        relevant_services = self._identify_services(question_lower)
        problem_types = self._identify_problem_types(question_lower)
        entities = self._extract_entities(question)
        
        required_data_types = self._determine_required_data(relevant_services, problem_types, question)
        
        return {
            'original_question': question,
            'relevant_services': relevant_services,
            'problem_types': problem_types,
            'entities': entities,
            'required_data_types': required_data_types,
            'analysis_confidence': self._calculate_confidence(relevant_services, problem_types, entities),
            'initial_hypotheses': self._generate_initial_hypotheses(relevant_services, problem_types, question)
        }
    
    def decide_data_collection(self, question: str, current_data: Dict,
                                previous_analysis: Dict = None) -> Dict[str, Any]:
        analysis = previous_analysis or self.analyze_question(question)
        
        required_data_types = analysis.get('required_data_types', [])
        
        data_to_collect = []
        for data_type in required_data_types:
            if data_type not in current_data or self._is_data_empty(current_data.get(data_type)):
                data_to_collect.append({
                    'type': data_type,
                    'priority': 'high' if data_type in analysis.get('relevant_services', []) else 'medium',
                    'reason': f'需要 {data_type} 数据来分析问题'
                })
        
        for service in analysis.get('relevant_services', []):
            related_data = self._get_related_data_types(service)
            for data_type in related_data:
                if data_type not in current_data or self._is_data_empty(current_data.get(data_type)):
                    if not any(d['type'] == data_type for d in data_to_collect):
                        data_to_collect.append({
                            'type': data_type,
                            'priority': 'medium',
                            'reason': f'与 {service} 分析相关'
                        })
        
        if 'connectivity' in analysis.get('problem_types', []):
            for data_type in ['vpc', 'security_group', 'route53']:
                if data_type not in current_data or self._is_data_empty(current_data.get(data_type)):
                    if not any(d['type'] == data_type for d in data_to_collect):
                        data_to_collect.append({
                            'type': data_type,
                            'priority': 'high',
                            'reason': '连接性问题需要检查网络配置'
                        })
        
        if 'performance' in analysis.get('problem_types', []):
            if 'cloudwatch' not in current_data or self._is_data_empty(current_data.get('cloudwatch')):
                if not any(d['type'] == 'cloudwatch' for d in data_to_collect):
                    data_to_collect.append({
                        'type': 'cloudwatch',
                        'priority': 'high',
                        'reason': '性能问题需要监控指标数据'
                    })
        
        return {
            'need_more_data': len(data_to_collect) > 0,
            'data_to_collect': data_to_collect,
            'reasoning': self._generate_collection_reasoning(question, analysis, data_to_collect)
        }
    
    def perform_root_cause_analysis(self, question: str, collected_data: Dict,
                                     analysis_history: List = None) -> Dict[str, Any]:
        root_causes = []
        contributing_factors = []
        analysis_steps = []
        
        analysis_steps.append({
            'step': 1,
            'action': '问题解析',
            'description': f'解析用户问题: "{question}"'
        })
        
        for data_type, data in collected_data.items():
            if not self._is_data_empty(data) and not isinstance(data, dict):
                analysis_steps.append({
                    'step': len(analysis_steps) + 1,
                    'action': f'分析 {data_type.upper()} 数据',
                    'description': f'检查 {len(data) if isinstance(data, list) else 1} 个资源的配置和状态'
                })
                
                findings = self._analyze_resource_data(data_type, data, question)
                if findings:
                    for finding in findings:
                        if finding['type'] == 'root_cause':
                            root_causes.append(finding)
                        else:
                            contributing_factors.append(finding)
        
        if not root_causes:
            analysis_steps.append({
                'step': len(analysis_steps) + 1,
                'action': '综合分析',
                'description': '未发现明显的配置问题，可能需要更多信息或进一步诊断'
            })
            
            root_causes.append({
                'type': 'root_cause',
                'category': 'General',
                'description': '未发现明确的根本原因',
                'severity': 'low',
                'confidence': 0.3
            })
        else:
            analysis_steps.append({
                'step': len(analysis_steps) + 1,
                'action': '根因确认',
                'description': f'识别到 {len(root_causes)} 个潜在的根本原因'
            })
        
        solutions = self._generate_solutions(root_causes, contributing_factors, question)
        
        return {
            'root_causes': root_causes,
            'contributing_factors': contributing_factors,
            'analysis_steps': analysis_steps,
            'solutions': solutions,
            'overall_confidence': self._calculate_overall_confidence(root_causes, collected_data),
            'recommendations': self._generate_recommendations(question, root_causes)
        }
    
    def check_data_sufficiency(self, question: str, collected_data: Dict,
                                analysis_history: List = None) -> Dict[str, Any]:
        analysis = self.analyze_question(question)
        required_data_types = analysis.get('required_data_types', [])
        
        missing_data = []
        partial_data = []
        sufficient_data = []
        
        for data_type in required_data_types:
            if data_type not in collected_data:
                missing_data.append({
                    'type': data_type,
                    'reason': '完全缺失'
                })
            elif self._is_data_empty(collected_data.get(data_type)):
                partial_data.append({
                    'type': data_type,
                    'reason': '数据为空或采集失败'
                })
            else:
                sufficient_data.append({
                    'type': data_type,
                    'reason': '数据充足'
                })
        
        for service in analysis.get('relevant_services', []):
            related_data = self._get_related_data_types(service)
            for data_type in related_data:
                if data_type not in required_data_types:
                    if data_type not in collected_data or self._is_data_empty(collected_data.get(data_type)):
                        if not any(d['type'] == data_type for d in missing_data + partial_data):
                            partial_data.append({
                                'type': data_type,
                                'reason': f'与 {service} 相关，但非必须'
                            })
        
        is_sufficient = len(missing_data) == 0
        
        return {
            'is_sufficient': is_sufficient,
            'missing_data': missing_data,
            'partial_data': partial_data,
            'sufficient_data': sufficient_data,
            'confidence_score': self._calculate_sufficiency_confidence(missing_data, partial_data, analysis),
            'recommended_next_steps': self._generate_sufficiency_recommendations(missing_data, partial_data, question)
        }
    
    def _identify_services(self, question_lower: str) -> List[str]:
        services = set()
        
        for service, keywords in self.service_keywords.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    services.add(service)
                    break
        
        if not services:
            if any(word in question_lower for word in ['连接', '网络', '无法访问', 'ping', 'ssh']):
                services.add('ec2')
                services.add('vpc')
                services.add('security_group')
            elif any(word in question_lower for word in ['存储', '文件', '上传', '下载']):
                services.add('s3')
            elif any(word in question_lower for word in ['查询', '数据', '表', 'sql']):
                services.add('rds')
        
        return list(services)
    
    def _identify_problem_types(self, question_lower: str) -> List[str]:
        problems = set()
        
        for problem_type, keywords in self.problem_keywords.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    problems.add(problem_type)
                    break
        
        return list(problems)
    
    def _extract_entities(self, question: str) -> Dict[str, List[str]]:
        entities = {
            'instance_ids': [],
            'arns': [],
            'bucket_names': [],
            'other_identifiers': []
        }
        
        instance_ids = self.instance_id_pattern.findall(question)
        entities['instance_ids'] = instance_ids
        
        arns = self.arn_pattern.findall(question)
        entities['arns'] = arns
        
        bucket_pattern = re.compile(r'(?i)(?:bucket[:\s]+|s3://)([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])')
        buckets = bucket_pattern.findall(question)
        entities['bucket_names'] = buckets
        
        return entities
    
    def _determine_required_data(self, services: List[str], problem_types: List[str], question: str) -> List[str]:
        required = set()
        
        for service in services:
            required.add(service)
            related = self._get_related_data_types(service)
            for r in related:
                required.add(r)
        
        if 'connectivity' in problem_types:
            required.add('vpc')
            required.add('security_group')
            if 'route53' not in required:
                required.add('route53')
        
        if 'performance' in problem_types:
            required.add('cloudwatch')
        
        if 'availability' in problem_types:
            required.add('cloudwatch')
        
        return list(required)
    
    def _get_related_data_types(self, service: str) -> List[str]:
        mapping = {
            'ec2': ['vpc', 'security_group', 'cloudwatch'],
            's3': ['cloudwatch'],
            'rds': ['vpc', 'security_group', 'cloudwatch'],
            'lambda': ['cloudwatch', 'iam'],
            'elb': ['ec2', 'vpc', 'cloudwatch'],
            'cloudfront': ['s3', 'cloudwatch'],
            'auto_scaling': ['ec2', 'cloudwatch']
        }
        return mapping.get(service, [])
    
    def _calculate_confidence(self, services: List[str], problem_types: List[str], entities: Dict) -> float:
        score = 0.0
        
        if services:
            score += 0.35
        if problem_types:
            score += 0.25
        if entities.get('instance_ids'):
            score += 0.2
        if entities.get('arns'):
            score += 0.1
        if entities.get('bucket_names'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_initial_hypotheses(self, services: List[str], problem_types: List[str], question: str) -> List[Dict]:
        hypotheses = []
        
        for service in services:
            for problem_type in problem_types:
                hypothesis = self._get_hypothesis(service, problem_type)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        if not hypotheses and services:
            hypotheses.append({
                'service': services[0],
                'problem_type': 'general',
                'description': f'{services[0].upper()} 服务存在未明确的问题',
                'priority': 'medium',
                'data_needed': [services[0]]
            })
        
        return hypotheses
    
    def _get_hypothesis(self, service: str, problem_type: str) -> Optional[Dict]:
        hypotheses = {
            ('ec2', 'connectivity'): {
                'service': 'ec2',
                'problem_type': 'connectivity',
                'description': 'EC2实例可能存在网络连接问题，可能原因：安全组配置、网络ACL、实例状态',
                'priority': 'high',
                'data_needed': ['ec2', 'security_group', 'vpc']
            },
            ('ec2', 'performance'): {
                'service': 'ec2',
                'problem_type': 'performance',
                'description': 'EC2实例可能存在性能问题，需要检查CPU、内存、网络等指标',
                'priority': 'high',
                'data_needed': ['ec2', 'cloudwatch']
            },
            ('ec2', 'availability'): {
                'service': 'ec2',
                'problem_type': 'availability',
                'description': 'EC2实例可能已停止或终止，需要检查实例状态',
                'priority': 'high',
                'data_needed': ['ec2']
            },
            ('s3', 'connectivity'): {
                'service': 's3',
                'problem_type': 'connectivity',
                'description': 'S3存储桶可能存在访问策略或权限问题',
                'priority': 'high',
                'data_needed': ['s3', 'iam']
            },
            ('s3', 'performance'): {
                'service': 's3',
                'problem_type': 'performance',
                'description': 'S3访问可能存在延迟问题，需要检查存储类型和区域配置',
                'priority': 'medium',
                'data_needed': ['s3', 'cloudwatch']
            },
            ('rds', 'connectivity'): {
                'service': 'rds',
                'problem_type': 'connectivity',
                'description': 'RDS数据库可能存在连接问题，可能原因：安全组、网络配置、实例状态',
                'priority': 'high',
                'data_needed': ['rds', 'security_group', 'vpc']
            },
            ('rds', 'performance'): {
                'service': 'rds',
                'problem_type': 'performance',
                'description': 'RDS数据库可能存在性能问题，需要检查CPU、内存、查询性能',
                'priority': 'high',
                'data_needed': ['rds', 'cloudwatch']
            },
            ('rds', 'availability'): {
                'service': 'rds',
                'problem_type': 'availability',
                'description': 'RDS实例可能不可用，需要检查实例状态',
                'priority': 'high',
                'data_needed': ['rds']
            },
            ('lambda', 'error'): {
                'service': 'lambda',
                'problem_type': 'error',
                'description': 'Lambda函数可能执行出错，需要检查函数配置和日志',
                'priority': 'high',
                'data_needed': ['lambda', 'cloudwatch']
            },
            ('lambda', 'performance'): {
                'service': 'lambda',
                'problem_type': 'performance',
                'description': 'Lambda函数可能存在性能问题，需要检查内存配置和执行时间',
                'priority': 'medium',
                'data_needed': ['lambda', 'cloudwatch']
            }
        }
        
        return hypotheses.get((service, problem_type))
    
    def _is_data_empty(self, data) -> bool:
        if data is None:
            return True
        if isinstance(data, list) and len(data) == 0:
            return True
        if isinstance(data, dict):
            if 'error' in data:
                return True
            if len(data) == 0:
                return True
        return False
    
    def _generate_collection_reasoning(self, question: str, analysis: Dict, data_to_collect: List) -> str:
        if not data_to_collect:
            return '当前收集的数据已足够进行分析'
        
        reasoning_parts = [
            f'基于问题分析，需要收集以下 {len(data_to_collect)} 类数据：',
        ]
        
        for item in data_to_collect[:5]:
            reasoning_parts.append(f'- {item["type"].upper()}: {item["reason"]}')
        
        if len(data_to_collect) > 5:
            reasoning_parts.append(f'... 还有 {len(data_to_collect) - 5} 类数据')
        
        return '\n'.join(reasoning_parts)
    
    def _analyze_resource_data(self, data_type: str, data, question: str) -> List[Dict]:
        findings = []
        
        if not isinstance(data, list):
            data = [data]
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            if data_type == 'ec2':
                state = item.get('State', '').lower()
                if state in ['stopped', 'terminated', 'stopping', 'shutting-down']:
                    findings.append({
                        'type': 'root_cause',
                        'category': 'EC2 Availability',
                        'description': f'EC2实例 {item.get("InstanceId")} 状态为 {state}，服务不可用',
                        'severity': 'high',
                        'confidence': 0.9,
                        'resource_id': item.get('InstanceId')
                    })
                
                security_groups = item.get('SecurityGroups', [])
                if not security_groups:
                    findings.append({
                        'type': 'contributing_factor',
                        'category': 'EC2 Configuration',
                        'description': f'EC2实例 {item.get("InstanceId")} 没有关联安全组',
                        'severity': 'medium',
                        'confidence': 0.7,
                        'resource_id': item.get('InstanceId')
                    })
            
            elif data_type == 'rds':
                status = item.get('DBInstanceStatus', '').lower()
                if status not in ['available', 'backing-up', 'storage-optimization', 'upgrading']:
                    findings.append({
                        'type': 'root_cause',
                        'category': 'RDS Availability',
                        'description': f'RDS实例 {item.get("DBInstanceIdentifier")} 状态为 {status}，服务不可用',
                        'severity': 'high',
                        'confidence': 0.9,
                        'resource_id': item.get('DBInstanceIdentifier')
                    })
                
                if not item.get('MultiAZ'):
                    findings.append({
                        'type': 'contributing_factor',
                        'category': 'RDS High Availability',
                        'description': f'RDS实例 {item.get("DBInstanceIdentifier")} 未启用多AZ部署，存在单点故障风险',
                        'severity': 'low',
                        'confidence': 0.5,
                        'resource_id': item.get('DBInstanceIdentifier')
                    })
            
            elif data_type == 'cloudwatch':
                state_value = item.get('StateValue', '')
                if state_value == 'ALARM':
                    findings.append({
                        'type': 'root_cause',
                        'category': 'CloudWatch Alarm',
                        'description': f'CloudWatch告警 {item.get("AlarmName")} 处于ALARM状态: {item.get("StateReason")}',
                        'severity': 'high',
                        'confidence': 0.95,
                        'resource_id': item.get('AlarmName')
                    })
        
        return findings
    
    def _generate_solutions(self, root_causes: List, contributing_factors: List, question: str) -> List[Dict]:
        solutions = []
        
        for cause in root_causes:
            solution = self._get_solution_for_cause(cause)
            if solution:
                solutions.append(solution)
        
        if not solutions:
            solutions.append({
                'title': '进一步诊断建议',
                'description': '根据当前收集的数据无法确定具体问题，请提供更多信息',
                'priority': 'medium',
                'steps': [
                    '提供具体的错误消息或日志内容',
                    '说明问题发生的时间范围',
                    '描述最近的任何配置更改',
                    '提供相关资源的标识符（实例ID、ARN等）'
                ],
                'related_issue': 'General Analysis'
            })
        
        return solutions
    
    def _get_solution_for_cause(self, cause: Dict) -> Optional[Dict]:
        category = cause.get('category', '')
        description = cause.get('description', '')
        
        if 'EC2 Availability' in category:
            state = ''
            for s in ['stopped', 'terminated', 'stopping', 'shutting-down']:
                if s in description.lower():
                    state = s
                    break
            
            if state == 'stopped':
                return {
                    'title': '启动已停止的EC2实例',
                    'description': cause['description'],
                    'priority': 'high',
                    'steps': [
                        '登录AWS管理控制台',
                        '导航到EC2服务',
                        f'找到实例 {cause.get("resource_id")}',
                        '选择实例并点击"实例状态" -> "启动实例"',
                        '等待实例状态变为"running"后测试连接'
                    ],
                    'related_issue': cause['description']
                }
            elif state in ['terminated', 'shutting-down']:
                return {
                    'title': '恢复已终止的EC2实例',
                    'description': cause['description'],
                    'priority': 'high',
                    'steps': [
                        '注意：已终止的实例无法直接恢复',
                        '检查是否有最新的AMI备份',
                        '检查是否有EBS卷快照',
                        '从备份创建新实例或从快照恢复卷',
                        '配置新实例的网络和安全设置'
                    ],
                    'related_issue': cause['description']
                }
        
        elif 'RDS Availability' in category:
            return {
                'title': '检查并恢复RDS实例',
                'description': cause['description'],
                'priority': 'high',
                'steps': [
                    '登录AWS管理控制台',
                    '导航到RDS服务',
                    f'查看实例 {cause.get("resource_id")} 的详细信息',
                    '检查事件日志了解具体原因',
                    '根据状态采取相应措施：重启、恢复、或从备份恢复'
                ],
                'related_issue': cause['description']
            }
        
        elif 'CloudWatch Alarm' in category:
            return {
                'title': '处理CloudWatch告警',
                'description': cause['description'],
                'priority': 'high',
                'steps': [
                    '登录AWS管理控制台',
                    '导航到CloudWatch服务',
                    f'查看告警 {cause.get("resource_id")} 的详情',
                    '分析告警触发的根本原因',
                    '根据告警内容调整资源配置或阈值设置'
                ],
                'related_issue': cause['description']
            }
        
        elif 'EC2 Configuration' in category:
            return {
                'title': '配置EC2安全组',
                'description': cause['description'],
                'priority': 'medium',
                'steps': [
                    '登录AWS管理控制台',
                    '导航到EC2服务',
                    f'找到实例 {cause.get("resource_id")}',
                    '查看实例的安全组配置',
                    '添加或修改安全组规则以允许必要的网络流量'
                ],
                'related_issue': cause['description']
            }
        
        return None
    
    def _calculate_overall_confidence(self, root_causes: List, collected_data: Dict) -> float:
        if not root_causes:
            return 0.3
        
        total_confidence = sum(cause.get('confidence', 0.5) for cause in root_causes)
        avg_confidence = total_confidence / len(root_causes)
        
        data_count = sum(1 for v in collected_data.values() if not self._is_data_empty(v))
        data_factor = min(data_count * 0.1, 0.2)
        
        return min(avg_confidence + data_factor, 1.0)
    
    def _generate_recommendations(self, question: str, root_causes: List) -> List[str]:
        recommendations = []
        
        if not root_causes or all(rc.get('severity') == 'low' for rc in root_causes):
            recommendations.append('建议提供更详细的问题描述，包括错误消息和发生时间')
            recommendations.append('如果可能，请提供相关资源的标识符（实例ID、ARN等）')
        
        high_severity = [rc for rc in root_causes if rc.get('severity') == 'high']
        if high_severity:
            recommendations.append(f'检测到 {len(high_severity)} 个高优先级问题，建议优先处理')
        
        return recommendations
    
    def _calculate_sufficiency_confidence(self, missing_data: List, partial_data: List, analysis: Dict) -> float:
        if missing_data:
            return 0.3
        
        if partial_data:
            return 0.6
        
        return 0.9
    
    def _generate_sufficiency_recommendations(self, missing_data: List, partial_data: List, question: str) -> List[str]:
        recommendations = []
        
        if missing_data:
            recommendations.append(f'需要补充收集以下数据: {", ".join([d["type"] for d in missing_data])}')
        
        if partial_data:
            recommendations.append(f'部分数据可能不完整: {", ".join([d["type"] for d in partial_data])}')
        
        if not missing_data and not partial_data:
            recommendations.append('当前收集的数据已足够进行完整分析')
        
        return recommendations


class OpenAIService(BaseAIService):
    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.client = None
        
        if HAS_OPENAI and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        if not self.client:
            return self._fallback_response(prompt, system_prompt)
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            return self._fallback_response(prompt, system_prompt)
    
    def _fallback_response(self, prompt: str, system_prompt: str = None) -> str:
        mock_service = MockAIService()
        
        if 'analyze_question' in (system_prompt or ''):
            result = mock_service.analyze_question(prompt)
            return json.dumps(result, ensure_ascii=False, indent=2)
        elif 'decide_data_collection' in (system_prompt or ''):
            try:
                data = json.loads(prompt)
                result = mock_service.decide_data_collection(
                    data.get('question', ''),
                    data.get('current_data', {}),
                    data.get('previous_analysis', {})
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            except:
                return json.dumps({'need_more_data': False, 'data_to_collect': []})
        elif 'perform_root_cause_analysis' in (system_prompt or ''):
            try:
                data = json.loads(prompt)
                result = mock_service.perform_root_cause_analysis(
                    data.get('question', ''),
                    data.get('collected_data', {}),
                    data.get('analysis_history', [])
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            except:
                return json.dumps({'root_causes': [], 'solutions': []})
        elif 'check_data_sufficiency' in (system_prompt or ''):
            try:
                data = json.loads(prompt)
                result = mock_service.check_data_sufficiency(
                    data.get('question', ''),
                    data.get('collected_data', {}),
                    data.get('analysis_history', [])
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            except:
                return json.dumps({'is_sufficient': True, 'missing_data': []})
        
        return json.dumps({'status': 'fallback'})
    
    def analyze_question(self, question: str, context: Dict = None) -> Dict[str, Any]:
        system_prompt = """
你是一个专业的AWS云架构师和运维专家。你的任务是分析用户的问题，识别相关的AWS服务和问题类型。

请以JSON格式返回分析结果，包含以下字段：
- original_question: 原始问题
- relevant_services: 相关的AWS服务列表（如: ec2, s3, rds, lambda, vpc, cloudwatch等）
- problem_types: 问题类型列表（如: connectivity, performance, error, availability, cost, security）
- entities: 提取的实体对象，包含:
  - instance_ids: EC2实例ID列表
  - arns: ARN列表
  - bucket_names: S3存储桶名称列表
- required_data_types: 需要收集的数据类型列表
- analysis_confidence: 分析置信度（0-1之间的浮点数）
- initial_hypotheses: 初始假设列表，每个假设包含:
  - service: 相关服务
  - problem_type: 问题类型
  - description: 假设描述
  - priority: 优先级（high, medium, low）
  - data_needed: 需要的数据列表

只返回JSON，不要其他内容。
"""
        
        prompt = f"""
用户问题: {question}

请分析这个问题，识别相关的AWS服务和问题类型。
"""
        
        response = self._call_llm(prompt, system_prompt)
        
        try:
            return json.loads(response)
        except:
            mock = MockAIService()
            return mock.analyze_question(question, context)
    
    def decide_data_collection(self, question: str, current_data: Dict,
                                previous_analysis: Dict = None) -> Dict[str, Any]:
        system_prompt = """
你是一个专业的AWS运维专家。基于用户的问题和已收集的数据，判断是否需要收集更多数据。

请以JSON格式返回结果，包含以下字段：
- need_more_data: 布尔值，是否需要更多数据
- data_to_collect: 需要收集的数据列表，每个项包含:
  - type: 数据类型（如: ec2, s3, rds, cloudwatch, vpc, security_group等）
  - priority: 优先级（high, medium, low）
  - reason: 收集原因
- reasoning: 决策推理过程的文字描述

只返回JSON，不要其他内容。
"""
        
        data_summary = json.dumps(current_data, ensure_ascii=False, default=str)
        analysis_summary = json.dumps(previous_analysis or {}, ensure_ascii=False, default=str)
        
        prompt = f"""
用户问题: {question}

已收集的数据:
{data_summary}

之前的分析:
{analysis_summary}

请判断是否需要收集更多数据，如果需要，请说明需要收集哪些数据。
"""
        
        response = self._call_llm(prompt, system_prompt)
        
        try:
            return json.loads(response)
        except:
            mock = MockAIService()
            return mock.decide_data_collection(question, current_data, previous_analysis)
    
    def perform_root_cause_analysis(self, question: str, collected_data: Dict,
                                     analysis_history: List = None) -> Dict[str, Any]:
        system_prompt = """
你是一个资深的AWS云架构师和问题诊断专家。基于用户的问题和收集到的AWS资源数据，进行根因分析。

请以JSON格式返回分析结果，包含以下字段：
- root_causes: 根本原因列表，每个原因包含:
  - type: 类型（root_cause）
  - category: 问题类别（如: EC2 Availability, RDS Performance等）
  - description: 详细描述
  - severity: 严重程度（high, medium, low）
  - confidence: 置信度（0-1之间的浮点数）
  - resource_id: 相关资源标识符（可选）
- contributing_factors: 促成因素列表，每个因素包含:
  - type: 类型（contributing_factor）
  - category: 类别
  - description: 详细描述
  - severity: 严重程度
  - confidence: 置信度
  - resource_id: 相关资源标识符（可选）
- analysis_steps: 分析步骤列表，每个步骤包含:
  - step: 步骤编号
  - action: 操作描述
  - description: 详细说明
- solutions: 解决方案列表，每个方案包含:
  - title: 方案标题
  - description: 方案描述
  - priority: 优先级
  - steps: 操作步骤列表
  - related_issue: 关联的问题描述
- overall_confidence: 总体置信度（0-1之间的浮点数）
- recommendations: 额外建议列表（字符串数组）

只返回JSON，不要其他内容。
"""
        
        data_json = json.dumps(collected_data, ensure_ascii=False, default=str)
        
        prompt = f"""
用户问题: {question}

收集到的AWS资源数据:
{data_json}

请进行详细的根因分析，找出问题的根本原因，并提供解决方案。
"""
        
        response = self._call_llm(prompt, system_prompt)
        
        try:
            return json.loads(response)
        except:
            mock = MockAIService()
            return mock.perform_root_cause_analysis(question, collected_data, analysis_history)
    
    def check_data_sufficiency(self, question: str, collected_data: Dict,
                                analysis_history: List = None) -> Dict[str, Any]:
        system_prompt = """
你是一个专业的AWS问题诊断专家。判断当前收集的数据是否足以进行完整的根因分析。

请以JSON格式返回结果，包含以下字段：
- is_sufficient: 布尔值，数据是否充足
- missing_data: 缺失的数据列表，每个项包含:
  - type: 数据类型
  - reason: 缺失原因
- partial_data: 部分数据列表，每个项包含:
  - type: 数据类型
  - reason: 说明
- sufficient_data: 充足的数据列表
- confidence_score: 数据充足性置信度（0-1之间的浮点数）
- recommended_next_steps: 建议的下一步操作列表（字符串数组）

只返回JSON，不要其他内容。
"""
        
        data_json = json.dumps(collected_data, ensure_ascii=False, default=str)
        
        prompt = f"""
用户问题: {question}

已收集的数据:
{data_json}

请判断这些数据是否足以进行完整的根因分析。
"""
        
        response = self._call_llm(prompt, system_prompt)
        
        try:
            return json.loads(response)
        except:
            mock = MockAIService()
            return mock.check_data_sufficiency(question, collected_data, analysis_history)


class AIServiceFactory:
    @staticmethod
    def create_service(service_type: str = 'mock', **kwargs) -> BaseAIService:
        if service_type == 'openai':
            return OpenAIService(**kwargs)
        elif service_type == 'anthropic' and HAS_ANTHROPIC:
            from anthropic import Anthropic
            class AnthropicService(BaseAIService):
                def __init__(self, api_key=None, model="claude-3-opus-20240229"):
                    self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
                    self.model = model
                    self.client = Anthropic(api_key=self.api_key) if self.api_key else None
                
                def analyze_question(self, question, context=None):
                    mock = MockAIService()
                    return mock.analyze_question(question, context)
                
                def decide_data_collection(self, question, current_data, previous_analysis=None):
                    mock = MockAIService()
                    return mock.decide_data_collection(question, current_data, previous_analysis)
                
                def perform_root_cause_analysis(self, question, collected_data, analysis_history=None):
                    mock = MockAIService()
                    return mock.perform_root_cause_analysis(question, collected_data, analysis_history)
                
                def check_data_sufficiency(self, question, collected_data, analysis_history=None):
                    mock = MockAIService()
                    return mock.check_data_sufficiency(question, collected_data, analysis_history)
            
            return AnthropicService(**kwargs)
        else:
            return MockAIService()


def get_ai_service() -> BaseAIService:
    service_type = os.environ.get('AI_SERVICE_TYPE', 'mock')
    
    if service_type == 'openai' and os.environ.get('OPENAI_API_KEY'):
        return AIServiceFactory.create_service('openai')
    elif service_type == 'anthropic' and os.environ.get('ANTHROPIC_API_KEY'):
        return AIServiceFactory.create_service('anthropic')
    else:
        return AIServiceFactory.create_service('mock')
