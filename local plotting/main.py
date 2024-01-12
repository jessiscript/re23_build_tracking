import argparse
from data_prep import load_data
from plot import plot_data

'''
Fetch graalvm-metrics refs: git fetch origin 'refs/graalvm-metrics/*:refs/graalvm-metrics/*'

Usage: python3 main.py [repo_path] [branch] [amount of builds] [metrics type]

Example: python3 main.py .. main 15 analysis_results
            -> creates .pdf file
Example: python3 main.py .. main 40 image_details  
            -> creates .pdf file
'''

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve native image size from last GitHub commit using setup-graalvm action.")
    parser.add_argument("repo_path", help="Path to your GitHub repository")
    parser.add_argument("branch", help="Name of the branch")
    parser.add_argument("n", help="Last n commits")
    parser.add_argument("metrics_type", help="Type of metrics from the report to be visulized. Either 'image_details', 'analysis_results', or 'resource_usage'")

    return parser.parse_args()

def main():
    args = parse_args()
    
    repo_path = args.repo_path
    branch = args.branch
    n = args.n 
    metrics_type = args.metrics_type

    if metrics_type not in ["image_details", "analysis_results", "resource_usage"]:
        print("Metrics type unknown. Valid options are 'image_details', 'analysis_results', or 'resource_usage'")
        exit()

    try:  
        n = int(n)  
        build_data = load_data(repo_path, n, branch, metrics_type)
        table_data = None
        plot_data(build_data, metrics_type, n)         

    except Exception as e: 
        print("The following exception returned: ", e)
        raise

if __name__ == "__main__":
    main()