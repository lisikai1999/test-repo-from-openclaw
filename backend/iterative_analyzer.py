from typing import Dict, List, Any
from datetime import datetime
import json
from aws_collector import AWSCollector
from analyzer import NLAnalyzer

class IterativeAnalyzer:
    def __init__(self, aws_collector: AWSCollector, nl_analyzer: NLAnalyzer):
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
            'type': 'ai_initial_analysis',
            'timestamp': datetime.now().isoformat(),
            'analysis': initial_analysis,
            'description': 'AI分析用户问题，识别相关服务和问题类型'
        })
        
        while iteration < self.max_iterations:
            iteration += 1
            
            collection_decision = self.nl_analyzer.decide_data_collection(
                question, collected_data, initial_analysis
            )
            
            analysis_history.append({
                'iteration': iteration,
                'type': 'ai_collection_decision',
                'timestamp': datetime.now().isoformat(),
                'decision': collection_decision,
                'description': 'AI决定是否需要采集更多数据'
            })
            
            if not collection_decision.get('need_more_data') or not collection_decision.get('data_to_collect'):
                sufficiency_check = self.nl_analyzer.check_data_sufficiency(
                    question, collected_data, analysis_history
                )
                
                analysis_history.append({
                    'iteration': iteration,
                    'type': 'ai_sufficiency_check',
                    'timestamp': datetime.now().isoformat(),
                    'check': sufficiency_check,
                    'description': 'AI检查数据是否足够进行分析'
                })
                
                if sufficiency_check.get('is_sufficient'):
                    break
                else:
                    missing = sufficiency_check.get('missing_data', [])
                    if missing:
                        collection_decision['need_more_data'] = True
                        collection_decision['data_to_collect'] = [
                            {'type': item['type'], 'priority': 'high', 'reason': item['reason']}
                            for item in missing
                        ]
                    else:
                        break
            
            if collection_decision.get('need_more_data'):
                collection_result = self._collect_resources_ai(
                    collection_decision.get('data_to_collect', []),
                    collected_data
                )
                
                collected_data.update(collection_result['new_data'])
                
                analysis_history.append({
                    'iteration': iteration,
                    'type': 'data_collection',
                    'timestamp': datetime.now().isoformat(),
                    'resources_collected': list(collection_result['new_data'].keys()),
                    'errors': collection_result.get('errors', []),
                    'description': '采集AWS资源数据'
                })
            
            sufficiency_check = self.nl_analyzer.check_data_sufficiency(
                question, collected_data, analysis_history
            )
            
            analysis_history.append({
                'iteration': iteration,
                'type': 'ai_sufficiency_check',
                'timestamp': datetime.now().isoformat(),
                'check': sufficiency_check,
                'description': 'AI检查数据充足性'
            })
            
            if sufficiency_check.get('is_sufficient'):
                break
            
            if iteration >= self.max_iterations:
                analysis_history.append({
                    'iteration': iteration,
                    'type': 'max_iterations_reached',
                    'timestamp': datetime.now().isoformat(),
                    'description': f'达到最大迭代次数({self.max_iterations})，停止数据采集'
                })
                break
        
        analysis_history.append({
            'iteration': iteration + 1,
            'type': 'ai_root_cause_analysis',
            'timestamp': datetime.now().isoformat(),
            'description': 'AI进行根因分析'
        })
        
        root_cause_analysis = self.nl_analyzer.perform_root_cause_analysis(
            question, collected_data, analysis_history
        )
        
        return {
            'question': question,
            'timestamp': datetime.now().isoformat(),
            'iterations_completed': iteration,
            'max_iterations': self.max_iterations,
            'analysis_history': analysis_history,
            'initial_analysis': initial_analysis,
            'collected_data': collected_data,
            'collected_data_summary': self._summarize_collected_data(collected_data),
            'root_cause_analysis': {
                'root_causes': root_cause_analysis.get('root_causes', []),
                'contributing_factors': root_cause_analysis.get('contributing_factors', []),
                'overall_confidence': root_cause_analysis.get('overall_confidence', 0),
                'recommendations': root_cause_analysis.get('recommendations', [])
            },
            'analysis_process': root_cause_analysis.get('analysis_steps', []),
            'solutions': root_cause_analysis.get('solutions', []),
            'confidence': root_cause_analysis.get('overall_confidence', 0),
            'follow_up_questions': self.nl_analyzer.generate_follow_up_questions(initial_analysis),
            'ai_driven': True
        }
    
    def _collect_resources_ai(self, data_to_collect: List[Dict], existing_data: Dict) -> Dict[str, Any]:
        new_data = {}
        errors = []
        
        for resource in data_to_collect:
            resource_type = resource.get('type')
            priority = resource.get('priority', 'medium')
            
            if resource_type in existing_data:
                continue
            
            try:
                data = self.aws_collector.get_resource_by_type(resource_type)
                new_data[resource_type] = data
                
                if isinstance(data, dict) and 'error' in data:
                    errors.append({
                        'resource_type': resource_type,
                        'priority': priority,
                        'error': data['error']
                    })
            except Exception as e:
                errors.append({
                    'resource_type': resource_type,
                    'priority': priority,
                    'error': str(e)
                })
                new_data[resource_type] = {'error': str(e)}
        
        return {
            'new_data': new_data,
            'errors': errors
        }
    
    def _summarize_collected_data(self, collected_data: Dict) -> Dict[str, Any]:
        summary = {}
        
        for resource_type, data in collected_data.items():
            if isinstance(data, dict) and 'error' in data:
                summary[resource_type] = {
                    'status': 'error',
                    'error': data['error']
                }
            elif isinstance(data, list):
                summary[resource_type] = {
                    'status': 'success',
                    'count': len(data),
                    'sample': data[:2] if len(data) > 2 else data
                }
            else:
                summary[resource_type] = {
                    'status': 'success',
                    'data': data
                }
        
        return summary
