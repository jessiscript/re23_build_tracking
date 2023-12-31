import json
from matplotlib.ticker import FuncFormatter
import pygit2
import os
from datetime import datetime, timezone, timedelta
import argparse
import pandas as pd
from dateutil import parser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

'''
Fetch graalvm-metrics refs: git fetch origin 'refs/graalvm-metrics/*:refs/graalvm-metrics/*'

Usage: python3 LocalBuildTracking.py [repo_path] [branch] [amount of builds] [metrics type]

Example: python3 LocalBuildTracking.py . main 15 analysis_results
            -> creates .pdf file
Example: python3 LocalBuildTracking.py . main 40 image_details  
'''

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("n", help="Last n commits")
    parser.add_argument("metrics_type", help="Type of metrics from the report to be visulized. Either 'image_detail', 'analysis_results', or 'resources'")

    return parser.parse_args()

def get_blob_data(n):
    return n.resolve().peel()[0].data

def get_commits(n):
    return n.resolve().peel()

def get_image_details(blob_data_entry):
    '''Returns the image_details part from the blob data entry.'''

    blob_data_entry = blob_data_entry.decode()
    blob_data_entry = "[" + blob_data_entry + "]"
    image_data = json.loads(blob_data_entry) 
    return image_data[0].get("image_details")

def get_analysis_results(blob_data_entry):
    '''Returns the analysis_results part from the blob data entry.'''

    blob_data_entry = blob_data_entry.decode()
    blob_data_entry = "[" + blob_data_entry + "]"
    image_data = json.loads(blob_data_entry) 
    return image_data[0].get("analysis_results")

def create_image_details_data_frame(blob_data, commit_dates, n):
    '''Creates pandas data frame for native image details.'''

    raw_image_data = [get_image_details(entry) for entry in blob_data]
    image_sizes = [entry.get("total_bytes") for entry in raw_image_data if entry != 0]
    code_area_sizes = [entry.get("code_area").get("bytes") for entry in raw_image_data if entry != 0]
    image_heap_sizes = [entry.get("image_heap").get("bytes") for entry in raw_image_data if entry != 0]
    other = []
    for i in range (0, n):
        other.append(int(image_sizes[i])-int(code_area_sizes[i])-int(image_heap_sizes[i]))
    

    # Create a DataFrame for Seaborn
    image_data = pd.DataFrame({ "Commit Dates": list(reversed(commit_dates)), 
                                "Image Size": list(reversed(image_sizes)), 
                                "Code Area Size": list(reversed(code_area_sizes)),
                                "Image Heap Size": list(reversed(image_heap_sizes)),
                                "Other": list(reversed(other))})

    return image_data

def create_analysis_results_data_frames(blob_data, commit_dates, n):
    '''Returns an array of pandas data frames for the visualization of native image build analysis results.'''

    raw_analysis_results = [get_analysis_results(entry) for entry in blob_data]
    types_data = create_single_ar_data_frame(raw_analysis_results, "types", commit_dates)
    methods_data = create_single_ar_data_frame(raw_analysis_results, "methods", commit_dates)
    classes_data = create_single_ar_data_frame(raw_analysis_results, "classes", commit_dates)
    fields_data = create_single_ar_data_frame(raw_analysis_results, "fields", commit_dates)

    analysis_results_data = [types_data, methods_data, classes_data, fields_data]

    return analysis_results_data

def create_single_ar_data_frame(analysis_results, aspect, commit_dates):
    '''Returns a single data frame. Requires the analysis_results json, the name of the aspect (types, classes, methods, fields), and the commit_dates.'''

    aspect_container = [entry.get(aspect) for entry in analysis_results]
    total = [entry.get("total") for entry in aspect_container if entry != 0]
    reflection = [entry.get("reflection") for entry in aspect_container if entry != 0]
    jni = [entry.get("jni") for entry in aspect_container if entry != 0]
    reachable = [entry.get("reachable") for entry in aspect_container if entry != 0]

    return pd.DataFrame({ "Commit Dates": list(reversed(commit_dates)), 
                                "Total": list(reversed(total)), 
                                "Reflection": list(reversed(reflection)),
                                "JNI": list(reversed(jni)),
                                "Reachable": list(reversed(reachable))
    })



