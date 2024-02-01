import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

### Constants ###
MODEL_LOCAL = "local_model"
API_KEY = "not-needed"  
BASE_URL = "http://82.170.246.151:1234/v1"

### Initializations ###
chat_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
load_dotenv()

### Global Variables ###
history = ""
temp_memory = ""
user_input = ""
agent_output = ""
already_written = False
temperature = 0.7

### System messages ###
Custom_SystemMessage = ()

### Classes ###
class Task:
    """Class representing a task."""
    
    def __init__(self, task_id, description, task_type, role):
        self.task_id = task_id
        self.description = description
        self.task_type = task_type
        self.role = role

    def __str__(self):
        return f"ID: {self.task_id}, Description: {self.description}, Type: {self.task_type}, Role: {self.role}"

class TaskList:
    """Class representing a list of tasks."""
    
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def get_task(self, task_id):
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def __str__(self):
        return "\n".join(str(task) for task in self.tasks)

class TaskPlanner:
    """Class for planning tasks."""
    
    def __init__(self, user_input, temperature):
        self.user_input = user_input
        self.temperature = temperature

    def generate_plan(self, temperature):
        print_section_header("Task Planning")
        history = [
            {"role": "system", "content": generate_ceo_system_message(self.user_input)},
            {"role": "user", "content": self.user_input}
        ]
        with st.chat_message("ai"):
            plan = generate_response(history, self.temperature)
        return parse_plan_to_json(plan)

class TaskExecutor:
    """Class for executing tasks."""

    def execute_task(self, task, task_list, history, temperature):
        print_section_header(f"Task ID: {task.task_id}\nRole: {task.role}\nCurrent task: {task.description}")
        task_agent_message = generate_task_agent_system_message(
            str(task_list), history, task.role, task.description
        )
        history_update = [
            {"role": "system", "content": task_agent_message},
            {"role": "user", "content": task.description}
        ]
        response = generate_response(history_update, temperature)
        return response

class TaskImprover:
    """Class for improving its own output based on feedback"""

    def execute_task(self, task, task_list, history, feedback, last_output, temperature):
        print_section_header(f"Role: {task.role}\nImproving current task: {task.description}")
        task_agent_message = generate_task_improver_agent_system_message(
            str(task_list), history, task.role, task.description, feedback, last_output
        )
        history_update = [
            {"role": "system", "content": task_agent_message},
            {"role": "user", "content": feedback}
        ]
        response = generate_response(history_update, temperature)
        return response

class TaskReviewer:
    """Class for reviewing task outputs."""

    def review_task(self, output, task, temperature):
        print_section_header(f"Reviewing output...")
        reviewer_message = generate_reviewer_system_message(user_input, output, task)
        history = [
            {"role": "system", "content": reviewer_message},
            {"role": "user", "content": output}
        ]
        response = generate_response(history, temperature)
        return response

class Finalizer:
    """Class for compiling the final output."""
    
    def compile_final_output(self, file_path, temperature):
        print_section_header("Finalizing the answer...")
        content = read_from_file(file_path)
        history = [
            {"role": "system", "content": "You are a finalizer. Now, please create 1 single coherent output that uses ALL the content that is generated throughout the given content.(If the content is mainly code, show the full final code based on all the codesnippets. If the content is a story, write the full complete story based on all the content, If the content is a PRD, write the full PRD based on all the snippets, etc...). Here is the content:"},
            {"role": "user", "content": content}
        ]
        response = generate_response(history, temperature)
        return response

### Functions ###
def generate_response(messages, temperature=temperature):
    """Generates a response using OpenAI's API."""
    
    stream = chat_client.chat.completions.create(
        model=MODEL_LOCAL,
        messages=messages,
        stream=True,
        temperature=temperature,
    )
    response = ""
    response_container = st.empty()
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
            response += chunk.choices[0].delta.content
            response_container.write(response)
    st.write("\n")
    return response

def generate_ceo_system_message(input_text):
    """Generates CEO system message based on user input."""

    return (
        f"Based on the goal: '{input_text}', generate a comprehensive step-by-step plan for developing the goal. "
        "The plan should include a series at a maximum of 10 tasks, each clearly defined to contribute towards achieving this goal and in the correct order of execution. "
        "For each task, STRICTLY AND ONLY provide the list in the following format and nothing else: \n"
        "```\n"
        "- ID: A unique identifier number for the task.(single INT)\n"
        "- Description: A clear and concise explanation of what the task involves.\n"
        "- Type: Specify the category of the task.\n"
        "- Role: A role responsible for completing the task (should be a role for an agent).\n"
        "```\n"
    )

