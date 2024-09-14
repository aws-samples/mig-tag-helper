import boto3
import configparser
from botocore.exceptions import ClientError

config = configparser.ConfigParser()
config.read('config.ini')

# Define the regions and services to iterate over
regions = set(config['Regions']['RegionList'].replace(" ","").split(','))
services = set(config['Services']['ServicesList'].replace(" ","").split(','))
tag = config['MAPTag']['Tag']

# Function to create clients for all services
def create_clients(region):
    global services
    return {service: boto3.client(service, region) for service in services}

# Function to write tags to file
def write_tags_to_file(resource_type, resource_id, tags, file):
    file.write(f"{resource_type} ID: {resource_id} ")
    file.write("Tags: ")
    for key, value in tags.items():
        file.write(f"  {key}: {value} ")
    file.write("\n")

# Function to fetch and write resource tags
def fetch_and_write_tags(client, resource_type, file):
    resource_tags = call_function(resource_type,client)
    if resource_tags is not None:
        for resource_id, tags in resource_tags.items():
            write_tags_to_file(resource_type, resource_id, tags, file)

# Define tag fetching functions for each resource type
def get_ec2_instance_tags(ec2_client):
    response = ec2_client.describe_instances()
    instance_tags = {}
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            tags = instance.get('Tags', [])
            instance_tags[instance_id] = {tag['Key']: tag['Value'] for tag in tags}
    return instance_tags

def get_efs_tags(efs_client):
    response = efs_client.describe_file_systems()
    file_system_tags = {}
    for file_system in response['FileSystems']:
        file_system_id = file_system['FileSystemId']
        tags_response = efs_client.describe_tags(FileSystemId=file_system_id)
        tags = tags_response.get('Tags', [])
        file_system_tags[file_system_id] = {tag['Key']: tag['Value'] for tag in tags}
    return file_system_tags

def get_elbv2_tags(elbv2_client):
        load_balancers_response = elbv2_client.describe_load_balancers()
        load_balancer_tags = {}
        for load_balancer in load_balancers_response['LoadBalancers']:
            load_balancer_arn = load_balancer['LoadBalancerArn']
            tags_response = elbv2_client.describe_tags(ResourceArns=[load_balancer_arn])
            tags = tags_response['TagDescriptions'][0]['Tags']
            load_balancer_tags[load_balancer_arn] = {tag['Key']: tag['Value'] for tag in tags}
        return load_balancer_tags

def get_elasticache_tags(elasticache_client):
    paginator = elasticache_client.get_paginator('describe_cache_clusters')
    cluster_tags = {}

    for page in paginator.paginate():
        for cluster in page['CacheClusters']:
            cluster_id = cluster['CacheClusterId']
            cluster_arn = f"arn:aws:elasticache:{elasticache_client.meta.region_name}:{boto3.client('sts').get_caller_identity()['Account']}:cluster:{cluster_id}"
            tags_response = elasticache_client.list_tags_for_resource(ResourceName=cluster_arn)
            tags = tags_response.get('TagList', [])
            cluster_tags[cluster_id] = {tag['Key']: tag['Value'] for tag in tags}

    return cluster_tags
    
def get_lambda_tags(lambda_client):
    functions_response = lambda_client.list_functions()
    function_tags = {}
    for function in functions_response['Functions']:
        function_arn = function['FunctionArn']
        tags_response = lambda_client.list_tags(Resource=function_arn)
        tags = tags_response.get('Tags', {})
        function_tags[function_arn] = tags
    return function_tags

def get_rds_instance_tags(rds_client):
    instances_response = rds_client.describe_db_instances()
    instance_tags = {}
    for instance in instances_response['DBInstances']:
        instance_arn = instance['DBInstanceArn']
        tags_response = rds_client.list_tags_for_resource(ResourceName=instance_arn)
        tags = tags_response.get('TagList', [])
        instance_tags[instance_arn] = {tag['Key']: tag['Value'] for tag in tags}
    return instance_tags

def get_gamelift_fleet_tags(gamelift_client):
    fleets_response = gamelift_client.list_fleets()
    fleet_tags = {}
    for fleet_id in fleets_response['FleetIds']:
        fleet_arn = f"arn:aws:gamelift:{gamelift_client.meta.region_name}:{boto3.client('sts').get_caller_identity()['Account']}:fleet/{fleet_id}"
        tags_response = gamelift_client.list_tags_for_resource(ResourceARN=fleet_arn)
        tags = tags_response.get('Tags', [])
        fleet_tags[fleet_id] = {tag['Key']: tag['Value'] for tag in tags}
    return fleet_tags

def get_docdb_tags(docdb_client):
    instances_tags = {}
    instances_response = docdb_client.describe_db_instances(Filters=[{'Name': 'engine', 'Values': ['docdb']}])
    for instance in instances_response['DBInstances']:
        instance_arn = instance['DBInstanceArn']
        tags_response = docdb_client.list_tags_for_resource(ResourceName=instance_arn)
        instances_tags[instance_arn] = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}

    return instances_tags

