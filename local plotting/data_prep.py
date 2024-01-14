import pygit2
import pandas as pd
import json
from datetime import datetime, timezone, timedelta

def get_blob_data(n):
    return n.resolve().peel()[0].data

def get_commits(n):
    return n.resolve().peel()

def get_metrics(blob_data_entry, metrics_type):
    '''Returns the correct metrics part from the blob data entry.'''

    blob_data_entry = blob_data_entry.decode()
    blob_data_entry = "[" + blob_data_entry + "]"
    metrics_data = json.loads(blob_data_entry) 
    return metrics_data[0].get(metrics_type)

def load_data(repo_path, n, branch_name, metrics_type):
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
    commit_messages = []
    commit_shas = []
    for commit in metrics_commits:
        tzinfo  = timezone( timedelta(minutes=commit.author.offset) )
        dt = datetime.fromtimestamp(float(commit.author.time), tzinfo)
        commit_dates.append(dt.strftime('%d.%m.%y, %H:%M'))
        commit_messages.append(commit.message.strip())
        commit_shas.append(str(commit.id))
   
    data_frame = None

    if metrics_type == "image_details":
        data_frame = create_image_details_data_frame(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n)
    elif metrics_type == "analysis_results":
        data_frame = create_analysis_results_data_frames(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n)
    elif metrics_type == "resource_usage":
        data_frame = create_resources_data_frame(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n)

    return data_frame

def create_image_details_data_frame(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n):
    '''Creates pandas data frame for native image details.'''

    raw_image_data = [get_metrics(entry, metrics_type) for entry in blob_data]
    image_sizes = [entry.get("total_bytes") / 1000000 for entry in raw_image_data if entry != 0]
    code_area_sizes = [entry.get("code_area").get("bytes") / 1000000 for entry in raw_image_data if entry != 0]
    image_heap_sizes = [entry.get("image_heap").get("bytes") / 1000000 for entry in raw_image_data if entry != 0]
    other = []
    for i in range (0, n):
        other.append(float(image_sizes[i])-float(code_area_sizes[i])-float(image_heap_sizes[i]))
    

    # Create a DataFrame for Seaborn
    image_data = pd.DataFrame({ "Commit Dates": list(reversed(commit_dates)), 
                                "Image Size": list(reversed(image_sizes)), 
                                "Code Area Size": list(reversed(code_area_sizes)),
                                "Image Heap Size": list(reversed(image_heap_sizes)),
                                "Other": list(reversed(other)),
                                "Commit Sha": list(reversed(commit_shas)),
                                "Commit Message": list(reversed(commit_messages))})

    return image_data

def create_analysis_results_data_frames(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n):
    '''Returns an array of pandas data frames for the visualization of native image build analysis results.'''

    raw_analysis_results = [get_metrics(entry, metrics_type) for entry in blob_data]
    types_data = create_single_ar_data_frame(raw_analysis_results, "types", commit_dates, commit_shas, commit_messages,)
    methods_data = create_single_ar_data_frame(raw_analysis_results, "methods", commit_dates, commit_shas, commit_messages)
    classes_data = create_single_ar_data_frame(raw_analysis_results, "classes", commit_dates, commit_shas, commit_messages)
    fields_data = create_single_ar_data_frame(raw_analysis_results, "fields", commit_dates, commit_shas, commit_messages)

    analysis_results_data = [types_data, methods_data, classes_data, fields_data]

    return analysis_results_data

def create_single_ar_data_frame(analysis_results, aspect, commit_dates, commit_shas, commit_messages):
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
                                "Reachable": list(reversed(reachable)),
                                "Commit Sha": list(reversed(commit_shas)),
                                "Commit Message": list(reversed(commit_messages))
    })

def create_resources_data_frame(blob_data, commit_dates, commit_shas, commit_messages, metrics_type, n):
    '''Creates pandas data frame for native image details.'''

    raw_resources_data = [get_metrics(entry, metrics_type) for entry in blob_data]
    memory = [entry.get("memory") for entry in raw_resources_data if entry != 0]
    peak_rss_bytes = [entry.get("peak_rss_bytes") / 1000000 for entry in memory if entry != 0]

    gc = [entry.get("garbage_collection") for entry in raw_resources_data if entry != 0]
    gc_time = [entry.get("total_secs") for entry in gc if entry != 0]
    gc_count = [entry.get("count") for entry in gc if entry != 0]

    cpu = [entry.get("cpu") for entry in raw_resources_data if entry != 0]
    load = [entry.get("load") for entry in cpu if entry != 0]
    total_cores = [entry.get("total_cores") for entry in cpu if entry != 0]
    
    # Create a DataFrame for Seaborn
    return pd.DataFrame({ "Commit Dates": list(reversed(commit_dates)), 
                                "GC Time": list(reversed(gc_time)), 
                                "GC Count": list(reversed(gc_count)),
                                "Peak RSS": list(reversed(peak_rss_bytes)),
                                "CPU Load": list(reversed(load)),
                                "Total Cores": list(reversed(total_cores)),
                                "Commit Sha": list(reversed(commit_shas)),
                                "Commit Message": list(reversed(commit_messages))})