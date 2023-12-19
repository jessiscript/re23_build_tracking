import json
from matplotlib.ticker import FuncFormatter
import pygit2
import os
from datetime import datetime, timezone, timedelta
import argparse
import pandas as pd
from dateutil import parser
import matplotlib.pyplot as plt
import seaborn as sns

#Fetch graalvm-metrics refs: git fetch origin 'refs/graalvm-metrics/*:refs/graalvm-metrics/*'

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("n", help="Last n commits")

    return parser.parse_args()

def get_blob_data(n):
    return n.resolve().peel()[0].data

def get_commits(n):
    return n.resolve().peel()

def get_image_data(n):
    n = n.decode()
    n = "[" + n + "]"
    image_data = json.loads(n) 
    return image_data[0].get("image_details")

def get_build_data(repo_path, n, branch_name):
    N = n
    repo = pygit2.Repository(repo_path)
    branch = repo.branches.get(branch_name)
    if branch is None:
        raise ValueError(f"Branch " + branch_name + " not found.")

    # Iterate through the commit history of the branch
    walker = repo.walk(branch.target, pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_REVERSE)
    commits = list(walker)
    commits.reverse()

    metrics_refs = []
    metrics_commits = []
    for commit in commits:
        try:
            metrics_refs.append(repo.lookup_reference('refs/graalvm-metrics/' + str(commit.id)))
            metrics_commits.append(commit)
            n = n-1
            if n <= 0:
                break
        except KeyError as e:
            #skip as no build was created
            continue
    
    blob_data = map(get_blob_data, metrics_refs)

    # Extract data for plotting
    commit_dates = []
    for commit in metrics_commits:
        tzinfo  = timezone( timedelta(minutes=commit.author.offset) )
        dt = datetime.fromtimestamp(float(commit.author.time), tzinfo)
        timestr = dt.strftime('%d.%m.%Y \n %H:%M')
        commit_dates.append(timestr)

    raw_image_data = [get_image_data(entry) for entry in blob_data]
    image_sizes = [entry.get("total_bytes") for entry in raw_image_data if entry != 0]
    code_area_sizes = [entry.get("code_area").get("bytes") for entry in raw_image_data if entry != 0]
    image_heap_sizes = [entry.get("image_heap").get("bytes") for entry in raw_image_data if entry != 0]
    other = []
    for i in range (0, N):
        other.append(int(image_sizes[i])-int(code_area_sizes[i])-int(image_heap_sizes[i]))
    

    # Create a DataFrame for Seaborn
    image_data = pd.DataFrame({ "Commit Dates": list(reversed(commit_dates)), 
                                "Image Size": list(reversed(image_sizes)), 
                                "Code Area Size": list(reversed(code_area_sizes)),
                                "Image Heap Size": list(reversed(image_heap_sizes)),
                                "Other": list(reversed(other))})

    return image_data

    
def format_date(date):
    return parser.isoparse(date).strftime('%Y-%m-%d \n %H:%M')

if __name__ == "__main__":
    args = parse_args()
    
    repo_path = args.repo_path
    branch = args.branch
    n = args.n

    try:  
    
        image_data = get_build_data(repo_path, int(n), branch)

        print(image_data)

        n = int(n)
        
        # Formatting Y-axis tick labels to display in MB
        def format_mb(x, _):
            return f"{x:.0f} MB"
        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_mb))

        # Set the size of the figure
        plt.figure(figsize=(15, 11))  

        sns.set_theme(style="whitegrid")

        # Rotate x-axis labels for better readability
        if n > 10:
            plt.xticks(rotation=45)
        if n > 30:
            plt.xticks(rotation=90)

        # Melt the DataFrame to use 'hue' for Seaborn
        image_data_melted = pd.melt(image_data, id_vars=["Commit Dates"], var_name="Size Type", value_name="Size (MB)")

        # Create a Seaborn point plot
        sns.pointplot(x="Commit Dates", y="Size (MB)", hue="Size Type", data=image_data_melted)
        plt.xlabel("Commit Dates")
        plt.ylabel("Size in MB")
        plt.title("Development of Native Image Sizes")

        # Add vertical grid lines
        sns.despine(left=True, bottom=True)
        plt.grid(axis='x', linestyle='--', alpha=1)

        # Add a legend
        plt.legend(title="Size Type")

        # Save the plot as a .png file
        plt.savefig("output_plot.png")

    except Exception as e: 
        print("The following exception returned: ", e)
        raise