def generate_subtask_planner_system_message(task_description, user_input):
    """Generates Subtask Planner system message."""
    
    return (
        f"Based on the goal: '{task_description}', generate a step-by-step plan for developing the goal. "
        "The plan should include a series at a maximum of 5 tasks, each clearly defined to contribute towards achieving this goal and in the correct order of execution. "
        "For each task, STRICTLY AND ONLY provide the list in the following format and nothing else: \n"
        "```\n"
        "- ID: A unique identifier number for the task.(single INT)\n"
        "- Description: A clear and concise explanation of what the task involves.\n"
        "- Type: Specify the category of the task.\n"
        "- Role: A role responsible for completing the task (should be a role for an agent).\n"
        "```\n"
        f"This is the overall goal: '{user_input}'"
    )

def generate_task_agent_system_message(tasklist, history, task_role, task_description):
    """Generates Task Agent system message."""

    return (
        f"Full tasklist:\n{tasklist}\n"
        f"Previous actions:\n{history}\n\n"
        f"Current role: {task_role}\n"
        f"Current task: {task_description}\n"
        "Try to achieve the best result to the best of your abilities.\n"
        "(If the task is to create code, please only output the code and make sure that the code is fully complete without placeholders, TODO's or skeleton code).\n"
    )

def generate_task_improver_agent_system_message(tasklist, history, task_role, task_description, feedback, agentoutput):
    """Generates Task Agent system message."""

    return (
        #f"Full tasklist:\n{tasklist}\n"
        f"Previous actions:\n{history}\n\n"
        f"Your last output:\n{agentoutput}\n\n"
        f"Current role: {task_role}\n"
        f"Current task: {task_description}\n"
        f"Feedback: {feedback}\n"
        "Based on the feedback, improve and expand your last output so it will strictly adhere to the feedback.\n"
        "(If the task is to create code, please only output the code and make sure that the code is fully complete without placeholders, TODO's or skeleton code).\n"
    )

def generate_reviewer_system_message(user_input, agent_output, task):
    """Generates Reviewer system message."""

    return (
        "As a review agent with specialized skills, your task is to evaluate the output provided by another agent.\n"
        "Your analysis should be based on the following criteria:\n\n"
        "- Accuracy: Does the output accurately address the user's end goal and task list?\n"
        "- Completeness: Is the information provided in the output thorough and detailed?\n"
        "- Relevance: Are the details in the output relevant to the user's request?\n"
        "- Quality: Assess the overall quality of the content for logical errors, inconsistencies, or omissions.\n\n"
        "Here is the overall main goal the user wants to have in the end:\n"
        "~~~\n"
        f"{user_input}\n"
        "~~~\n\n"
        "This is the current objective for the agent to achieve:\n"
        "~~~\n"
        f"{task.description}\n"
        "~~~\n\n"
        "Here is the content for your review:\n"
        "~~~\n"
        f"{agent_output}\n"
        "~~~\n\n"
        "Make sure to solely focus on the task at hand with the overall goal in the back of your mind"
        "After reviewing, label your response at the beginning with either:\n"
        "- '### Needs Adjustment ###' if the output requires modifications.\n"
        "- '### Satisfied ###' if the output adequately meets the criteria.\n\n"
        "Your feedback should focus on conceptual and content-related aspects.\n"
    )

def parse_plan_to_json(plan):
    """Parses a plan string into a JSON object."""
    
    # Adjusted pattern to match various formats
    pattern = r'ID:\s*(\w+).*?Description:\s*(.*?)[,\n].*?Type:\s*(.*?)[,\n].*?Role:\s*(.*?)[,\n]'
    tasks = re.findall(pattern, plan, re.DOTALL)
    return [{'ID': id, 'Description': desc.strip(), 'Type': type.strip(), 'Role': role.strip()} for id, desc, type, role in tasks]

def get_user_goal():
    """Asks the user for their goal."""
    
    goal = input("What is your goal? ")
    os.system("cls")
    print_section_header('Main Goal:')
    print(goal)
    return goal

def read_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def write_to_file(file_path, text):
    """Writes text to a file."""
    if not already_written:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text + "\n")
    else:
        with open(file_path, 'a', encoding='utf-8') as file:
                    file.write(text + "\n")
            
def print_section_header(title):
    """Prints a section header with a specific color."""
    
    print(f"\n{'#' * 60}")
    print(f"{title}")
    print(f"{'#' * 60}\n")

def print_section_footer():
    """Prints a section footer."""
    
    print(f"\n{'#' * 60}\n")

def check_if_satisfied(review_result):
    # A check if the result of the task agent is satisfactory or not.

    adjustment_pattern = r"(###\s*)?Needs\s*Adjustment(\s*###)?"
    if re.search(adjustment_pattern, review_result, re.IGNORECASE):
        satisfied = False
    else:
        satisfied = True
    return satisfied

