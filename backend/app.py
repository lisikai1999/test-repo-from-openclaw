from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from aws_collector import AWSCollector
from analyzer import NLAnalyzer
from iterative_analyzer import IterativeAnalyzer

app = Flask(__name__)
CORS(app)

aws_collector = AWSCollector()
nl_analyzer = NLAnalyzer()
iterative_analyzer = IterativeAnalyzer(aws_collector, nl_analyzer)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    result = iterative_analyzer.analyze_question(question)
    
    return jsonify(result)

@app.route('/api/aws/resources', methods=['GET'])
def list_aws_resources():
    resource_type = request.args.get('type', 'all')
    
    try:
        if resource_type == 'all':
            resources = aws_collector.get_all_resources()
        elif resource_type == 'ec2':
            resources = aws_collector.get_ec2_instances()
        elif resource_type == 's3':
            resources = aws_collector.get_s3_buckets()
        elif resource_type == 'rds':
            resources = aws_collector.get_rds_instances()
        elif resource_type == 'lambda':
            resources = aws_collector.get_lambda_functions()
        else:
            return jsonify({'error': 'Unsupported resource type'}), 400
        
        return jsonify({'resources': resources})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
