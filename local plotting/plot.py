from datetime import datetime
import plotly.graph_objects as go
import plotly.subplots as sp
from dateutil import parser

def plot_data(build_data, branch, metrics_type):
    '''Creates plotly graph as html file. Requires the build data as pandas data frames as well as user's arguments.'''
    # Get current date and time
    current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Distinguish between different metrics types to be plotted
    if metrics_type == "image_details":

        fig = go.Figure()

        # Add traces for teach dataset
        fig.add_trace(go.Scatter(x=build_data["Commit Dates"], y=build_data["Image Size"], mode='markers', name='Image Size', text=build_data[["Commit Message", "Commit Sha"]].values))
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Total Image Size (MB):</b> %{y}')

        fig.add_trace(go.Scatter(x=build_data["Commit Dates"], y=build_data["Code Area Size"], mode='markers', name='Code Area Size', text=build_data[["Commit Message", "Commit Sha"]].values))
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Code Area Size (MB):</b> %{y}')

        fig.add_trace(go.Scatter(x=build_data["Commit Dates"], y=build_data["Image Heap Size"], mode='markers', name='Image Heap Size', text=build_data[["Commit Message", "Commit Sha"]].values))
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Image Heao Size (MB):</b> %{y}')

        fig.add_trace(go.Scatter(x=build_data["Commit Dates"], y=build_data["Other"], mode='markers', name='Other', text=build_data[["Commit Message", "Commit Sha"]].values))
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Other (MB):</b> %{y}')
        
        # Customize layout
        y_range = [-1, max(build_data["Image Size"]) + 1] 
        fig.update_layout(title='Native Image Size History of Branch: ' + '\'' + branch +'\'', xaxis_title='Commit Dates', yaxis_title='Size in MB', yaxis=dict(range=y_range))

        # Show the interactive plot and save to html
        fig.show()
        fig.write_html("output/image_details_" + branch + "_{}.html".format(current_datetime))
        print("Successfully created 'image_details_" + branch + "_{}.html' under local_plotting/output".format(current_datetime))

    elif metrics_type == "analysis_results":

        # Create subplot grid with 2 rows and 2 columns
        fig = sp.make_subplots(rows=2, cols=2, subplot_titles=['Types', 'Methods', 'Classes', 'Fields'])

        # Create subplots
        create_analysis_results_subplot(fig, 0, build_data)
        create_analysis_results_subplot(fig, 1, build_data)
        create_analysis_results_subplot(fig, 2, build_data)
        create_analysis_results_subplot(fig, 3, build_data)

        # Update y-axis range for each subplot
        fig.update_yaxes(range=[-300, max(build_data[0]["Total"]) + 500], row=1, col=1)
        fig.update_yaxes(range=[-3000, max(build_data[1]["Total"]) + 5000], row=1, col=2)
        fig.update_yaxes(range=[-300, max(build_data[2]["Total"]) + 500], row=2, col=1)
        fig.update_yaxes(range=[-300, max(build_data[3]["Total"]) + 500], row=2, col=2)

        # Update layout 
        fig.update_layout(title_text='Build Analysis Results of Branch: ' + '\'' + branch +'\'', yaxis_title='Amount')
        fig.show()
        fig.write_html("output/analysis_results_" + branch + "_{}.html".format(current_datetime))
  
        print("Successfully created 'analysis_results_" + branch + "_{}.html' under local_plotting/output".format(current_datetime))

    elif metrics_type == "resource_usage":
        # Create subplot grid with 2 rows and 2 columns
        fig = sp.make_subplots(rows=2, cols=2, subplot_titles=['GC Time', 'GC Count', 'Peak RSS', 'CPU Load'])

        # Create traces 
        trace1 = go.Scatter(x=build_data["Commit Dates"], y=build_data["GC Time"], mode='markers', 
                            name='GC Time', text=build_data[["Commit Message", "Commit Sha"]].values)
        trace2 = go.Scatter(x=build_data["Commit Dates"], y=build_data["GC Count"], mode='markers', 
                            name='GC Count', text=build_data[["Commit Message", "Commit Sha"]].values)
        trace3 = go.Scatter(x=build_data["Commit Dates"], y=build_data["Peak RSS"], mode='markers', 
                            name='Peak RSS', text=build_data[["Commit Message", "Commit Sha"]].values)
        trace4 = go.Scatter(x=build_data["Commit Dates"], y=build_data["CPU Load"], mode='markers', 
                            name='CPU Load', text=build_data[["Commit Message", "Commit Sha", "Total Cores"]].values)
        
        fig.add_trace(trace1, row=1, col=1)
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>GC Time (s):</b> %{y}', row=1, col=1)
        fig.add_trace(trace2, row=1, col=2)
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>GC Count:</b> %{y}', row=1, col=2)
        fig.add_trace(trace3, row=2, col=1)
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Peak RSS (MB):</b> %{y}', row=2, col=1)
        fig.add_trace(trace4, row=2, col=2)
        fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>CPU Load:</b> %{y}<br><b>Total Cores:</b> %{text[2]}', row=2, col=2)

        # Update y-axis range for each subplot
        fig.update_yaxes(range=[-0.5, max(build_data["GC Time"]) + 1], title_text="GC Time (s)", row=1, col=1)
        fig.update_yaxes(range=[-30, max(build_data["GC Count"]) + 100],title_text="GC Count", row=1, col=2)
        fig.update_yaxes(range=[-100, max(build_data["Peak RSS"]) + 100],title_text="Peak RSS (MB)", row=2, col=1)
        fig.update_yaxes(range=[-0.5, max(build_data["CPU Load"]) + 1],title_text="CPU Load", row=2, col=2)
        
        # Update layout 
        fig.update_layout(title_text='Resource Usage of Branch: ' + '\'' + branch +'\'', showlegend=False)
        fig.show()
        fig.write_html("output/resource_usage_" + branch + "_{}.html".format(current_datetime))

        print("Successfully created 'resource_usage_" + branch + "_{}.html' under local_plotting/output".format(current_datetime))

