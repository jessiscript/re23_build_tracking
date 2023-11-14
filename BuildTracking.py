import json
import urlfetch
import base64
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("token", help="Your personal access token")

    return parser.parse_args()

def check_response(response):
    if response.status != 200:
        os.system('clear')
        data = json.loads(response.content)
        message = data.get("message")
        print("An error ocurred. The server responded with the following message: " + message)
        exit()

def get_response(url, token):
    response = urlfetch.get(url, headers={
            "Authorization": "Bearer " + token
        })
    check_response(response)
    return json.loads(response.content)

if __name__ == "__main__":
    args = parse_args()
    
    repo_path = args.repo_path
    branch = args.branch
    token = args.token

    try:  
        data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/ref/heads/' + branch, token)
        commit_sha = data.get("object").get("sha")

        data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/ref/metrics/' + commit_sha, token)
        ref_sha = data.get("object").get("sha")

        data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/trees/' + ref_sha, token)
        blob_sha = data.get("tree")[0].get("sha")

        data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/blobs/' + blob_sha, token)
        content = base64.b64decode(data.get("content"))

        data = json.loads(content)
        print("The image file has a total size of " + str(data.get("image_details").get("total_bytes")) + " bytes.")

    except Exception as e: 
        print("The following exception returned: ", e)
        raise












