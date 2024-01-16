## How to locally plot native image build data using the cloned git repository

1) On GitHub, enable the 'Read and write permissions' under 'Workflow permissions' to ensure that the report data can be persisted (link: https://github.com/user_account/repo_name/settings/actions)

2) Make sure that the correct git repository has been cloned and that the branches of interest have been checked out

3) Depending on your platform, either run __*git fetch origin refs/graalvm-metrics/\*:refs/graalvm-metrics/\**__ or __*git fetch origin 'refs/graalvm-metrics/\*:refs/graalvm-metrics/\*'*__ on each branch to fetch all the metric references that contain the report data

4) To plot the data, make sure that you are in your cloned git repository and run:<br><br> __*py local_plotting/main.py [repo_path] [branch] [n] [metrics_type]*__<br><br> With the options being: <br> *repo_path* = relative path to local git repository<br>*branch* = name of the branch<br>*n* = last n builds to be plotted<br>*metrics_type* = Type of report metrics to be visualized. Either 'image_details', 'analysis_results', or 'resource_usage'

5) The plot should show up in the browser and a copy of the .html is safed under */local_plotting/output*

