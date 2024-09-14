## Migration Tag Helper

# Intro

This sample is designed for new AWS customers. Its main purpose is to guide customers on how to quickly and conveniently obtain tag information for specific resources under their account. Compared to the Tag Editor Console, using boto3 can help customers only obtain information related to MAP tags, reducing the chances of customers missing tags or adding too many tags.

# Prerequisites

In order to execute the sample in this repository you'll need the following:

* An AWS account
* The latest version of the AWS Command Line Interface ([AWS CLI](https://aws.amazon.com/cli/)) configured and with permissions to “Describe” resources information of the account
* Python 3.8 and boto3 installed
* Clone this repository into your local environment

# Configuration and Execution

This sample uses Python boto3, so it is necessary to install the required dependencies before running it.

```
cd mig-tag-helper/
python3 -m pip install -r requirements.txt -t "python/"
```

After installed requirements, we need to change the configure file to choose in which regions and which servers taht need to be collected.

```
cd mig-tag-helper/
vi config.ini
```

Here is an example of setting regions, services and tag:

```
[Regions]
RegionList = us-east-1, ap-southeast-1, eu-central-1, sa-east-1, us-west-2

[Services]
ServicesList = ec2, efs, elasticache, elbv2, lambda, rds, s3, sns, gamelift, docdb, glue, backup, logs

[MAPTag]
Tag = map-migrated
```

Using following command to execute the sample:

```
python3 mig-tag-solution.py 
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

