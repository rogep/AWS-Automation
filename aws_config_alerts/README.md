# AWS Config Alerts

CloudFormation templates to generate an SNS topic to sends non-compliance alerts to any reporting medium (slack, email,
etc). These templates are based on an [AWS blog post](https://aws.amazon.com/blogs/mt/managing-aged-access-keys-through-aws-config-remediations/) with modifications that enable AWS config on accounts without this
enabled, and a custom lambda that checks if config already exists before provisioning.

