from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import requests
from fuzzywuzzy import process

# GitHub API token and repository details
GITHUB_API_TOKEN = 'your_github_api_token'
REPO_OWNER = 'your_github_username'
REPO_NAME = 'your_repo_name'

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

def get_scripts_list(directory):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{directory}'
    headers = {'Authorization': f'token {GITHUB_API_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [file['name'] for file in response.json() if file['type'] == 'file']
    else:
        return []

def find_best_match(directory, query):
    scripts = get_scripts_list(directory)
    best_match, score = process.extractOne(query, scripts)
    return best_match, score

def serve_script(directory, query):
    best_match, score = find_best_match(directory, query)
    if score > 80:
        script_url = f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{directory}/{best_match}'
        response = requests.get(script_url)
        if response.status_code == 200:
            return response.text
        else:
            return "Error: Unable to fetch the script."
    elif best_match:
        vague_match_url = f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{directory}/{best_match}'
        return f"Unable to find a close match for the script you've specified, but a script located at {vague_match_url} with {score}% match was found to be a vague match. Perhaps this is what you're after?"
    else:
        return "Error: No suitable script found."

@app.route('/<directory>/<query>', methods=['GET'])
@limiter.limit("10 per minute")
def get_script(directory, query):
    return serve_script(directory, query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
