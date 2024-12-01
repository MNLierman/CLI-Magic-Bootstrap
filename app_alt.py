# THIS IS AN ALTERNATIVE VERSION OF THE APP.
# I CREATED TWO VERSIONS AND THIS ONE IS NOT THE ONE I PICKED TO CONTINUE WORKING WITH.
# THIS VERSION STILL HAS VALUE, AND I MAY MERGE THE TWO LATER, BUT THE PROJECT IS STILL BEING TESTED.

from flask import Flask, request, jsonify
from fuzzywuzzy import process
import requests
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# GitHub repository details
GITHUB_USER = 'yourusername'
GITHUB_REPO = 'script-repo'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/'
GITHUB_TOKEN = 'your_personal_access_token'  # Replace with your personal access token

# List all scripts in the specified directory on GitHub
def list_scripts(directory):
    url = GITHUB_API_URL + directory
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        scripts = [item['name'] for item in response.json() if item['type'] == 'file']
        logging.info(f"Scripts in {directory}: {scripts}")
        return scripts
    else:
        logging.warning(f"Failed to list scripts in {directory}. Status code: {response.status_code}")
        return []

# Get the best matching scripts for the query in the specified directory
def get_script(directory, query):
    scripts = list_scripts(directory)
    matches = process.extract(query, scripts, limit=3)
    logging.info(f"Matches for query '{query}' in {directory}: {matches}")
    return matches

# Fetch the script based on the directory and query provided in the URL
@app.route('/<path:dir_and_query>', methods=['GET'])
def fetch_script(dir_and_query):
    parts = dir_and_query.split('/')
    directory = '/'.join(parts[:-1])
    query = parts[-1]

    logging.info(f"Received request for directory: {directory}, query: {query}")

    matches = get_script(directory, query)
    if not matches:
        logging.error("No matching script found.")
        return jsonify({"error": "No matching script found"}), 404
    
    # Auto-select the top match if the -y option is provided or if the match score is very high
    if 'y' in request.args or matches[0][1] > 80:
        selected_script = matches[0][0]
    else:
        options = {i+1: f"{directory}/{match[0]}" for i, match in enumerate(matches)}
        logging.info(f"Multiple matches found: {options}")
        return jsonify({"options": options}), 200
    
    script_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{directory}/{selected_script}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(script_url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Selected script: {script_url}")
        return response.text
    else:
        logging.error(f"Script not found: {script_url}")
        return jsonify({"error": "Script not found"}), 404

# Select a script from multiple options based on user input
@app.route('/select/<path:dir_and_query>/<int:option>', methods=['GET'])
@app.route('/s/<path:dir_and_query>/<int:option>', methods=['GET'])
@app.route('/sel/<path:dir_and_query>/<int:option>', methods=['GET'])
def select_script(dir_and_query, option):
    parts = dir_and_query.split('/')
    directory = '/'.join(parts[:-1])
    query = parts[-1]

    logging.info(f"Received selection request for directory: {directory}, query: {query}, option: {option}")

    matches = get_script(directory, query)
    if not matches or option < 1 or option > len(matches):
        logging.error("Invalid option selected.")
        return jsonify({"error": "Invalid option"}), 404
    
    selected_script = matches[option-1][0]
    script_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{directory}/{selected_script}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(script_url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Selected script: {script_url}")
        return response.text
    else:
        logging.error(f"Script not found: {script_url}")
        return jsonify({"error": "Script not found"}), 404

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
