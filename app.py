import os
import requests
from fuzzywuzzy import process
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import configparser
import logging

# Load configuration from settings.conf
config = configparser.ConfigParser()
config.read('settings.conf')

# Git service settings
GIT_SERVICE = config['GIT Settings']['service']
GIT_API_TOKEN = config['GIT Settings']['api_token']
REPO_OWNER = config['GIT Settings']['repo_owner']
REPO_NAME = config['GIT Settings']['repo_name']

# Server settings
DOMAIN = config['Server Settings']['domain']
USER = config['Server Settings']['user']
PORT = int(config['Server Settings']['port'])
ENABLE_IPV6 = config.getboolean('Server Settings', 'enable_ipv6')

# Installation settings
INSTALL_DIR = config['Installation Settings']['install_dir']

# App behavior settings
MATCH_PERCENTAGE = int(config['App Behavior']['match_percentage'])
LOGGING_LEVEL = config['App Behavior'].get('logging_level', 'Off').upper()
LOG_FILE_LOCATION = config['App Behavior'].get('log_file_location', 'app.log')

# Configure logging based on the logging level
if LOGGING_LEVEL == 'VERBOSE':
    logging.basicConfig(filename=LOG_FILE_LOCATION, level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
elif LOGGING_LEVEL == 'ON':
    logging.basicConfig(filename=LOG_FILE_LOCATION, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
else:
    logging.basicConfig(level=logging.CRITICAL)  # Only log critical errors

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="ratelimit exceeded", message="You have exceeded your rate limit. Please try again later."), 429

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"An error occurred: {str(e)}")
    return jsonify(error="internal server error", message=str(e)), 500

def get_scripts_list(directory=None):
    paths = ['scripts']
    if directory:
        paths.append(f'scripts/{directory}')
    
    scripts = []
    for path in paths:
        try:
            if GIT_SERVICE == 'github':
                url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}'
            elif GIT_SERVICE == 'gitlab':
                url = f'https://gitlab.com/api/v4/projects/{REPO_OWNER}%2F{REPO_NAME}/repository/tree?path={path}'
            else:
                url = f'https://{GIT_SERVICE}.com/api/v4/projects/{REPO_OWNER}%2F{REPO_NAME}/repository/tree?path={path}'
            
            headers = {'Authorization': f'token {GIT_API_TOKEN}'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                if GIT_SERVICE == 'github':
                    scripts.extend([file['name'] for file in response.json() if file['type'] == 'file'])
                elif GIT_SERVICE == 'gitlab':
                    scripts.extend([file['name'] for file in response.json() if file['type'] == 'blob'])
                else:
                    scripts.extend([file['name'] for file in response.json() if file['type'] == 'blob'])
            else:
                logging.error(f"Error fetching scripts from {path}: {response.status_code}")
                raise Exception(f"Error fetching scripts from {path}: {response.status_code}")
        except Exception as e:
            logging.error(f"Exception occurred while fetching scripts: {str(e)}")
            raise Exception(f"Exception occurred while fetching scripts: {str(e)}")
    
    return scripts

def find_best_match(directory, query):
    try:
        scripts = get_scripts_list(directory)
        best_match, score = process.extractOne(query, scripts)
        return best_match, score
    except Exception as e:
        logging.error(f"Exception occurred while finding best match: {str(e)}")
        raise Exception(f"Exception occurred while finding best match: {str(e)}")

def serve_script(directory, query):
    try:
        best_match, score = find_best_match(directory, query)
        if score >= MATCH_PERCENTAGE:
            if GIT_SERVICE == 'github':
                script_url = f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/scripts/{directory}/{best_match}' if directory else f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/scripts/{best_match}'
            elif GIT_SERVICE == 'gitlab':
                script_url = f'https://gitlab.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{directory}/{best_match}' if directory else f'https://gitlab.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{best_match}'
            else:
                script_url = f'https://{GIT_SERVICE}.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{directory}/{best_match}' if directory else f'https://{GIT_SERVICE}.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{best_match}'
            response = requests.get(script_url)
            if response.status_code == 200:
                return response.text
            else:
                logging.error(f"Error fetching script from URL: {script_url}, Status Code: {response.status_code}")
                raise Exception(f"Error fetching script from URL: {script_url}, Status Code: {response.status_code}")
        elif best_match:
            if GIT_SERVICE == 'github':
                vague_match_url = f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/scripts/{directory}/{best_match}' if directory else f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/scripts/{best_match}'
            elif GIT_SERVICE == 'gitlab':
                vague_match_url = f'https://gitlab.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{directory}/{best_match}' if directory else f'https://gitlab.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{best_match}'
            else:
                vague_match_url = f'https://{GIT_SERVICE}.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{directory}/{best_match}' if directory else f'https://{GIT_SERVICE}.com/{REPO_OWNER}/{REPO_NAME}/-/raw/main/scripts/{best_match}'
            return f"Unable to find a close match for the script you've specified, but a script located at {vague_match_url} with {score}% match was found to be a vague match. Perhaps this is what you're after?"
        else:
            return "Error: No suitable script found."
    except Exception as e:
        logging.error(f"Exception occurred while serving script: {str(e)}")
        raise Exception(f"Exception occurred while serving script: {str(e)}")

@app.route('/<directory>/<query>', methods=['GET'])
@app.route('/<query>', methods=['GET'])
@limiter.limit("10 per minute")
def get_script(directory=None, query=None):
    try:
        # Log request details in verbose mode
        if LOGGING_LEVEL == 'VERBOSE':
            logging.debug(f"Request received: directory={directory}, query={query}")
            logging.debug(f"Request headers: {request.headers}")
        
        result = serve_script(directory, query)
        
        # Log response details in verbose mode
        if LOGGING_LEVEL == 'VERBOSE':
            logging.debug(f"Response: {result}")
        
        return result
    except Exception as e:
        logging.error(f"Exception occurred while processing request: {str(e)}")
        return jsonify(error="internal server error", message=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
