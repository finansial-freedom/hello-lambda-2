# Hello World Lambda (Docker)

Minimal Python 3.12 AWS Lambda packaged as a container image, deployed by GitHub Actions on a self-hosted EC2 runner. Built for **AWS Academy Learner Lab**, so all IAM uses **LabRole** / **LabInstanceProfile**.

## Deployment guide

AWS resources are created in the **AWS Console**. Region: **us-west-2 (Oregon)**.

### 1. Create the GitHub repository

- On GitHub, create a new repository named `hello-lambda`
  - Visibility: **Public** (branch rulesets in step 10 need a public repo on GitHub Free)
  - Don't add a README, `.gitignore` or license (the project already has them)
- In VS Code, open this project folder and push it to the new repository on the `main` branch
- Check that `app/`, `ci.txt`, `deploy-dev.txt`, `deploy-prod.txt` and `README.md` show up on GitHub

### 2. Create the ECR repository and push the first image

- Go to **Elastic Container Registry → Repositories → Create repository**
- Visibility: **Private**
- Name: `hello-lambda`
- Tag mutability: **Mutable**, encryption: default (AES-256)
- One repo for both envs; images are tagged `dev-<sha>` / `prod-<sha>`

**Task:** build the image from `app/Dockerfile` on your laptop and push it to the `hello-lambda` ECR repository with the tag `initial`.

### 3. Create the Lambda functions

- Go to **Lambda → Functions → Create function → Container image**
- Function name: `hello-lambda-dev`
- Container image URI: **Browse images** → repo `hello-lambda` → pick the `initial` tag from step 2
- Architecture: **x86_64**
- Permissions → **Use an existing role** → **LabRole**
- Create, wait until the state is **Active**
- **Test** tab → event `{}` → should return status 200 with the hardcoded `message_lambda`, `message`, `owner` and `env`
- Repeat for `hello-lambda-prod` (same image is fine)

### 4. Launch the EC2 runner

- Go to **EC2 → Instances → Launch instances**
- Name: `github-runner`
- AMI: **Ubuntu Server 24.04 LTS**, architecture **64-bit (x86)**
- Instance type: **t3.small** (2 vCPU, 2 GiB)
- Key pair: create new → `github-runner-key` (.pem), download it
- Network settings:
  - Default VPC, public subnet, **Auto-assign public IP: Enable**
  - New security group `github-runner-sg`
  - Inbound: **SSH (22)** from **My IP** only (the runner needs no other inbound ports)
- Storage: **30 GiB gp3** (Docker images fill up the default 8 GiB)
- Advanced details → **IAM instance profile: `LabInstanceProfile`** (gives the runner LabRole, so no access keys are needed)
- Launch, wait until **Running** and **2/2 status checks passed**
- Copy the **Public IPv4 address**

### 5. Install Docker + AWS CLI on the runner

**Task:** SSH into the EC2 instance and prepare it to run the workflows.

- SSH into the instance as the `ubuntu` user with your key pair
- Install **Docker Engine** from Docker's official repository (not the Ubuntu `docker.io` package)
  - Make sure the **buildx** plugin is installed too, because the deploy workflows use `docker buildx build`
- Let the `ubuntu` user run Docker **without `sudo`**
- Install **AWS CLI v2**, because the deploy workflows call `aws ecr` and `aws lambda` on the runner
- Install `unzip` and `python3-pip`

### 6. Register the GitHub self-hosted runner

