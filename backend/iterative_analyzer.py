from typing import Dict, List, Any
import json
from datetime import datetime

class IterativeAnalyzer:
    def __init__(self, aws_collector, nl_analyzer):
        self.aws_collector = aws_collector
        self.nl_analyzer = nl_analyzer
        self.max_iterations = 5
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        analysis_history = []
        collected_data = {}
        iteration = 0
        
        initial_analysis = self.nl_analyzer.analyze_question(question)
        analysis_history.append({
            'iteration': 0,
            'type': 'initial_analysis',
            'timestamp': datetime.now().isoformat(),
            'analysis': initial_analysis
        })
        
        while iteration < self.max_iterations:
            iteration += 1
            
            required_resources = self._determine_required_resources(initial_analysis, collected_data)
            
            if required_resources:
                collection_result = self._collect_resources(required_resources, collected_data)
                collected_data.update(collection_result['new_data'])
                
                analysis_history.append({
                    'iteration': iteration,
                    'type': 'data_collection',
                    'timestamp': datetime.now().isoformat(),
                    'resources_collected': list(collection_result['new_data'].keys()),
                    'errors': collection_result.get('errors', [])
                })
            
            sufficiency_check = self.nl_analyzer.check_data_sufficiency(collected_data, initial_analysis)
            
            analysis_history.append({
                'iteration': iteration,
                'type': 'sufficiency_check',
                'timestamp': datetime.now().isoformat(),
                'sufficient': sufficiency_check['sufficient'],
                'missing_data': sufficiency_check['missing_data']
            })
            
            if sufficiency_check['sufficient'] or not sufficiency_check['missing_data']:
                break
            
            if iteration >= self.max_iterations:
                break
        
        final_analysis = self._perform_root_cause_analysis(
            question, initial_analysis, collected_data, analysis_history
        )
        
        return {
            'question': question,
            'timestamp': datetime.now().isoformat(),
            'iterations_completed': iteration,
            'analysis_history': analysis_history,
            'collected_data_summary': self._summarize_collected_data(collected_data),
            'root_cause_analysis': final_analysis['root_cause'],
            'analysis_process': final_analysis['process'],
            'solutions': final_analysis['solutions'],
            'confidence': final_analysis['confidence'],
            'follow_up_questions': self.nl_analyzer.generate_follow_up_questions(initial_analysis)
        }
    
    def _determine_required_resources(self, initial_analysis: Dict, collected_data: Dict) -> List[Dict]:
        required = []
        
        for resource in initial_analysis.get('required_resources', []):
            resource_type = resource['type']
            if resource_type not in collected_data:
                required.append(resource)
        
        return required
    
    def _collect_resources(self, required_resources: List[Dict], existing_data: Dict) -> Dict[str, Any]:
        new_data = {}
        errors = []
        
        for resource in required_resources:
            resource_type = resource['type']
            
            try:
                data = self.aws_collector.get_resource_by_type(resource_type)
                new_data[resource_type] = data
                
                if isinstance(data, dict) and 'error' in data:
                    errors.append({
                        'resource_type': resource_type,
                        'error': data['error']
                    })
            except Exception as e:
                errors.append({
                    'resource_type': resource_type,
                    'error': str(e)
                })
                new_data[resource_type] = {'error': str(e)}
        
        return {
            'new_data': new_data,
            'errors': errors
        }
    
    def _perform_root_cause_analysis(self, question: str, initial_analysis: Dict, 
                                     collected_data: Dict, history: List) -> Dict[str, Any]:
        root_cause = {
            'identified': False,
            'categories': [],
            'specific_issues': [],
            'confidence_factors': []
        }
        
        analysis_process = self._build_analysis_process(question, initial_analysis, collected_data, history)
        solutions = []
        
        services = initial_analysis.get('relevant_services', [])
        problem_types = initial_analysis.get('problem_type', [])
        
        if 'ec2' in services:
            ec2_data = collected_data.get('ec2', [])
            if ec2_data and not isinstance(ec2_data, dict):
                for instance in ec2_data:
                    state = instance.get('State', '').lower()
                    
                    if state in ['stopped', 'terminated', 'stopping']:
                        root_cause['identified'] = True
                        root_cause['categories'].append('Instance Availability')
                        root_cause['specific_issues'].append(
                            f"EC2实例 {instance.get('InstanceId')} 状态为 {state}"
                        )
                        root_cause['confidence_factors'].append('实例状态检查')
                        
                        solutions.append({
                            'priority': 'high',
                            'action': f'启动EC2实例 {instance.get("InstanceId")}',
                            'description': f'该实例当前状态为 {state}，需要启动以恢复服务',
                            'steps': [
                                '登录AWS控制台',
                                f'导航到EC2服务，找到实例 {instance.get("InstanceId")}',
                                '选择实例并点击"启动实例"'
                            ]
                        })
                    
                    security_groups = instance.get('SecurityGroups', [])
                    sg_data = collected_data.get('security_group', [])
                    
                    if sg_data and not isinstance(sg_data, dict):
                        for sg_id in security_groups:
                            for sg in sg_data:
                                if sg.get('GroupId') == sg_id:
                                    ingress_rules = sg.get('IpPermissions', [])
                                    
                                    has_ssh = any(r.get('FromPort') == 22 for r in ingress_rules if r.get('FromPort'))
                                    has_http = any(r.get('FromPort') == 80 for r in ingress_rules if r.get('FromPort'))
                                    has_https = any(r.get('FromPort') == 443 for r in ingress_rules if r.get('FromPort'))
                                    
                                    if 'connectivity' in problem_types:
                                        if not has_ssh and not has_http and not has_https:
                                            root_cause['identified'] = True
                                            root_cause['categories'].append('Security Group Configuration')
                                            root_cause['specific_issues'].append(
                                                f"安全组 {sg_id} 没有开放常用端口（SSH/HTTP/HTTPS）"
                                            )
                                            root_cause['confidence_factors'].append('安全组规则检查')
                                            
                                            solutions.append({
                                                'priority': 'high',
                                                'action': f'更新安全组 {sg_id} 的入站规则',
                                                'description': '当前安全组没有开放必要的入站端口',
                                                'steps': [
                                                    '登录AWS控制台',
                                                    f'导航到VPC服务，找到安全组 {sg_id}',
                                                    '添加入站规则，开放必要的端口（如SSH 22, HTTP 80, HTTPS 443）',
                                                    '保存规则更改'
                                                ]
                                            })
        
        if 's3' in services:
            s3_data = collected_data.get('s3', [])
            if s3_data and not isinstance(s3_data, dict):
                root_cause['categories'].append('S3 Configuration')
                root_cause['specific_issues'].append(
                    f"检测到 {len(s3_data)} 个S3存储桶"
                )
                
                solutions.append({
                    'priority': 'medium',
                    'action': '检查S3存储桶配置',
                    'description': '根据具体问题检查存储桶策略、权限或配置',
                    'steps': [
                        '登录AWS控制台',
                        '导航到S3服务',
                        '检查相关存储桶的策略、权限和配置'
                    ]
                })
        
        if 'rds' in services:
            rds_data = collected_data.get('rds', [])
            if rds_data and not isinstance(rds_data, dict):
                for db in rds_data:
                    status = db.get('DBInstanceStatus', '').lower()
                    
                    if status not in ['available', 'backing-up', 'storage-optimization']:
                        root_cause['identified'] = True
                        root_cause['categories'].append('RDS Availability')
                        root_cause['specific_issues'].append(
                            f"RDS实例 {db.get('DBInstanceIdentifier')} 状态为 {status}"
                        )
                        root_cause['confidence_factors'].append('RDS状态检查')
                        
                        solutions.append({
                            'priority': 'high',
                            'action': f'检查RDS实例 {db.get("DBInstanceIdentifier")}',
                            'description': f'RDS实例当前状态为 {status}，需要检查',
                            'steps': [
                                '登录AWS控制台',
                                f'导航到RDS服务，找到实例 {db.get("DBInstanceIdentifier")}',
                                '检查实例状态和事件日志',
                                '根据具体状态采取相应措施'
                            ]
                        })
        
        if 'lambda' in services:
            lambda_data = collected_data.get('lambda', [])
            if lambda_data and not isinstance(lambda_data, dict):
                root_cause['categories'].append('Lambda Configuration')
                root_cause['specific_issues'].append(
                    f"检测到 {len(lambda_data)} 个Lambda函数"
                )
                
                solutions.append({
                    'priority': 'medium',
                    'action': '检查Lambda函数配置和日志',
                    'description': '检查Lambda函数的配置、权限和CloudWatch日志',
                    'steps': [
                        '登录AWS控制台',
                        '导航到Lambda服务',
                        '检查相关函数的配置和权限',
                        '查看CloudWatch日志中的错误信息'
                    ]
                })
        
        cloudwatch_data = collected_data.get('cloudwatch', [])
        if cloudwatch_data and not isinstance(cloudwatch_data, dict):
            alarms_in_alarm = [a for a in cloudwatch_data if a.get('StateValue') == 'ALARM']
            if alarms_in_alarm:
                root_cause['identified'] = True
                root_cause['categories'].append('CloudWatch Alarms')
                for alarm in alarms_in_alarm:
                    root_cause['specific_issues'].append(
                        f"CloudWatch告警 {alarm.get('AlarmName')} 处于ALARM状态: {alarm.get('StateReason')}"
                    )
                root_cause['confidence_factors'].append('CloudWatch告警检查')
                
                solutions.append({
                    'priority': 'high',
                    'action': '处理活跃的CloudWatch告警',
                    'description': '有CloudWatch告警处于触发状态，需要调查',
                    'steps': [
                        '登录AWS控制台',
                        '导航到CloudWatch服务',
                        '查看活跃的告警详情',
                        '根据告警内容采取相应措施'
                    ]
                })
        
        if not root_cause['identified']:
            root_cause['categories'].append('General Analysis')
            root_cause['specific_issues'].append(
                '未发现明显的配置问题或资源状态异常'
            )
            
            solutions.append({
                'priority': 'low',
                'action': '提供更多信息以进行深入分析',
                'description': '当前收集的数据不足以确定具体问题',
                'steps': [
                    '提供具体的错误消息或日志',
                    '说明问题发生的时间范围',
                    '描述最近的任何配置更改',
                    '提供相关的资源标识符（如实例ID、存储桶名称等）'
                ]
            })
        
        confidence = self._calculate_final_confidence(root_cause, collected_data, initial_analysis)
        
        return {
            'root_cause': root_cause,
            'process': analysis_process,
            'solutions': solutions,
            'confidence': confidence
        }
    
    def _build_analysis_process(self, question: str, initial_analysis: Dict, 
                                collected_data: Dict, history: List) -> List[Dict]:
        process = []
        
        process.append({
            'step': 1,
            'action': '问题解析',
            'description': f'解析用户问题: "{question}"',
            'details': {
                '识别的服务': initial_analysis.get('relevant_services', []),
                '识别的问题类型': initial_analysis.get('problem_type', []),
                '提取的实体': initial_analysis.get('entities', {})
            }
        })
        
        process.append({
            'step': 2,
            'action': '数据收集',
            'description': '根据分析结果收集相关AWS资源信息',
            'details': {
                '收集的资源类型': list(collected_data.keys()),
                '收集的数据摘要': self._summarize_collected_data(collected_data)
            }
        })
        
        process.append({
            'step': 3,
            'action': '数据分析',
            'description': '分析收集的数据以识别潜在问题',
            'details': {
                '检查的配置项': [
                    'EC2实例状态',
                    '安全组规则',
                    'RDS实例状态',
                    'CloudWatch告警',
                    'Lambda函数配置'
                ]
            }
        })
        
        process.append({
            'step': 4,
            'action': '根因识别',
            'description': '基于分析结果确定问题的根本原因',
            'details': '见根因分析部分'
        })
        
        process.append({
            'step': 5,
            'action': '解决方案生成',
            'description': '根据识别的问题生成解决方案',
            'details': '见解决方案部分'
        })
        
        return process
    
    def _summarize_collected_data(self, collected_data: Dict) -> Dict[str, Any]:
        summary = {}
        
        for resource_type, data in collected_data.items():
            if isinstance(data, dict) and 'error' in data:
                summary[resource_type] = {'error': data['error']}
            elif isinstance(data, list):
                summary[resource_type] = {
                    'count': len(data),
                    'sample': data[:3] if len(data) > 3 else data
                }
            else:
                summary[resource_type] = data
        
        return summary
    
    def _calculate_final_confidence(self, root_cause: Dict, collected_data: Dict, 
                                     initial_analysis: Dict) -> float:
        score = 0.0
        
        if root_cause['identified']:
            score += 0.4
        if root_cause['categories']:
            score += 0.2
        if root_cause['specific_issues']:
            score += 0.2
        
        data_available = any(
            not (isinstance(v, dict) and 'error' in v) 
            for v in collected_data.values()
        )
        if data_available:
            score += 0.2
        
        return min(score, 1.0)
