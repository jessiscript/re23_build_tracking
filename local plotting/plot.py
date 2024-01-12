import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.ticker import FuncFormatter
from dateutil import parser
from matplotlib.backends.backend_pdf import PdfPages

def plot_data(build_data, metrics_type, n):
    '''Creates seaborn graph as pdf file. Requires the build data as pandas data frames as well as user's arguments.'''

    # Distinguish between different metrics types to be plotted
    if metrics_type == "image_details":
        
        with PdfPages("native_image_details.pdf") as pdf:
            # Formatting Y-axis tick labels to display in MB
            def format_mb(x, _):
                return f"{x:.0f} MB"
            plt.gca().yaxis.set_major_formatter(FuncFormatter(format_mb))
            
            # Set the size of the figure
            plt.figure(figsize=(18, 11))  
            sns.set_theme(style="whitegrid")
            rotate_x_labels(n)
            
            image_data_melted = pd.melt(build_data["metrics"], id_vars=["Commit Dates"], var_name="Size Type", value_name="Size (MB)")
            sns.scatterplot(x="Commit Dates", y="Size (MB)", hue="Size Type", data=image_data_melted)
            plt.xlabel("Commit Dates")
            plt.ylabel("Size in MB")
            plt.title("Development of Native Image Sizes")
            plt.ylim(bottom=0)
            sns.despine(left=True, bottom=True)
            plt.legend(title="Size Type")
            plt.grid(axis='x', linestyle='--', alpha=1)
            # Save the plot as a .png file
            pdf.savefig()
            plt.close()
            generate_table(pdf, build_data["table"])
            print("Successfully created 'native_image_details.pdf'")


    elif metrics_type == "analysis_results":
        # Create a PDF file
        with PdfPages("native_image_build_analysis_results.pdf") as pdf:
            plt.xlabel("Commit Dates")
            plt.ylabel("Amount")  
            sns.set_theme(style="whitegrid")
            create_analysis_results_subplot(pdf, 0, "Types", n, build_data["metrics"])
            create_analysis_results_subplot(pdf, 1, "Methods",n, build_data["metrics"])
            create_analysis_results_subplot(pdf, 2, "Classes",n, build_data["metrics"] )
            create_analysis_results_subplot(pdf, 3, "Fields",n, build_data["metrics"] )
            generate_table(pdf, build_data["table"])
            print("Successfully created 'native_image_build_analysis_results.pdf'")

    elif metrics_type == "resource_usage":
        
        # Create a PDF file
        with PdfPages("native_image_build_resource_usage.pdf") as pdf:    
            
            sns.set_theme(style="whitegrid")
            
            #melted_data = pd.melt(build_data[1], id_vars=["Commit Dates"], var_name="variable", value_name="value")
            # Create a figure and axis
            fig, ax1 = plt.subplots(figsize=(15, 9))
            sns.scatterplot(x="Commit Dates", y="GC Count", data=build_data["metrics"][1], color='orange', ax=ax1)
            plt.ylim(bottom=0)
            rotate_x_labels(n)
            
            # Create a second y-axis
            ax2 = ax1.twinx()
            # Plot the second dataset using the second y-axis (ax2)
            sns.scatterplot(x="Commit Dates", y="GC Time", data=build_data["metrics"][1], ax=ax2, color='blue')
           
            #Set axis labels and title
            plt.title("Garbage Collection")
            ax1.set_xlabel('Commit Dates')
            ax2.set_ylabel('GC Time (s)', color='blue')
            ax1.set_ylabel('Count', color='orange')
            # Add vertical dashed lines for each commit date
            for commit_date in build_data["metrics"][1]['Commit Dates']:
                ax1.axvline(commit_date, color='lightgrey', linestyle='--', linewidth=1)
            plt.ylim(bottom=0)
            sns.despine(left=True, bottom=True)
            plt.grid(axis='x', linestyle='--', alpha=1)
            ax1.yaxis.grid(color='orange', linewidth=0.8)
            pdf.savefig()
            plt.close()

            plt.figure(figsize=(15, 9))
            rotate_x_labels(n)
            # Formatting Y-axis tick labels to display in MB
            def format_mb(x, _):
                    return f"{x / 1e6:.0f} MB"
            ax = sns.scatterplot(x="Commit Dates", y="Peak RSS", data=build_data["metrics"][0])
            ax.yaxis.set_major_formatter(FuncFormatter(format_mb))
            plt.title("Peak RSS in MB")
            plt.ylim(bottom=0)
            sns.despine(left=True, bottom=True)
            plt.grid(axis='x', linestyle='--', alpha=1)
            pdf.savefig()
            plt.close()

            generate_table(pdf, build_data["table"])

            print("Successfully created 'native_image_build_resource_usage.png'")

def generate_table(pdf, table_data):
    fig, ax = plt.subplots(figsize=(14, 10))

    # hide axes
    fig.patch.set_visible(False)
    ax.axis('off')

    table = ax.table(cellText=table_data.values, colLabels=table_data.columns, loc='center')

    # Adjust font size
    table.auto_set_font_size(False)
    table.set_fontsize(10)  # Change the font size as needed

    # Adjust cell padding
    table.auto_set_column_width(col=list(range(len(table_data.columns))))

    fig.tight_layout()
    pdf.savefig()
    plt.close()
    
def rotate_x_labels(n):
    '''Rotate x-axis labels for better readability.'''

    if n > 10:
        plt.xticks(rotation=45)
    if n > 30:
        plt.xticks(rotation=90)

def create_analysis_results_subplot(pdf, index, aspect, n, build_data):
    '''Create a pdf page with on seaborn line plot showing the development of one native image build's analysis results aspect.'''

    plt.figure(figsize=(18, 11))
    rotate_x_labels(n)
    ar_data_melted = pd.melt(build_data[index], id_vars=["Commit Dates"], var_name=aspect, value_name="Amount")
    sns.scatterplot(x="Commit Dates", y="Amount", hue=aspect, data=ar_data_melted)
    plt.title("Analysis Results: " + aspect)
    plt.ylim(bottom=0)
    sns.despine(left=True, bottom=True)
    plt.legend(title=aspect)
    plt.grid(axis='x', linestyle='--', alpha=1)
    pdf.savefig()
    plt.close()


def format_date(date):
    '''Formats the x-Axis ticks accordingly.'''

    return parser.isoparse(date).strftime('%Y-%m-%d \n %H:%M')