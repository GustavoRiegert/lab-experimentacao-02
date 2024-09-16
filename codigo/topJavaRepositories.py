import requests
import os
import subprocess
import shutil
import pandas as pd

def fetch_top_java_repositories():
    url = 'https://api.github.com/graphql'
    
    token = ''
    query = """
    {
      search(query: "language:Java stars:>1 fork:false sort:stars-desc", type: REPOSITORY, first: 1, after: null) {
        repositoryCount
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          node {
            ... on Repository {
              name
              url
            }
          }
        }
      }
    }
    """
    headers = {'Authorization': f'Bearer {token}'}
    repositories = []

    while len(repositories) < 1:
        response = requests.post(url, json={'query': query}, headers=headers)
        data = response.json().get('data', {}).get('search', {})

        repositories.extend(data.get('edges', []))
        if not data.get('pageInfo', {}).get('hasNextPage'):
            break

        query = query.replace(
            f'after: null', f'after: "{data["pageInfo"]["endCursor"]}"'
        )

    return repositories[:1]

def clone_repository(url, target_dir):
    try:
        subprocess.run(['git', 'clone', url, target_dir], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")

def clone_repositories_and_run_ck(repositories, target_dir, results_dir, ck_dir):
    for repo in repositories:
        name = repo['node']['name']
        url = repo['node']['url'] + '.git'
        directory = os.path.join(target_dir, name)
        os.makedirs(directory, exist_ok=True)
        clone_repository(url, directory)
        run_ck_analysis(directory, results_dir, ck_dir, name)

def run_ck_analysis(repo_path, results_dir, ck_dir, repo_name):
    try:
        print(f"Running CK analysis on {repo_path}...")
        ck_results = os.path.join(results_dir, repo_name)
        ck_command = f'java -jar {ck_dir} {repo_path} true 0 false {ck_results}'
        if not os.path.exists(ck_results):
            os.makedirs(ck_results)
        subprocess.run(ck_command, shell=True)
        print(f"CK analysis completed for {repo_path}")
    except Exception as e:
        print(f"Error occurred during CK analysis for {repo_path}: {e}")

def append_to_excel(results_dir, excel_path):
    excel_data = pd.DataFrame()
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(root, file))
                excel_data = excel_data.append(df, ignore_index=True)

    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
            excel_data.to_excel(writer, index=False, header=False, sheet_name='Metrics') 
    else:
        excel_data.to_excel(excel_path, index=False, sheet_name='Metrics') 
def main():
    repositories = fetch_top_java_repositories()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repositories_dir = os.path.join(current_dir, 'repositories')
    results_dir = os.path.join(current_dir, "results")
    ck_path = os.path.join(current_dir, "scripts", "ck_script", "target","ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar")
    excel_path = os.path.join(current_dir, "metrics.xlsx")

    if not os.path.exists(repositories_dir):
        os.makedirs(repositories_dir)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    clone_repositories_and_run_ck(repositories, repositories_dir, results_dir, ck_path)
    append_to_excel(results_dir, excel_path)

if __name__ == "__main__":
    main()
