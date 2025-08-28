import os
import subprocess
import tempfile
import uuid
from datetime import datetime

from fastapi import FastAPI, Request
import requests
from dotenv import load_dotenv
import uvicorn

load_dotenv()  # load GITHUB_TOKEN from .env

app = FastAPI()


@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()

    repo_url = data.get("repository", {}).get("clone_url")
    branch = data.get("ref").split("/")[-1]
    commit_sha = data.get("after")
    repo_full_name = data.get("repository", {}).get("full_name")  # e.g., "user/repo"

    timestamp = datetime.now().isoformat()

    print(f"[{timestamp}] Received webhook for {repo_full_name}, branch {branch}, commit {commit_sha}")

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_repo(repo_url, branch, commit_sha, temp_dir)

        compile_success, compile_log = compile_project(temp_dir)
        test_success, test_log = run_tests(temp_dir)

    # Send statuses back to GitHub
    send_commit_status(commit_sha, "success" if compile_success else "failure",
                       "Compilation finished", repo_full_name, context="ci/compile")
    send_commit_status(commit_sha, "success" if test_success else "failure",
                       "Tests finished", repo_full_name, context="ci/tests")

    return {"message": "CI job done"}


def clone_repo(repo_url, branch, commit_sha, dir):
    subprocess.run(f"git clone {repo_url} {dir}", shell=True, check=True)
    subprocess.run(f"cd {dir} && git checkout {branch} && git reset --hard {commit_sha}",
                   shell=True, check=True)


def compile_project(dir):
    result = subprocess.run(f"cd {dir} && python -m compileall .",
                            shell=True, capture_output=True, text=True)
    success = result.returncode == 0
    return success, result.stdout + result.stderr

def run_tests(dir):
    result = subprocess.run(f"cd {dir} && python -m unittest discover tests",
                            shell=True, capture_output=True, text=True)
    success = result.returncode == 0
    return success, result.stdout + result.stderr


def send_commit_status(commit_sha, state, description, repo_full_name, context="ci/demo"):
    github_token = os.getenv("GITHUB_TOKEN")
    url = os.getenv("GITHUB_API_URL") + f"/{commit_sha}"
    #url = f"https://api.github.com/repos/{repo_full_name}/statuses/{commit_sha}"
    headers = {"Authorization": f"token {github_token}",
               "Accept": "application/vnd.github.v3+json"}
    payload = {"state": state, "description": description, "context": context}
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Sent status '{state}' for {context}: {resp.status_code}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
