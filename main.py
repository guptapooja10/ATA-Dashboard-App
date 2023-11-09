import streamlit as st
from google.cloud import firestore
import json
import datetime as dt
from streamlit_calendar import calendar
from google.oauth2 import service_account

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("ata-firestore-key-dashboard.json")

st.set_page_config(page_title="ATA-Dashboard-App",layout="wide")
st.write("### Welcome to the ATA-Dashboard-App")
st.markdown("* Use the sidebar for Overall Project Data *")
# Sidebar
st.sidebar.title("Project Overview")

st.header("Project Status App")

# Create a reference to the projects
project_ref = db.collection("projects")
projects = list(project_ref.stream())  # Fetch data once and convert to a list

project_name_list = []

for project in projects:
    project_data = project.to_dict()
    project_name = project_data.get("name")
    project_name_list.append(project_name)

selected_project = st.selectbox("Select a project", project_name_list)

# Get details of the selected project
selected_project_query = project_ref.where("name", "==", selected_project).stream()

# Calculate progress for all projects
total_completed_tasks = 0
total_num_tasks = 0
total_projects = len(projects)
# Display overall progress in the sidebar
st.sidebar.subheader("Overall Progress")
st.sidebar.metric("Total Number of Projects", total_projects)
for proj in projects:
    project_data = proj.to_dict()
    total_completed_tasks += project_data.get("num_completed_tasks",0)
    total_num_tasks += project_data.get("num_tasks",0)

# Calculate delta
delta = total_num_tasks - total_completed_tasks
st.sidebar.metric(
    "Total Completed Tasks",
    total_completed_tasks,
    total_num_tasks, delta_color="normal"
)
# Calculate progress ratio
progress_ratio = total_completed_tasks / total_num_tasks
# Display total completed tasks as a progress bar in the sidebar
st.sidebar.write(f"Over Progress Ratio: {progress_ratio * 100:.2f}%")
st.sidebar.write(f"Total Tasks Delta: {delta}")

for proj in selected_project_query:
    selected_project_data = proj.to_dict()

    # Project data
    current_progress_ratio = selected_project_data.get("current_progress_ratio")
    num_completed_tasks = selected_project_data.get("num_completed_tasks")
    num_tasks = selected_project_data.get("num_tasks")
    project_name = selected_project_data.get("name")

    starting_date = (selected_project_data.get("starting_date").date())
    target_date = (selected_project_data.get("target_date").date())
    current_expected_date = (selected_project_data.get("current_expected_date").date())

    # st.write(selected_project_data)
    st.title(project_name)

    st.divider()
    # Progress visualization
    bar_column, ratio_column, task_ratio_column = st.columns([4, 1, 1])
    with bar_column:
        my_bar = st.progress(current_progress_ratio, text="Project Progress")
    with ratio_column:
        st.metric(label="Progress Ratio", value=current_progress_ratio)
    with task_ratio_column:
        st.metric(label="Completed Tasks", value=f"{num_completed_tasks}/{num_tasks}")

    st.divider()

    schedule_deviation = current_expected_date - target_date

    if int(schedule_deviation.days) > 0:
        current_timeline_color = "#FF0000"
    else:
        current_timeline_color = "#5DBB63"

    timeline_column, deviation_column = st.columns([4, 2])
    with timeline_column:
        if int(schedule_deviation.days) > 0:
            st.error(
                f"Start date: {starting_date} \n\n End date: {target_date} \n\n Expected End date:  {current_expected_date}")
        else:
            st.success(
                f"Start date: {starting_date} \n\n End date: {target_date} \n\n Expected End date:  {current_expected_date}")
    with deviation_column:
        st.metric(label="Current End date", value=str(current_expected_date), delta=int(schedule_deviation.days),
                  delta_color="inverse")

    st.divider()
    # Create a selection widget for the calendar view
    selected_view = st.selectbox("Select Calendar View", ["timeline", "multiMonthYear"])
    if selected_view == "timeline":
        calendar_options = {
            "headerToolbar": {
                "left": "today,prev,next",
                "center": "title",
                "right": "timelineDay,timelineWeek,timelineMonth,timelineYear",
            },
            "initialView": "timelineMonth",
            "resourceGroupField": "project",
            "resources": [
                {"id": "expected_timeline",
                 "project": project_name,
                 "title": "Expected Timeline", },
                {"id": "current_timeline",
                 "project": project_name,
                 "title": "Current Timeline", },
                {"id": "events",
                 "project": project_name,
                 "title": "Events", },
            ],
        }
    else:
        calendar_options = {
            "headerToolbar": {
                "left": "today,prev,next",
                "center": "title",
                "right": "multiMonthYear",
            },
            "initialView": "multiMonthYear",
            "resourceGroupField": "project",
            "resources": [
                {"id": "expected_timeline",
                 "project": project_name,
                 "title": "Expected Timeline", },
                {"id": "current_timeline",
                 "project": project_name,
                 "title": "Current Timeline", },
                {"id": "events",
                 "project": project_name,
                 "title": "Events", },
            ],
        }
    calendar_events = [
        {
            "title": "Expected project timeline",
            "start": str(starting_date),
            "end": str(target_date),
            "resourceId": "expected_timeline",
        },
        {
            "title": "Current project timeline",
            "start": str(starting_date),
            "end": str(current_expected_date),
            "resourceId": "current_timeline",
            "color": current_timeline_color
        },
    ]
    # Display the calendar using streamlit_calendar
    st.title("Project Calendar")
    calendar = calendar(events=calendar_events, options=calendar_options)
