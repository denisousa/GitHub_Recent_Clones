from github import Auth, Github
import os
import subprocess
import requests

def download_java_files_from_github(repo_name: str, commit_index: int):
    token = os.getenv('GH_TOKEN')
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # Get SHA of the selected commit
    commits = repo.get_commits()
    if commit_index >= commits.totalCount:
        raise ValueError(f"The repository has only {commits.totalCount} commits. Index {commit_index} is out of range.")
    sha = commits[commit_index].sha

    # Get the full tree recursively
    print(f"Fetching repository tree at commit {sha}...")
    tree = repo.get_git_tree(sha=sha, recursive=True).tree

    java_files = [item for item in tree if item.path.endswith(".java") and item.type == "blob"]
    print(f"Found {len(java_files)} Java files.")

    headers = {"Authorization": f"token {token}"}

    output_dir = repo_name.split('/')[-1]

    for file in java_files:
        raw_url = f"https://raw.githubusercontent.com/{repo_name}/{sha}/{file.path}"
        dest_path = os.path.join(output_dir, file.path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        response = requests.get(raw_url, headers=headers)
        if response.status_code == 200:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            print(f"Failed to download {file.path} (HTTP {response.status_code})")

    print(f"All Java files downloaded to: {os.path.abspath(output_dir)}")


def checkout_repo_commit_by_index(repo_name: str, commit_index: int, local_dir: str = None):
    auth = Auth.Token(os.getenv("GH_TOKEN"))
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    commits = repo.get_commits()
    if commit_index >= commits.totalCount:
        raise ValueError(f"The repository has only {commits.totalCount} commits. Index {commit_index} is out of range.")
    sha = commits[commit_index].sha

    if local_dir is None:
        project_name = repo_name.split("/")[-1]
        local_dir = f"{project_name}"

    if not os.path.exists(local_dir):
        print(f"Cloning {repo_name} into {local_dir}...")
        subprocess.run(["git", "clone", f"https://github.com/{repo_name}.git", local_dir], check=True)
    else:
        print(f"Repository already exists at {local_dir}, reusing it...")

    print(f"Checking out commit {sha}...")
    subprocess.run(["git", "checkout", sha], cwd=local_dir, check=True)

    print(f"Repository '{repo_name}' is now at commit #{commit_index} ({sha}).")
    print(f"Local path: {os.path.abspath(local_dir)}")
    return os.path.abspath(local_dir)