def create_analysis_results_subplot(fig, index, build_data):
    '''Create a sub plot showing the development of one native image build's analysis results aspect.'''

    # Define colors for the traces
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # Create traces 
    trace1_1 = go.Scatter(x=build_data[index]["Commit Dates"], y=build_data[index]["Total"], mode='markers', 
                          name='Total', marker=dict(color=colors[0]), text=build_data[index][["Commit Message", "Commit Sha"]].values)
    trace1_2 = go.Scatter(x=build_data[index]["Commit Dates"], y=build_data[index]["Reflection"], mode='markers', 
                          name='Reflection', marker=dict(color=colors[1]), text=build_data[index][["Commit Message", "Commit Sha"]].values)
    trace1_3 = go.Scatter(x=build_data[index]["Commit Dates"], y=build_data[index]["JNI"], mode='markers', 
                          name='JNI', marker=dict(color=colors[2]), text=build_data[index][["Commit Message", "Commit Sha"]].values)
    trace1_4 = go.Scatter(x=build_data[index]["Commit Dates"], y=build_data[index]["Reachable"], mode='markers', 
                          name='Reachable', marker=dict(color=colors[3]), text=build_data[index][["Commit Message", "Commit Sha"]].values)

    # Determine row and col given index
    row = 1 if index < 2 else 2
    col = 1 if (index % 2) == 0 else 2

    # Add traces to subplot
    fig.add_trace(trace1_1, row=row, col=col)
    fig.add_trace(trace1_2, row=row, col=col)
    fig.add_trace(trace1_3, row=row, col=col)
    fig.add_trace(trace1_4, row=row, col=col)

    # Print only legend for first subplot as all subplots share the same attributes
    if index == 0:
        fig.update_traces(showlegend=True)
    else:
        fig.update_traces(showlegend=False, row=row, col=col)

    # Add hovertemplate
    fig.update_traces(hovertemplate='<b>Commit Message:</b> %{text[0]}<br><b>Commit Sha:</b> %{text[1]}<br><b>Commit Time:</b> %{x}<br><b>Amount:</b> %{y}')