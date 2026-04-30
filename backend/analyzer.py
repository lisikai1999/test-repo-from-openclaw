from typing import Dict, List, Any
from ai_service import get_ai_service, BaseAIService

class NLAnalyzer:
    def __init__(self, ai_service: BaseAIService = None):
        self.ai_service = ai_service or get_ai_service()
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        return self.ai_service.analyze_question(question)
    
    def decide_data_collection(self, question: str, current_data: Dict,
                                previous_analysis: Dict = None) -> Dict[str, Any]:
        return self.ai_service.decide_data_collection(question, current_data, previous_analysis)
    
    def perform_root_cause_analysis(self, question: str, collected_data: Dict,
                                     analysis_history: List = None) -> Dict[str, Any]:
        return self.ai_service.perform_root_cause_analysis(question, collected_data, analysis_history)
    
    def check_data_sufficiency(self, question: str, collected_data: Dict,
                                analysis_history: List = None) -> Dict[str, Any]:
        return self.ai_service.check_data_sufficiency(question, collected_data, analysis_history)
    
    def generate_follow_up_questions(self, analysis_result: Dict[str, Any]) -> List[str]:
        follow_ups = []
        
        relevant_services = analysis_result.get('relevant_services', [])
        if not relevant_services:
            follow_ups.append("请问您想了解哪个AWS服务的问题？例如EC2、S3、RDS等")
        
        problem_types = analysis_result.get('problem_types', [])
        if not problem_types:
            follow_ups.append("您遇到的具体问题是什么？例如连接问题、性能问题、错误等")
        
        entities = analysis_result.get('entities', {})
        if not entities.get('instance_ids') and 'ec2' in relevant_services:
            follow_ups.append("如果您知道具体的EC2实例ID，请提供它以帮助更精确的分析")
        
        if not entities.get('bucket_names') and 's3' in relevant_services:
            follow_ups.append("如果您知道具体的S3存储桶名称，请提供它以帮助更精确的分析")
        
        confidence = analysis_result.get('analysis_confidence', 0)
        if confidence < 0.5:
            follow_ups.append("能否提供更多关于问题的细节？例如错误消息、时间范围或最近的更改")
        
        initial_hypotheses = analysis_result.get('initial_hypotheses', [])
        for hypothesis in initial_hypotheses[:3]:
            follow_ups.append(f"初步假设: {hypothesis.get('description', 'N/A')}")
        
        return follow_ups
