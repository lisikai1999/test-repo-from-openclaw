import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

class AWSCollector:
    def __init__(self):
        self.session = boto3.Session()
    
    def get_ec2_instances(self):
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance.get('InstanceId'),
                        'InstanceType': instance.get('InstanceType'),
                        'State': instance.get('State', {}).get('Name'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'LaunchTime': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                        'Tags': self._extract_tags(instance.get('Tags', [])),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId'),
                        'SecurityGroups': [sg.get('GroupId') for sg in instance.get('SecurityGroups', [])]
                    })
            
            return instances
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_s3_buckets(self):
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            buckets = []
            
            for bucket in response['Buckets']:
                bucket_info = {
                    'Name': bucket.get('Name'),
                    'CreationDate': bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                }
                
                try:
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    bucket_info['Region'] = location.get('LocationConstraint') or 'us-east-1'
                except:
                    pass
                
                buckets.append(bucket_info)
            
            return buckets
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_rds_instances(self):
        try:
            rds = self.session.client('rds')
            response = rds.describe_db_instances()
            instances = []
            
            for db in response['DBInstances']:
                instances.append({
                    'DBInstanceIdentifier': db.get('DBInstanceIdentifier'),
                    'DBInstanceClass': db.get('DBInstanceClass'),
                    'Engine': db.get('Engine'),
                    'EngineVersion': db.get('EngineVersion'),
                    'DBInstanceStatus': db.get('DBInstanceStatus'),
                    'Endpoint': db.get('Endpoint', {}).get('Address'),
                    'Port': db.get('Endpoint', {}).get('Port'),
                    'VpcSecurityGroups': [sg.get('VpcSecurityGroupId') for sg in db.get('VpcSecurityGroups', [])],
                    'AvailabilityZone': db.get('AvailabilityZone'),
                    'MultiAZ': db.get('MultiAZ'),
                    'StorageEncrypted': db.get('StorageEncrypted')
                })
            
            return instances
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_lambda_functions(self):
        try:
            lambda_client = self.session.client('lambda')
            response = lambda_client.list_functions()
            functions = []
            
            for func in response['Functions']:
                functions.append({
                    'FunctionName': func.get('FunctionName'),
                    'FunctionArn': func.get('FunctionArn'),
                    'Runtime': func.get('Runtime'),
                    'Handler': func.get('Handler'),
                    'Role': func.get('Role'),
                    'CodeSize': func.get('CodeSize'),
                    'Description': func.get('Description'),
                    'Timeout': func.get('Timeout'),
                    'MemorySize': func.get('MemorySize'),
                    'LastModified': func.get('LastModified')
                })
            
            return functions
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_cloudwatch_alarms(self):
        try:
            cloudwatch = self.session.client('cloudwatch')
            response = cloudwatch.describe_alarms()
            alarms = []
            
            for alarm in response['MetricAlarms']:
                alarms.append({
                    'AlarmName': alarm.get('AlarmName'),
                    'AlarmArn': alarm.get('AlarmArn'),
                    'AlarmDescription': alarm.get('AlarmDescription'),
                    'StateValue': alarm.get('StateValue'),
                    'StateReason': alarm.get('StateReason'),
                    'MetricName': alarm.get('MetricName'),
                    'Namespace': alarm.get('Namespace'),
                    'Threshold': alarm.get('Threshold'),
                    'ComparisonOperator': alarm.get('ComparisonOperator')
                })
            
            return alarms
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_vpcs(self):
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_vpcs()
            vpcs = []
            
            for vpc in response['Vpcs']:
                vpcs.append({
                    'VpcId': vpc.get('VpcId'),
                    'CidrBlock': vpc.get('CidrBlock'),
                    'IsDefault': vpc.get('IsDefault'),
                    'State': vpc.get('State'),
                    'Tags': self._extract_tags(vpc.get('Tags', []))
                })
            
            return vpcs
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_security_groups(self):
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_security_groups()
            security_groups = []
            
            for sg in response['SecurityGroups']:
                security_groups.append({
                    'GroupId': sg.get('GroupId'),
                    'GroupName': sg.get('GroupName'),
                    'Description': sg.get('Description'),
                    'VpcId': sg.get('VpcId'),
                    'IpPermissions': sg.get('IpPermissions'),
                    'IpPermissionsEgress': sg.get('IpPermissionsEgress')
                })
            
            return security_groups
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_route53_hosted_zones(self):
        try:
            route53 = self.session.client('route53')
            response = route53.list_hosted_zones()
            zones = []
            
            for zone in response['HostedZones']:
                zones.append({
                    'Id': zone.get('Id'),
                    'Name': zone.get('Name'),
                    'CallerReference': zone.get('CallerReference'),
                    'ResourceRecordSetCount': zone.get('ResourceRecordSetCount'),
                    'Config': zone.get('Config')
                })
            
            return zones
        except (ClientError, NoCredentialsError) as e:
            return {'error': str(e)}
    
    def get_all_resources(self):
        return {
            'ec2_instances': self.get_ec2_instances(),
            's3_buckets': self.get_s3_buckets(),
            'rds_instances': self.get_rds_instances(),
            'lambda_functions': self.get_lambda_functions(),
            'cloudwatch_alarms': self.get_cloudwatch_alarms(),
            'vpcs': self.get_vpcs(),
            'security_groups': self.get_security_groups(),
            'route53_zones': self.get_route53_hosted_zones()
        }
    
    def _extract_tags(self, tags_list):
        if not tags_list:
            return {}
        return {tag['Key']: tag['Value'] for tag in tags_list}
    
    def get_resource_by_type(self, resource_type):
        resource_mapping = {
            'ec2': self.get_ec2_instances,
            's3': self.get_s3_buckets,
            'rds': self.get_rds_instances,
            'lambda': self.get_lambda_functions,
            'cloudwatch': self.get_cloudwatch_alarms,
            'vpc': self.get_vpcs,
            'security_group': self.get_security_groups,
            'route53': self.get_route53_hosted_zones
        }
        
        if resource_type in resource_mapping:
            return resource_mapping[resource_type]()
        else:
            return {'error': f'Unknown resource type: {resource_type}'}
