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


### Lambda ###

# The main api lambda function, sitting behind API Gateway.
resource "aws_lambda_function" "api" {
  function_name = "2020-rechtsinfo-Api"

  s3_bucket = "2020-rechtsinfo-lambda-assets"
  s3_key    = "latest/lambda_function.zip"

  handler = "rip_api.lambda_handlers.api"
  runtime = "python3.8"
  layers  = [aws_lambda_layer_version.deps_layer.arn]

  role = aws_iam_role.lambda_exec.arn
}

# The update function, to be triggered by CloudWatch
resource "aws_lambda_function" "update_data" {
  function_name = "2020-rechtsinfo-UpdateData"

  s3_bucket = "2020-rechtsinfo-lambda-assets"
  s3_key    = "latest/lambda_function.zip"

  handler = "rip_api.lambda_handlers.update_data"
  runtime = "python3.8"
  layers  = [aws_lambda_layer_version.deps_layer.arn]

  role = aws_iam_role.lambda_exec.arn
}

# Lambda layer with all Python dependencies.
resource "aws_lambda_layer_version" "deps_layer" {
  s3_bucket  = "2020-rechtsinfo-lambda-assets"
  s3_key     = "lambda_deps_layer.zip"
  layer_name = "2020-rechtsinfo-lambda-deps"
}

# Create IAM Role and allow Lambda to assume it.
resource "aws_iam_role" "lambda_exec" {
  name = "2020-rechtsinfo-lambda-exec-role"

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

# Allow the role access to VPC.
resource "aws_iam_policy_attachment" "default" {
  name       = "2020-rechtsinfo-lambda-exec-role-vpc-access"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


### API Gateway ###

resource "aws_api_gateway_rest_api" "api_gateway" {
  name        = "2020-rechtsinfo-api-gateway"
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
  name   = "2020-rechtsinfo-rds-pg"
  family = "postgres12.3"
}

resource "aws_db_instance" "default" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "12.3"
  instance_class       = "db.t3.small"
  name                 = "2020-rechtsinfo"
  username             = "rip"
  password             = "NNfLV9~}8xe64ws4P4nt"
  parameter_group_name = aws_db_parameter_group.default.name

  apply_immediately = true
}

output "db_url" {
  aws_db_instance.default.endpoint
}