- Repo → **Settings → Actions → Runners → New self-hosted runner** → **Linux / x64**
- On the EC2 instance, run the download + `./config.sh` commands GitHub shows
- Keep the default runner group and labels (`self-hosted, Linux, X64`)
- Install it as a service (don't use `./run.sh`, it stops when SSH closes):

```bash
cd ~/actions-runner
sudo ./svc.sh install ubuntu
sudo ./svc.sh start
```

- Check the runner shows **Idle** in GitHub

### 7. Configure GitHub environments

- Repo → **Settings → Environments** → create `dev` and `prod`
- No secrets needed: the runner uses LabRole through the instance profile
- Add these **environment variables**:

| Variable | dev | prod |
|---|---|---|
| `AWS_REGION` | `us-west-2` | `us-west-2` |
| `ECR_REPOSITORY` | `hello-lambda` | `hello-lambda` |
| `LAMBDA_FUNCTION_NAME` | `hello-lambda-dev` | `hello-lambda-prod` |

- Optional for `prod`: **Required reviewers** + **Deployment branches** limited to `main`

### 8. Create the GitHub Actions workflows

**Task:** the project root has 4 workflow templates: `test-runner.txt`, `ci.txt`, `deploy-dev.txt` and `deploy-prod.txt`. Turn them into GitHub Actions workflows that GitHub can detect, then commit and push to `main`.

- Make sure **Test Self-Hosted Runner**, **CI**, **Deploy DEV** and **Deploy PROD** show up in the repo's **Actions** tab
- Run **Test Self-Hosted Runner** manually (**Run workflow**) and make sure every step is green before moving on
- Fix the workflows so every job runs on **your self-hosted runner** from step 6, not on GitHub-hosted runners
- The deploy workflows must use the runner's **LabRole** (from the instance profile), not AWS secrets

### 9. Create the `dev` branch

- Create a `dev` branch from `main` and push it
- **Deploy DEV** runs and succeeds

### 10. Protect the `dev` and `main` branches

Block direct pushes so changes can only reach `dev` and `main` through a pull request.

- Repo → **Settings → Rules → Rulesets → New ruleset → New branch ruleset**
- Ruleset name: `protect-dev-main`
- Enforcement status: **Active**
- Bypass list: leave **empty** (so the rules apply to admins too)
- Target branches → **Add target → Include by pattern** → add `dev` and `main`
- Branch rules, enable:
  - **Restrict deletions**
  - **Require a pull request before merging** (required approvals: `0` if you work alone, `1` or more for a team)
  - **Require status checks to pass** → **Add checks** → `ci` (the CI job; it only appears after CI has run at least once)
  - **Block force pushes**
- Click **Create**
- Test it: run `git push` straight to `dev` and check that GitHub rejects it

Rulesets work on public repos with GitHub Free. Private repos need GitHub Pro, Team or Enterprise.

## Task: CI/CD practice

Ship one change all the way from a feature branch to production.

### Part 1 – Feature branch

- Pull the latest `dev`
- Create a branch named `feature/<your-name>-hello-message` (e.g. `feature/budi-hello-message`)
- In `app/app.py` (in VS Code), change `message_lambda`, e.g. `"Hello World!"` → `"Hello World from <your-name>!"`
  - Never edit code in the AWS Lambda console editor. Every code change is made locally in **VS Code**, committed with Git, and shipped through the CI/CD pipeline.
- Commit and push the branch

### Part 2 – Pull request to `dev`

- Open a PR: `feature/<your-name>-hello-message` → `dev`
- Make sure the **CI** workflow runs on the PR and passes (green check):
  - flake8 lint
  - Docker build
  - Handler import test
- Merge the PR

### Part 3 – Verify the dev deployment

- Go to **Actions** and make sure **Deploy DEV** started after the merge
- Make sure every step is green, including **Test invoke**
- In **ECR → hello-lambda**, check that a new `dev-<sha>` image exists
- In **Lambda → hello-lambda-dev → Test**, run `{}` and check that the response shows your new `message_lambda`

### Part 4 – Pull request to `main`

- Open a PR: `dev` → `main`
- Make sure **CI** runs on the PR and passes
- Merge the PR

### Part 5 – Verify the prod deployment

- Go to **Actions** and make sure **Deploy PROD** started after the merge
  - If required reviewers are enabled on `prod`, approve the deployment first
- Make sure every step is green, including **Test invoke**
- In **ECR → hello-lambda**, check that a new `prod-<sha>` image exists
- In **Lambda → hello-lambda-prod → Test**, run `{}` and check that the response shows your new `message_lambda`

### Done when

- [ ] CI passed on the PR to `dev`
- [ ] Deploy DEV is green and `hello-lambda-dev` returns the new `message_lambda`
- [ ] CI passed on the PR to `main`
- [ ] Deploy PROD is green and `hello-lambda-prod` returns the new `message_lambda`

## Task: Read values from Secrets Manager

Right now `message`, `owner` and `env` are hardcoded in `app/app.py`. Move them into Secrets Manager.

### Part 1 – Create the secrets

- In **Secrets Manager**, create 2 secrets (type **Other type of secret**):
  - `hello-lambda/dev`
  - `hello-lambda/prod`
- Each secret is JSON with these keys:
  - `message`
  - `owner`
  - `env` (`dev` or `prod`)

### Part 2 – Point each Lambda to its secret

- Add an environment variable `SECRET_NAME` to each Lambda function:
  - `hello-lambda-dev` → `hello-lambda/dev`
  - `hello-lambda-prod` → `hello-lambda/prod`

### Part 3 – Change the code

- Create a branch `feature/<your-name>-secrets-manager` from `dev`
- In VS Code, change `app/app.py` so that `message`, `owner` and `env` are read from the secret named in `SECRET_NAME`
  - Never edit code in the AWS Lambda console editor. Every code change is made locally in **VS Code**, committed with Git, and shipped through the CI/CD pipeline.
- `message_lambda` stays hardcoded
- Commit and push the branch

### Part 4 – Ship it

- PR to `dev` → CI passes → merge → **Deploy DEV** is green
- PR `dev` → `main` → CI passes → merge → **Deploy PROD** is green

### Done when

- [ ] `hello-lambda-dev` returns `message`, `owner` and `env` from `hello-lambda/dev` (`"env": "dev"`)
- [ ] `hello-lambda-prod` returns `message`, `owner` and `env` from `hello-lambda/prod` (`"env": "prod"`)
- [ ] Changing a value in Secrets Manager changes the Lambda response without changing any code

## Learner Lab notes

- EC2 stops when the lab session ends and starts again with the next session; the runner service starts automatically
- The public IP changes after each restart (use the new one for SSH)
- If a job sits on "Waiting for a runner", SSH in and run `sudo ./svc.sh status` in `~/actions-runner`
- If the runner disk is full, run `docker system prune -af`
