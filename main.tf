terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 2.70"
    }
  }
}

provider "aws" {
  profile = "default"
  region  = "eu-central-1"
}

provider "aws" {
  alias  = "cloudfront-acm-certs"
  region = "us-east-1"
}


### S3 ###

resource "aws_s3_bucket" "main" {
  bucket = "fellows-2020-rechtsinfo-assets"
}

# Allow public access to public/
resource "aws_s3_bucket_policy" "main_public" {
  bucket = aws_s3_bucket.main.id

  policy = <<POLICY
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AddPerm",
      "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject"],
      "Resource":["arn:aws:s3:::${aws_s3_bucket.main.bucket}/public/*"]
      }
  ]
}
POLICY
}

resource "aws_s3_bucket" "clickdummy_redirect" {
  bucket = "clickdummy.rechtsinformationsportal.de"
  website {
    redirect_all_requests_to = "https://rechtsinformationsportal.webflow.io"
  }
}


### VPC data ###

resource "aws_default_vpc" "default" {
}

data "aws_subnet_ids" "default_vpc" {
  vpc_id = aws_default_vpc.default.id
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

# Add VPC Endpoint for VPC-connected Lambdas to access S3
resource "aws_vpc_endpoint" "s3" {
  vpc_id          = aws_default_vpc.default.id
  service_name    = "com.amazonaws.eu-central-1.s3"
  route_table_ids = [aws_default_vpc.default.default_route_table_id]
}


### Lambda ###

# The main api lambda function, sitting behind API Gateway.
resource "aws_lambda_function" "api" {
  function_name = "fellows-2020-rechtsinfo-Api"

  s3_bucket = aws_s3_bucket.main.bucket
  s3_key    = "lambda_function.zip"

  handler     = "rip_api.lambda_handlers.api"
  runtime     = "python3.8"
  layers      = [aws_lambda_layer_version.deps_layer.arn]
  timeout     = 30
  memory_size = 2048

  role = aws_iam_role.lambda_exec.arn

  vpc_config {
    subnet_ids         = data.aws_subnet_ids.default_vpc.ids
    security_group_ids = ["${aws_default_vpc.default.default_security_group_id}"]
  }

  environment {
    variables = {
      DB_URI = "postgresql://${aws_db_instance.default.username}:${aws_db_instance.default.password}@${aws_db_instance.default.endpoint}/rechtsinfo"
    }
  }
}

# Update function to download law data, triggered by CloudWatch
resource "aws_lambda_function" "download_laws" {
  function_name = "fellows-2020-rechtsinfo-DownloadLaws"

  s3_bucket = aws_s3_bucket.main.bucket
  s3_key    = "lambda_function.zip"

  handler = "rip_api.lambda_handlers.download_laws"
  runtime = "python3.8"
  layers  = [aws_lambda_layer_version.deps_layer.arn]
  timeout = 900

  role = aws_iam_role.lambda_exec.arn
}

# Function to ingest downloaded laws, connected to the VPC for RDS access, triggered by the download function.
resource "aws_lambda_function" "ingest_laws" {
  function_name = "fellows-2020-rechtsinfo-IngestLaws"

  s3_bucket = aws_s3_bucket.main.bucket
  s3_key    = "lambda_function.zip"

  handler     = "rip_api.lambda_handlers.ingest_laws"
  runtime     = "python3.8"
  layers      = [aws_lambda_layer_version.deps_layer.arn]
  timeout     = 900
  memory_size = 2048

  role = aws_iam_role.lambda_exec.arn

  vpc_config {
    subnet_ids         = data.aws_subnet_ids.default_vpc.ids
    security_group_ids = ["${aws_default_vpc.default.default_security_group_id}"]
  }

  environment {
    variables = {
      DB_URI = "postgresql://${aws_db_instance.default.username}:${aws_db_instance.default.password}@${aws_db_instance.default.endpoint}/rechtsinfo"
    }
  }
}

# Lambda layer with all Python dependencies.
resource "aws_lambda_layer_version" "deps_layer" {
  s3_bucket  = aws_s3_bucket.main.bucket
  s3_key     = "lambda_deps_layer.zip"
  layer_name = "fellows-2020-rechtsinfo-lambda-deps"
}

# Create IAM Role and allow Lambda to assume it.
resource "aws_iam_role" "lambda_exec" {
  name = "fellows-2020-rechtsinfo-lambda-exec-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

# Allow the role access to VPC (and thereby RDS).
resource "aws_iam_role_policy_attachment" "rds-access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Allow the role access to S3.
resource "aws_iam_role_policy_attachment" "s3-access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Allow the role to invoke Lambda functions.
resource "aws_iam_role_policy_attachment" "lambda-access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

# Schedule the update functions to run daily.
resource "aws_cloudwatch_event_rule" "daily_import" {
  name                = "fellows-2020-rechtsinfo-daily-import"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "daily_import" {
  rule = aws_cloudwatch_event_rule.daily_import.name
  arn  = aws_lambda_function.download_laws.arn
}

# Allow lambda funtion to be triggered by CloudWatch Events.
resource "aws_lambda_permission" "allow_cloudwatch_invoke" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.download_laws.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_import.arn
}


### API Gateway ###

resource "aws_api_gateway_rest_api" "api_gateway" {
  name        = "fellows-2020-rechtsinfo-api-gateway"
  description = "API Gateway for the RIP API"
}

# Proxy all incoming requests to the Lambda function
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  parent_id   = aws_api_gateway_rest_api.api_gateway.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  resource_id = aws_api_gateway_method.proxy.resource_id
  http_method = aws_api_gateway_method.proxy.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# Separate handler for /, since that's not covered by the proxy.
resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  resource_id   = aws_api_gateway_rest_api.api_gateway.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_stage" "prod" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.api_gateway.id
  deployment_id = aws_api_gateway_deployment.api.id
}

resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = "prod"

  lifecycle {
    create_before_destroy = true
  }
}

