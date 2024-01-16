import pygit2
import pandas as pd
import json
from datetime import datetime, timezone, timedelta

def get_blob_data(n):
    return n.resolve().peel()[0].data

def get_metrics(blob_data_entry, metrics_type):
    '''Returns the correct metrics part of the blob data entry.'''

    blob_data_entry = blob_data_entry.decode()
    blob_data_entry = "[" + blob_data_entry + "]"
    metrics_data = json.loads(blob_data_entry) 
    return metrics_data[0].get(metrics_type)

def load_data(repo_path, n, branch_name, metrics_type):
    '''Creates pandas data frames for visualization with plotly. Requires user's arguments.'''

    repo = pygit2.Repository(repo_path)
    branch = repo.branches.get(branch_name)
    if branch is None:
        raise ValueError(f"Branch " + branch_name + " not found.")

    # Iterate through the commit history of the branch
    walker = repo.walk(branch.target, pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_REVERSE)
    commits = list(walker)
    
    # reverse commits list to filter for the newest n commits
    commits.reverse()
    metrics_refs = []
    metrics_commits = []
    i = n
    for commit in commits:
        try:
            metrics_refs.insert(0, repo.lookup_reference('refs/graalvm-metrics/' + str(commit.id)))
            metrics_commits.insert(0, commit)
            i = i-1
            if i <= 0:
                break
        except KeyError as e:
            #skip as no build was created
            continue
    
    blob_data = map(get_blob_data, metrics_refs)

    # Extract commit dates, messages, and shas for plotting
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
        data_frame = create_image_details_data_frame(blob_data, commit_dates, commit_shas, commit_messages)
    elif metrics_type == "analysis_results":
        data_frame = create_analysis_results_data_frames(blob_data, commit_dates, commit_shas, commit_messages)
    elif metrics_type == "resource_usage":
        data_frame = create_resources_data_frame(blob_data, commit_dates, commit_shas, commit_messages)

    return data_frame

def create_image_details_data_frame(blob_data, commit_dates, commit_shas, commit_messages):
    '''Creates pandas data frame for native image details.'''

    #Filter for relevant metrics data
    raw_image_data = [get_metrics(entry, "image_details") for entry in blob_data]
    image_sizes = [entry.get("total_bytes") / 1000000 for entry in raw_image_data if entry != 0]
    code_area_sizes = [entry.get("code_area").get("bytes") / 1000000 for entry in raw_image_data if entry != 0]
    image_heap_sizes = [entry.get("image_heap").get("bytes") / 1000000 for entry in raw_image_data if entry != 0]
    other = []
    for i in range (0, len(image_sizes)):
        other.append(float(image_sizes[i])-float(code_area_sizes[i])-float(image_heap_sizes[i]))
    
    #Create and return data frame 
    return pd.DataFrame({ "Commit Date": commit_dates, 
                                "Image Size": image_sizes, 
                                "Code Area Size": code_area_sizes,
                                "Image Heap Size": image_heap_sizes,
                                "Other": other,
                                "Commit Sha": commit_shas,
                                "Commit Message": commit_messages
    })

def create_analysis_results_data_frames(blob_data, commit_dates, commit_shas, commit_messages):
    '''Returns an array of pandas data frames for the visualization of native image build analysis results.'''

    raw_analysis_results = [get_metrics(entry, "analysis_results") for entry in blob_data]
    types_data = create_single_ar_data_frame(raw_analysis_results, "types", commit_dates, commit_shas, commit_messages,)
    methods_data = create_single_ar_data_frame(raw_analysis_results, "methods", commit_dates, commit_shas, commit_messages)
    classes_data = create_single_ar_data_frame(raw_analysis_results, "classes", commit_dates, commit_shas, commit_messages)
    fields_data = create_single_ar_data_frame(raw_analysis_results, "fields", commit_dates, commit_shas, commit_messages)

    return [types_data, methods_data, classes_data, fields_data]

def create_single_ar_data_frame(analysis_results, aspect, commit_dates, commit_shas, commit_messages):
    '''Returns a single data frame. Requires the analysis_results json, the name of the aspect (types, classes, methods, fields), and the commit_dates.'''

    aspect_container = [entry.get(aspect) for entry in analysis_results]
    total = [entry.get("total") for entry in aspect_container if entry != 0]
    reflection = [entry.get("reflection") for entry in aspect_container if entry != 0]
    jni = [entry.get("jni") for entry in aspect_container if entry != 0]
    reachable = [entry.get("reachable") for entry in aspect_container if entry != 0]

    return pd.DataFrame({ "Commit Date": commit_dates, 
                            "Total": total, 
                            "Reflection": reflection,
                            "JNI": jni,
                            "Reachable": reachable,
                            "Commit Sha": commit_shas,
                            "Commit Message": commit_messages
    })

def create_resources_data_frame(blob_data, commit_dates, commit_shas, commit_messages):
    '''Creates pandas data frame for native image details.'''

    raw_resources_data = [get_metrics(entry, "resource_usage") for entry in blob_data]
    memory = [entry.get("memory") for entry in raw_resources_data if entry != 0]
    peak_rss_bytes = [entry.get("peak_rss_bytes") / 1000000 for entry in memory if entry != 0]

    gc = [entry.get("garbage_collection") for entry in raw_resources_data if entry != 0]
    gc_time = [entry.get("total_secs") for entry in gc if entry != 0]
    gc_count = [entry.get("count") for entry in gc if entry != 0]

    cpu = [entry.get("cpu") for entry in raw_resources_data if entry != 0]
    load = [entry.get("load") for entry in cpu if entry != 0]
    total_cores = [entry.get("total_cores") for entry in cpu if entry != 0]

    return pd.DataFrame({ "Commit Date": commit_dates, 
                            "GC Time": gc_time, 
                            "GC Count": gc_count,
                            "Peak RSS": peak_rss_bytes,
                            "CPU Load": load,
                            "Total Cores": total_cores,
                            "Commit Sha": commit_shas,
                            "Commit Message": commit_messages
    })