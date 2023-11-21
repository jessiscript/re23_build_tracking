import json
import urlfetch
import base64
import os
import argparse
import pandas as pd
from dateutil import parser
import matplotlib.pyplot as plt
import seaborn as sns

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("n", help="Last n commits")
    parser.add_argument("token", help="Your personal access token")

    return parser.parse_args()

def check_response(response):
    if response.status != 200:
        data = json.loads(response.content)
        message = data.get("message")
        print("An error ocurred. The server responded with the following message: " + message)
        return False
    return True

def get_response(url, token):
    response = urlfetch.get(url, headers={
            "Authorization": "Bearer " + token
        })
    if check_response(response):
        return json.loads(response.content)
    return None

def get_image_size(commit_sha):
    data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/ref/metrics/' + commit_sha, token)
    if data != None:
        ref_sha = data.get("object").get("sha")
    else:
        return 0

    data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/trees/' + ref_sha, token)
    if data != None:
        blob_sha = data.get("tree")[0].get("sha")
    else:
        return 0

    data = get_response('https://api.github.com/repos/jessiscript/' + repo_path + '/git/blobs/' + blob_sha, token)
    if data != None:
        content = base64.b64decode(data.get("content"))
        data = json.loads(content)
        return data.get("image_details").get("total_bytes")
    else:
        return 0
    
def format_date(date):
    return parser.isoparse(date).strftime('%d.%m.%Y \n %H:%M')

if __name__ == "__main__":
    args = parse_args()
    
    repo_path = args.repo_path
    branch = args.branch
    n = args.n
    token = args.token

    try:  
        response = urlfetch.get('https://api.github.com/repos/jessiscript/' + repo_path + '/commits', params = {'per_page': n})
        data = json.loads(response.content)
        print(data)
        
        shas = [commit.get('sha') for commit in data]
        
        #print("The image file has a total size of " + str(data.get("image_details").get("total_bytes")) + " bytes.")

        # Extract data for plotting
        commit_dates = [format_date(commit.get('commit').get('author').get('date')) for commit in data]
        image_sizes = [get_image_size(sha) for sha in shas]


        # Create a DataFrame for Seaborn
        image_data = pd.DataFrame({"Commit Dates": list(reversed(commit_dates)), "Image Size in MB": list(reversed(image_sizes))})
        #print(image_data)

        # Set the size of the figure
        plt.figure(figsize=(15, 11))  

        # Create a Seaborn point plot
        sns.set_theme(style="darkgrid")
        sns.pointplot(x="Commit Dates", y="Image Size in MB", data=image_data)

        # Rotate x-axis labels for better readability
        if int(n) > 10 :
            plt.xticks(rotation=45)

        #plot
        plt.xlabel("Commit Dates")
        plt.ylabel("Image Size in MB")
        plt.title("Development of Native Image Sizes")

        # Save the plot as a .png file
        plt.savefig("output2_plot.png")


    except Exception as e: 
        print("The following exception returned: ", e)
        raise