def get_backup_tags(backup_client):
    vaults_tags = {}
    vault_paginator = backup_client.get_paginator('list_backup_vaults')
    for vault_page in vault_paginator.paginate():
        for vault in vault_page['BackupVaultList']:
            vault_arn = vault['BackupVaultArn']
            tags_response = backup_client.list_tags(ResourceArn=vault_arn)
            vaults_tags[vault_arn] = tags_response.get('Tags', {})
    return vaults_tags

def get_cloudwatch_log_group_tags(logs_client):
    log_groups_tags = {}
    paginator = logs_client.get_paginator('describe_log_groups')
    for page in paginator.paginate():
        for log_group in page['logGroups']:
            log_group_name = log_group['logGroupName']
            tags_response = logs_client.list_tags_log_group(logGroupName=log_group_name)
            log_groups_tags[log_group_name] = tags_response.get('tags', {})
    return log_groups_tags
    
def get_glue_tags(glue_client):
    jobs_tags = {}
    paginator = glue_client.get_paginator('get_jobs')
    try:
        for page in paginator.paginate():
            for job in page['Jobs']:
                job_name = job['Name']
                job_arn = f"arn:aws:glue:{region}:{boto3.client('sts').get_caller_identity()['Account']}:job/{job_name}"
                tags_response = glue_client.get_tags(ResourceArn=job_arn)
                jobs_tags[job_arn] = tags_response.get('Tags', {})
    except Exception as e:
        print(f"Error listing jobs: {e}")
    return jobs_tags

def get_sns_tags(sns_client):
    topics_response = sns_client.list_topics()
    topic_tags = {}
    paginator = sns_client.get_paginator('list_topics')
    for page in paginator.paginate():
        for topic in page['Topics']:
            topic_arn = topic['TopicArn']
            tags_response = sns_client.list_tags_for_resource(ResourceArn=topic_arn)
            tags = tags_response.get('Tags', [])
            topic_tags[topic_arn] = {tag['Key']: tag['Value'] for tag in tags}
    return topic_tags

def get_s3_bucket_tags(s3_client):
    # Get all S3 buckets
    response = s3_client.list_buckets()
    buckets = response['Buckets']
    bucket_tags = {}

    for bucket in buckets:
        bucket_name = bucket['Name']
        try:
            #Get tag for each bucket
            tags_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            tags = tags_response.get('TagSet', [])
            #Store bucket and its tags in a dictionary
            bucket_tags[bucket_name] = {tag['Key']: tag['Value'] for tag in tags}
        except ClientError as e:
            #Catch exception of No Tag buckets
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                bucket_tags[bucket_name] = {"No Tag":"No Tag"}
            else:
                print(f"An error occurred while processing bucket '{bucket_name}': {e}")

    return bucket_tags

#Call fetch function by providing resource type    
dispatch = {
    'ec2': get_ec2_instance_tags,
    'efs': get_efs_tags,
    'elbv2': get_elbv2_tags,
    'elasticache': get_elasticache_tags,
    'lambda': get_lambda_tags,
    'rds': get_rds_instance_tags,
    'gamelift': get_gamelift_fleet_tags,
    'docdb': get_docdb_tags,
    'backup': get_backup_tags,
    'logs': get_cloudwatch_log_group_tags,
    'glue': get_glue_tags,
    'sns': get_sns_tags,
    's3': get_s3_bucket_tags
}

#Return specified function by dispatch
def call_function(func_name, client):
    if func_name in dispatch:
        return dispatch[func_name](client)
    else:
        print(f"Function not found for {func_name}" ) 

# Main execution
with open('map-resources.txt', 'w') as file:
    pass  # Clear the file

#S3 buckets information only need one time fetching
s3_call = 0

for region in regions:
    print(f"Fetching '{region}' resources")
    clients = create_clients(region)

    with open("map-resources.txt", "a") as file:
        file.write(f"Region: {region}\n")
        for service in services:
            if service == 's3':
                s3_call += 1
                if s3_call == 1:
                    print(f"    Fetching '{service}' resources")
                    fetch_and_write_tags(clients[service], service, file)
            else:
                print(f"    Fetching '{service}' resources")
                fetch_and_write_tags(clients[service], service, file)
                
# Function to filter lines from a file
def filter_lines(input_file, output_file, exclude_string):
    with open(input_file, 'r') as infile:
        with open(output_file, 'w') as outfile:
            for line in infile:
                if exclude_string not in line:
                    outfile.write(line)

# Filter lines from the map-resources.txt
input_file = 'map-resources.txt'
output_file = 'map-resources-no-map-tag.txt'
exclude_string = 'map-migrated'
filter_lines(input_file, output_file, exclude_string)