# Permission for the API Gateway to invoke the api Lambda function.
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"

  # The "/*/*" portion grants access from any method on any resource
  # within the API Gateway REST API.
  source_arn = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/*/*"
}


### RDS ###

# Create parameter group, so that parameters can be changed later without recreating the DB instance.
resource "aws_db_parameter_group" "default" {
  name   = "fellows-2020-rechtsinfo-rds-pg"
  family = "postgres12"
}

resource "aws_db_instance" "default" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "12.3"
  instance_class         = "db.t3.small"
  name                   = "rechtsinfo"
  username               = "rip"
  # Warning: this is the DB password in plain text. Even if removed here, it will remain in the
  # terraform state file. For the Tech4Germany project, this is fine (no personal information is
  # stored and the database is not accessible from the internet), but for a more permanent
  # deployment, this should be handled with more care. See e.g. https://blog.gruntwork.io/a-comprehensive-guide-to-managing-secrets-in-your-terraform-code-1d586955ace1
  password               = "NNfLV9~}8xe64ws4P4nt"
  parameter_group_name   = aws_db_parameter_group.default.name
  vpc_security_group_ids = ["${aws_security_group.allow_db_access.id}"]

  apply_immediately = true
}

# Security group for the DB instance that allows access from the default VPC's
# default security group.
resource "aws_security_group" "allow_db_access" {
  name        = "fellows-2020-rechtsinfo-allow-rds-access"
  description = "Allow RDS access from the default SG"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    description     = "Postgres from the default SG"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = ["${aws_default_vpc.default.default_security_group_id}"]
  }
}


### DNS and related ###

resource "aws_route53_zone" "rip" {
  name = "rechtsinformationsportal.de"
}

resource "aws_route53_record" "clickdummy" {
  name    = "clickdummy.rechtsinformationsportal.de"
  zone_id = aws_route53_zone.rip.zone_id
  type    = "A"

  alias {
    name                   = aws_s3_bucket.clickdummy_redirect.website_domain
    zone_id                = aws_s3_bucket.clickdummy_redirect.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_api_gateway_domain_name" "api" {
  domain_name     = "api.rechtsinformationsportal.de"
  certificate_arn = aws_acm_certificate_validation.api.certificate_arn
}

resource "aws_api_gateway_base_path_mapping" "api" {
  api_id      = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = aws_api_gateway_deployment.api.stage_name
  domain_name = aws_api_gateway_domain_name.api.domain_name
}

resource "aws_route53_record" "api" {
  name    = aws_api_gateway_domain_name.api.domain_name
  zone_id = aws_route53_zone.rip.zone_id
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.api.cloudfront_domain_name
    zone_id                = aws_api_gateway_domain_name.api.cloudfront_zone_id
    evaluate_target_health = true
  }
}


### SSL certificates and validation ###

resource "aws_acm_certificate" "api" {
  # cf. https://github.com/terraform-providers/terraform-provider-aws/issues/5146
  provider          = aws.cloudfront-acm-certs
  domain_name       = "api.rechtsinformationsportal.de"
  validation_method = "DNS"
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.rip.zone_id
}

resource "aws_acm_certificate_validation" "api" {
  provider                = aws.cloudfront-acm-certs
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}
