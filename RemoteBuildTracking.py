import json
import urlfetch
import base64
import re
import pytz
import argparse
import pandas as pd
from dateutil import parser
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import seaborn as sns

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("owner", help="Username of the GitHub repository owner")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("token", help="Your personal access token")
    parser.add_argument("n", nargs="?", default="10", help="Last n commits (default is 10)") 

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

def get_image_data(commit_sha):
    data = get_response('https://api.github.com/repos/' + owner + '/' + repo_path + '/git/ref/graalvm-metrics/' + commit_sha, token)
    if data != None:
        ref_sha = data.get("object").get("sha")
    else:
        return [0, 0, 0]

    data = get_response('https://api.github.com/repos/' + owner + '/' + repo_path + '/git/trees/' + ref_sha, token)
    if data != None:
        blob_sha = data.get("tree")[0].get("sha")
    else:
        return [0, 0, 0]

    data = get_response('https://api.github.com/repos/' + owner + '/' + repo_path + '/git/blobs/' + blob_sha, token)
    if data != None:
        content = base64.b64decode(data.get("content"))
        data = json.loads(content)
        return [data.get("image_details").get("total_bytes") / 1e6, 
                data.get("image_details").get("code_area").get("bytes") / 1e6,
                data.get("image_details").get("image_heap").get("bytes") / 1e6]
    else:
        return [0, 0, 0]
    
def format_date(date):
    # Parse the timestamp and convert it to the desired timezone
    commit_time = parser.isoparse(date)
    commit_time_utc = commit_time.replace(tzinfo=pytz.utc)
    desired_timezone = pytz.timezone('Europe/Berlin')
    commit_time_local = commit_time_utc.astimezone(desired_timezone)
    return commit_time_local.strftime('%d.%m.%Y \n %H:%M')

if __name__ == "__main__":
    args = parse_args()
    
    owner = args.owner
    repo_path = args.repo_path
    branch = args.branch
    n = args.n
    token = args.token

    if not n.isnumeric():
        print("Wrong use: n should be a number")
        exit(1)
    else:
        n = int(n)

    try:  

        response = urlfetch.get('https://api.github.com/repos/' + owner + '/' + repo_path + '/events', headers={
            "Authorization": "Bearer " + token
        })
        link_header = response.headers.get("link")
        response_json = json.loads(response.content)
        commits_left = n
        push_events = []

        for event in response_json:
            if commits_left <= 0:
                break
            if event["type"] == "PushEvent" and event["payload"]["ref"] == ("refs/heads/" + branch):
                push_events.append(event)
                commits_left = commits_left-1

        # Check for pagination
            link_header = response.headers.get("link")
            next_page_match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)

        while link_header and "rel=\"next\"" in link_header and commits_left > 0:
            # Extract the URL for the next page
            next_page_url = next_page_match.group(1)

            # Make the request for the next page
            response = urlfetch.fetch(next_page_url, headers={
                "Authorization": "Bearer " + token
            })
            response_json = json.loads(response.content)

            for event in response_json:
                if commits_left <= 0:
                    break
                if event["type"] == "PushEvent" and event["payload"]["ref"] == ("refs/heads/" + branch):
                    push_events.append(event)
                    commits_left = commits_left-1

            # Update the next_page_match for the next iteration
            link_header = response.headers.get("link")
            next_page_match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)

        # Prepare data
        timestamps = []
        shas = []
        for push_event in push_events:
            timestamps.append(push_event.get("created_at"))
            shas.append(push_event.get("payload").get("commits")[-1].get("sha"))

        # Extract data for plotting
        commit_dates = [format_date(timestamp) for timestamp in timestamps]
        image_data = [get_image_data(sha) for sha in shas]
        #print(image_data)
        image_sizes = [entry[0] for entry in image_data if entry != 0]
        code_area_sizes = [entry[1] for entry in image_data if entry != 0]
        image_heap_sizes = [entry[2] for entry in image_data if entry != 0]

        # Create a DataFrame for Seaborn
        image_data = pd.DataFrame({"Commit Dates": list(reversed(commit_dates)), 
                                   "Image Size (MB)": list(reversed(image_sizes)), 
                                   "Code Area Size (MB)": list(reversed(code_area_sizes)),
                                   "Image Heap Size (MB)": list(reversed(image_heap_sizes))})

        # Formatting Y-axis tick labels to display in MB
        def format_mb(x, _):
            return f"{x:.0f} MB"
        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_mb))

        # Set the size of the figure
        plt.figure(figsize=(15, 11))  

        # Rotate x-axis labels for better readability
        if n > 10:
            plt.xticks(rotation=45)

        # Create a Seaborn point plot
        sns.set_theme(style="darkgrid")
        sns.pointplot(x="Commit Dates", y="Image Size (MB)", data=image_data)
        sns.pointplot(x="Commit Dates", y="Code Area Size (MB)", data=image_data)
        sns.pointplot(x="Commit Dates", y="Image Heap Size (MB)", data=image_data)
        plt.xlabel("Commit Dates")
        plt.ylabel("Image Size in MB")
        plt.title("Development of Native Image Sizes")

        # Save the plot as a .png file
        plt.savefig("output_plot.png")


    except Exception as e: 
        print("The following exception returned: ", e)
        raise












