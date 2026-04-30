import re
from typing import Dict, List, Any

class NLAnalyzer:
    def __init__(self):
        self.aws_service_keywords = {
            'ec2': ['ec2', 'virtual machine', 'vm', 'instance', 'server', 'compute', 'virtual machine'],
            's3': ['s3', 'bucket', 'storage', 'object storage', 'simple storage service'],
            'rds': ['rds', 'database', 'db', 'mysql', 'postgres', 'aurora', 'sql server', 'mariadb', 'oracle'],
            'lambda': ['lambda', 'serverless', 'function', 'faas', 'function as a service'],
            'cloudwatch': ['cloudwatch', 'monitoring', 'metrics', 'alarms', 'logs'],
            'vpc': ['vpc', 'network', 'subnet', 'security group', 'route table', 'networking'],
            'route53': ['route53', 'dns', 'domain', 'hosted zone', 'record'],
            'elb': ['elb', 'load balancer', 'alb', 'nlb', 'classic load balancer', 'application load balancer'],
            'cloudfront': ['cloudfront', 'cdn', 'content delivery', 'edge'],
            'iam': ['iam', 'identity', 'permission', 'role', 'policy', 'access'],
            'cloudformation': ['cloudformation', 'cfn', 'stack', 'template', 'infrastructure as code'],
            'auto_scaling': ['autoscaling', 'auto scaling', 'asg', 'auto scaling group']
        }
        
        self.problem_keywords = {
            'connectivity': ['cannot connect', 'unable to connect', 'connection failed', 'timeout', 'network issue', 
                            "can't reach", 'not reachable', 'connection refused', 'no connection'],
            'performance': ['slow', 'performance', 'high latency', 'slow response', 'high cpu', 'high memory',
                           'lag', 'slow down', 'bottleneck', 'throughput'],
            'error': ['error', 'failed', 'exception', 'issue', 'problem', 'not working', 'broken',
                     'crash', 'crashed', 'failure'],
            'cost': ['cost', 'bill', 'expense', 'price', 'too expensive', 'high cost'],
            'security': ['security', 'vulnerable', 'hack', 'attack', 'breach', 'unauthorized',
                        'permission', 'access denied', 'forbidden'],
            'availability': ['down', 'offline', 'unavailable', 'not running', 'stopped',
                            'high availability', 'downtime', 'outage']
        }
        
        self.instance_id_pattern = re.compile(r'i-[0-9a-f]{17}')
        self.bucket_name_pattern = re.compile(r'^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')
        self.arn_pattern = re.compile(r'arn:aws:[\w-]+:[a-z0-9-]*:\d{12}:[\w/:-]+')
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        question_lower = question.lower()
        
        relevant_services = self._identify_services(question_lower)
        problem_type = self._identify_problem_type(question_lower)
        entities = self._extract_entities(question)
        
        required_resources = self._determine_required_resources(relevant_services, problem_type)
        
        return {
            'original_question': question,
            'relevant_services': relevant_services,
            'problem_type': problem_type,
            'entities': entities,
            'required_resources': required_resources,
            'confidence': self._calculate_confidence(relevant_services, problem_type, entities)
        }
    
    def _identify_services(self, question_lower: str) -> List[str]:
        services = set()
        
        for service, keywords in self.aws_service_keywords.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    services.add(service)
                    break
        
        return list(services)
    
    def _identify_problem_type(self, question_lower: str) -> List[str]:
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
            'bucket_names': []
        }
        
        instance_ids = self.instance_id_pattern.findall(question)
        entities['instance_ids'] = instance_ids
        
        arns = self.arn_pattern.findall(question)
        entities['arns'] = arns
        
        potential_buckets = self.bucket_name_pattern.findall(question)
        if potential_buckets:
            entities['bucket_names'] = [b for b in potential_buckets if ' ' not in b]
        
        return entities
    
    def _determine_required_resources(self, services: List[str], problem_types: List[str]) -> List[Dict[str, Any]]:
        required = []
        
        base_resources = {
            'ec2': ['ec2', 'security_group', 'vpc'],
            's3': ['s3'],
            'rds': ['rds', 'security_group', 'vpc'],
            'lambda': ['lambda', 'cloudwatch'],
            'cloudwatch': ['cloudwatch'],
            'vpc': ['vpc', 'security_group'],
            'route53': ['route53'],
            'elb': ['ec2', 'vpc'],
            'cloudfront': ['s3', 'cloudwatch'],
            'iam': ['iam'],
            'cloudformation': ['cloudformation'],
            'auto_scaling': ['ec2', 'cloudwatch']
        }
        
        for service in services:
            if service in base_resources:
                for resource in base_resources[service]:
                    if not any(r['type'] == resource for r in required):
                        required.append({
                            'type': resource,
                            'priority': 'high' if resource in services else 'medium',
                            'reason': f'Related to {service} analysis'
                        })
        
        if 'connectivity' in problem_types:
            for resource in ['vpc', 'security_group']:
                if not any(r['type'] == resource for r in required):
                    required.append({
                        'type': resource,
                        'priority': 'high',
                        'reason': 'Connectivity analysis requires network configuration'
                    })
        
        if 'performance' in problem_types:
            if not any(r['type'] == 'cloudwatch' for r in required):
                required.append({
                    'type': 'cloudwatch',
                    'priority': 'high',
                    'reason': 'Performance analysis requires metrics data'
                })
        
        if 'availability' in problem_types:
            if not any(r['type'] == 'cloudwatch' for r in required):
                required.append({
                    'type': 'cloudwatch',
                    'priority': 'high',
                    'reason': 'Availability analysis requires alarms and metrics'
                })
        
        return required
    
    def _calculate_confidence(self, services: List[str], problem_types: List[str], entities: Dict) -> float:
        score = 0.0
        
        if services:
            score += 0.4
        if problem_types:
            score += 0.3
        if entities['instance_ids'] or entities['arns'] or entities['bucket_names']:
            score += 0.3
        
        return min(score, 1.0)
    
    def generate_follow_up_questions(self, analysis_result: Dict[str, Any]) -> List[str]:
        follow_ups = []
        
        if not analysis_result['relevant_services']:
            follow_ups.append("请问您想了解哪个AWS服务的问题？例如EC2、S3、RDS等")
        
        if not analysis_result['problem_type']:
            follow_ups.append("您遇到的具体问题是什么？例如连接问题、性能问题、错误等")
        
        if not analysis_result['entities']['instance_ids'] and 'ec2' in analysis_result['relevant_services']:
            follow_ups.append("如果您知道具体的实例ID，请提供它以帮助更精确的分析")
        
        if analysis_result['confidence'] < 0.5:
            follow_ups.append("能否提供更多关于问题的细节？例如错误消息、时间范围或最近的更改")
        
        return follow_ups
    
    def check_data_sufficiency(self, collected_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        missing_data = []
        sufficient = True
        
        required_resources = analysis_result.get('required_resources', [])
        
        for resource in required_resources:
            resource_type = resource['type']
            
            if resource_type not in collected_data or not collected_data[resource_type]:
                sufficient = False
                missing_data.append({
                    'type': resource_type,
                    'priority': resource['priority'],
                    'reason': resource['reason']
                })
            elif isinstance(collected_data[resource_type], dict) and 'error' in collected_data[resource_type]:
                sufficient = False
                missing_data.append({
                    'type': resource_type,
                    'priority': resource['priority'],
                    'reason': f'Failed to collect {resource_type} data: {collected_data[resource_type]["error"]}'
                })
        
        return {
            'sufficient': sufficient,
            'missing_data': missing_data,
            'confidence': 0.8 if sufficient else 0.3
        }
