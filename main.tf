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


### S3 ###

resource "aws_s3_bucket" "main" {
  bucket = "fellows-2020-rechtsinfo-assets"
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

  handler = "rip_api.lambda_handlers.api"
  runtime = "python3.8"
  layers  = [aws_lambda_layer_version.deps_layer.arn]
  timeout = 30

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

  handler = "rip_api.lambda_handlers.ingest_laws"
  runtime = "python3.8"
  layers  = [aws_lambda_layer_version.deps_layer.arn]
  timeout = 900

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

resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  stage_name  = "prod"
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

output "api_base_url" {
  value = aws_api_gateway_deployment.api.invoke_url
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

output "db_url" {
  value = aws_db_instance.default.endpoint
}