def handle_finalization_and_downloads(download_on):
    # Finalizer to compile final output
    with st.expander("Final Output"):
        finalizer = Finalizer()
        final_output = finalizer.compile_final_output("final_output", temperature)

    # Download buttons
    # Only display download buttons if there is content
    if download_on and final_output:
        st.balloons()
        st.download_button(
            label='Download full execution log',
            data=execution_result,
            file_name='execution_output.txt',
            mime=None,
        )
        st.download_button(
            label='Download Final output',
            data=final_output,
            file_name='final_output.txt',
            mime=None,
        )

def execute_and_review_task(task, task_list):
    global already_written
    with st.sidebar.expander("## Current Task:", expanded=True):
        st.write(f"{task.description}")
    st.subheader(f"Task: {task.description}")

    # Expander for task executor
    with st.expander(f"Executing Task: {task.description}", expanded=True):
        agent = TaskExecutor()
        with st.spinner("Executing task..."):
            execution_result = agent.execute_task(task, task_list, history, temperature)
            
    # Expander for first task reviewer
    with st.expander(f"Reviewing Task: {task.description}", expanded=True):
        reviewer = TaskReviewer()
        review_result = reviewer.review_task(execution_result, task, temperature)
        satisfied = check_if_satisfied(review_result)
        
        col1, col2 = st.columns(2)
        if not satisfied:
            st.warning("Task needs adjustment based on review feedback.")
            # Task improvement logic
            while not satisfied:
                agent = TaskImprover()
                with col1:
                    with st.spinner("Improving task based on feedback..."):
                        with st.container(border=True):
                            execution_result = agent.execute_task(task, task_list, history, review_result, execution_result, temperature)
                        
                reviewer = TaskReviewer()
                with col2:
                    with st.spinner("Reviewing the improved task..."):
                        with st.container(border=True):
                            review_result = reviewer.review_task(execution_result, task, temperature)
                satisfied = check_if_satisfied(review_result)

                if not satisfied:
                    st.warning("Further adjustment needed based on feedback.")
                else:
                    st.success("Task execution is satisfactory based on review.")

        # Write to file if the task is satisfied
        if satisfied:
            write_to_file("execution_output", execution_result)
            already_written = True  # Update the flag after first write

def main():
    global already_written, temperature
    st.set_page_config(
        page_title="Local Devai",
        page_icon=":clipboard:",
        initial_sidebar_state="auto",
        layout = "wide",
        menu_items={
            "About": (
                "## Local Devai\n\n"
                "Local Devai is an AI-powered task planner and executor designed to autonomously generate the goal that the user inputs."
                "With its intelligent agents, Local devai shows the user the task planning process, "
                "shows a step-by-step execution process, and has internal reviews to "
                "ensure tasks are completed successfully.\n\n"
                "Key Features:\n"
                "- Generate task plans based on user input\n"
                "- Execute tasks with intelligent agents\n"
                "- Review task outputs from agents for accuracy and completeness\n\n"
                "Local Devai simplifies complex workflows and empowers users to achieve their goals with a single input"
                "effectively. It can be seamlessly integrated with local Language Model (LLM) models "
                "such as LM Studio, LlamaCPP, or oLlama, enabling users to leverage the power of "
                "advanced language models for task planning and execution. Explore its capabilities "
                "and streamline your task management today!"
            )
        }
    )
    st.session_state.already_written = False  # Using session state
    with st.sidebar.expander("Adjustable Settings", expanded=False):
        download_on = st.checkbox("Enable Download", False)
        st.divider()
        temperature = st.slider("Set Agent Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, help=f"Lower values make the Agents more deterministic, meaning that that the Agents will be less creative.\nHigher values mean that the Agents will be more creative, with the possibility that the output will have lots of hallucinations.")

    with st.sidebar.expander("Input", expanded=True):
        user_input = st.text_area("# Enter your goal:", placeholder="Tell the AI what it should make (Be as descriptive as possible")
        st.divider()
        plan_tasks = st.button("Plan Tasks")

    task_status_filter = st.sidebar.selectbox("Filter tasks by status", ["All", "Pending", "Completed"],disabled=True, help="WIP")

    # Planning phase
    if plan_tasks:
        with st.expander(f"Task Planner"):
            with st.spinner("Generating task plan..."):
                task_planner = TaskPlanner(user_input, temperature)
                task_list_json = task_planner.generate_plan(temperature)

        task_list = TaskList()
        st.session_state["task_list"] = []  # Initialize task list in session state

        
        for index, task_info in enumerate(task_list_json):
            task = Task(task_info['ID'], task_info['Description'], task_info['Type'], task_info['Role'])
            task_list.add_task(task)
            st.session_state["task_list"].append({"description": task.description, "completed": False})

            if task_status_filter in ["All", "Pending"]:
                execute_and_review_task(task, task_list)  # Execute and review each task
                
        # Finalization and download buttons
        handle_finalization_and_downloads(download_on)

if __name__ == "__main__":
    main()
