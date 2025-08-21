# deployment — Deployment & packaging helpers

This folder contains deployment scripts and configuration for packaging the EVTrack Automation project for different environments (local, serverless/AWS Lambda, etc.). Below is a description of each file and recommended deployment flows.

Directory structure

- `aws-lambda/`
  - `lambda_handler.py` — AWS Lambda entrypoint for the packaged automation. Exposes a handler function compatible with Lambda/ API Gateway (or Lambda Function URL). This file adapts the FastAPI/automation logic to a Lambda environment (may use a lightweight ASGI adapter or invoke specific automation functions directly).
  - `package.json` — Node package manifest used by the Serverless packaging process or by helper scripts that bundle Node-based assets (e.g., for headless Chromium or Puppeteer techniques). May also be used by CI pipelines that run JS-based build/pack steps.
  - `serverless.yml` — Serverless Framework configuration that defines functions, IAM roles, environment variables, memory/timeouts, and API Gateway endpoints. Use this file to deploy the lambda-based API using `serverless deploy`.

- `scripts/`
  - `deploy.sh` — Shell helper script to automate local packaging and deployment steps. Typical responsibilities:
    - Install dependencies
    - Package the project for Lambda (zip or serverless package)
    - Upload artifacts to S3 (if configured)
    - Run `serverless deploy` or call AWS CLI to update functions
  - Additional helper scripts may be present or added for rollback, warming, or blue/green deploy approaches.

Usage notes

1. Local testing
- For development, run the API locally with uvicorn (recommended):
  - `uvicorn api.main:app --reload --host 0.0.0.0 --port 3000`
- Lambda deployments are intended for production/hosted use and usually require additional packaging steps.

2. Serverless / AWS Lambda deployment
- Ensure you have the Serverless Framework installed and configured with AWS credentials:
  - `npm install -g serverless`
  - `serverless config credentials --provider aws --key <AWS_KEY> --secret <AWS_SECRET>`
- Edit `serverless.yml` to set the stage, region, memory, and environment variables (EVTRACK_EMAIL, EVTRACK_PASSWORD, etc.).
- From the `deployment/aws-lambda/` directory run:
  - `serverless deploy` (this will package and deploy according to `serverless.yml`)

3. Environment variables and secrets
- Do not hard-code secrets in `serverless.yml`. Use encrypted variables (Serverless Variables referencing SSM/Secrets Manager) or populate stage-specific env files.
- Required runtime variables typically include EVTrack credentials and any API keys or OAuth client IDs.

4. Packaging notes
- The automation relies on a Selenium webdriver and may require native binaries (Chrome/Chromium and chromedriver). Packaging these for Lambda often requires building a Lambda-friendly headless Chromium binary or using a Lambda layer that provides the browser.
- Consider using one of the community Lambda layers for headless Chrome, or package a static build of Chromium and chromedriver in a Lambda layer.

5. CI/CD
- Use CI pipelines to run tests, linting, build artifacts and deploy to staging with `serverless deploy --stage staging`.
- Store AWS credentials in CI secrets and use Serverless configuration to reference those securely.

7. Rollback & updates
- Serverless keeps track of deployed versions — use `serverless rollback -v <version>` to revert, or deploy a new version with updated code.
- For safe updates, deploy to a staging stage, run smoke tests, then deploy to production.