def create_data_frames(repo_path, n, branch_name, metrics_type):
    '''Creates pandas data frames for visualization with seaborn. Requires user's arguments.'''

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
    i = n
    for commit in commits:
        try:
            metrics_refs.append(repo.lookup_reference('refs/graalvm-metrics/' + str(commit.id)))
            metrics_commits.append(commit)
            i = i-1
            if i <= 0:
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
        timestr = dt.strftime('%d.%m.%y \n %H:%M')
        commit_dates.append(timestr)

    if metrics_type == "image_details":
        return create_image_details_data_frame(blob_data, commit_dates, n)
    elif metrics_type == "analysis_results":
        return create_analysis_results_data_frames(blob_data, commit_dates, n)

    #return create_image_details_data_frame(blob_data, commit_dates, N)
    
def generate_graph(build_data, metrics_type, n):
    '''Creates seaborn graph as .png file (image_details) or .pdf file (analysis_results). Requires the build data as pandas data frames as well as user's arguments.'''

    # Melt the DataFrame to use 'hue' for Seaborn
    if metrics_type == "image_details":

            # Formatting Y-axis tick labels to display in MB
        def format_mb(x, _):
            return f"{x:.0f} MB"
        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_mb))
        
        # Set the size of the figure
        plt.figure(figsize=(18, 11))  
        sns.set_theme(style="whitegrid")
        rotate_x_labels(n)
        
        image_data_melted = pd.melt(build_data, id_vars=["Commit Dates"], var_name="Size Type", value_name="Size (MB)")
        sns.pointplot(x="Commit Dates", y="Size (MB)", hue="Size Type", data=image_data_melted)
        plt.xlabel("Commit Dates")
        plt.ylabel("Size in MB")
        plt.title("Development of Native Image Sizes")
        sns.despine(left=True, bottom=True)
        plt.legend(title="Size Type")
        plt.grid(axis='x', linestyle='--', alpha=1)
        # Save the plot as a .png file
        plt.savefig("native_image_details.png")


    elif metrics_type == "analysis_results":
        # Create a PDF file
        with PdfPages("native_image_build_analysis_results.pdf") as pdf:
            plt.xlabel("Commit Dates")
            plt.ylabel("Amount")  
            sns.set_theme(style="whitegrid")
            create_analysis_results_subplot(pdf, 0, "Types")
            create_analysis_results_subplot(pdf, 1, "Methods")
            create_analysis_results_subplot(pdf, 2, "Classes")
            create_analysis_results_subplot(pdf, 3, "Fields")
    
def rotate_x_labels(n):
    '''Rotate x-axis labels for better readability.'''

    if n > 10:
        plt.xticks(rotation=45)
    if n > 30:
        plt.xticks(rotation=90)

def create_analysis_results_subplot(pdf, index, aspect):
    '''Create a pdf page with on seaborn line plot showing the development of one native image build's analysis results aspect.'''

    plt.figure(figsize=(18, 11))
    rotate_x_labels(n)
    image_data_melted = pd.melt(build_data[index], id_vars=["Commit Dates"], var_name=aspect, value_name="Amount")
    sns.pointplot(x="Commit Dates", y="Amount", hue=aspect, data=image_data_melted)
    plt.title("Analysis Results: " + aspect)
    sns.despine(left=True, bottom=True)
    plt.legend(title=aspect)
    plt.grid(axis='x', linestyle='--', alpha=1)
    pdf.savefig()
    plt.close()


def format_date(date):
    '''Formats the x-Axis ticks accordingly.'''

    return parser.isoparse(date).strftime('%Y-%m-%d \n %H:%M')

if __name__ == "__main__":
    args = parse_args()
    
    repo_path = args.repo_path
    branch = args.branch
    n = args.n 
    metrics_type = args.metrics_type

    if metrics_type not in ["image_details", "analysis_results", "resources"]:
        print("Metrics type unknown. Valid options are 'image_details', 'analysis_results', or 'resources'")
        exit()

    try:  
        n = int(n)  
        build_data = create_data_frames(repo_path, n, branch, metrics_type)
        print(build_data)
        generate_graph(build_data, metrics_type, n)         

    except Exception as e: 
        print("The following exception returned: ", e)
        raise












