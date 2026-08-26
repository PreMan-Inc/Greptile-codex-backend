#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-greptile-codex-backend-demo}"
DEMO_PASSWORD="${DEMO_PASSWORD:-PremanDemo123!}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-preman-deployments-${ACCOUNT_ID}-${AWS_REGION}}"

mkdir -p build/lambda
rm -rf build/lambda/* build/function.zip

uv export \
  --frozen \
  --no-dev \
  --no-emit-project \
  --quiet \
  --output-file build/lambda-requirements.txt

uv pip install \
  --quiet \
  --requirement build/lambda-requirements.txt \
  --target build/lambda \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --only-binary :all:

cp -R app build/lambda/app
(
  cd build/lambda
  zip -qr ../function.zip .
)

ARTIFACT_DIGEST="$(git hash-object build/function.zip)"
ARTIFACT_KEY="greptile-codex-backend/${GITHUB_SHA:-$(git rev-parse --short HEAD)}-${ARTIFACT_DIGEST:0:12}/function.zip"

if ! aws s3api head-bucket --bucket "${ARTIFACT_BUCKET}" 2>/dev/null; then
  aws s3api create-bucket --bucket "${ARTIFACT_BUCKET}" --region "${AWS_REGION}"
  aws s3api put-bucket-versioning \
    --bucket "${ARTIFACT_BUCKET}" \
    --versioning-configuration Status=Enabled
  aws s3api put-public-access-block \
    --bucket "${ARTIFACT_BUCKET}" \
    --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-encryption \
    --bucket "${ARTIFACT_BUCKET}" \
    --server-side-encryption-configuration \
      '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'
fi

aws s3 cp build/function.zip "s3://${ARTIFACT_BUCKET}/${ARTIFACT_KEY}"

aws cloudformation deploy \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --template-file infra/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    CodeBucket="${ARTIFACT_BUCKET}" \
    CodeKey="${ARTIFACT_KEY}" \
    DemoPassword="${DEMO_PASSWORD}" \
  --tags application=greptile-codex-backend environment=hackathon-demo

aws cloudformation update-termination-protection \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --enable-termination-protection >/dev/null

aws cloudformation describe-stacks \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
