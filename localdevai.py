import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import subprocess
import sys

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Error installing package {package}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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
    
    def __init__(self, user_input):
        self.user_input = user_input

    def generate_plan(self):
        print_section_header("Task Planning")
        history = [
            {"role": "system", "content": generate_ceo_system_message(self.user_input)},
            {"role": "user", "content": self.user_input}
        ]
        with st.chat_message("ai"):
            plan = generate_response(history)
        return parse_plan_to_json(plan)

class TaskExecutor:
    """Class for executing tasks."""

    def execute_task(self, task, task_list, history):
        print_section_header(f"Task ID: {task.task_id}\nRole: {task.role}\nCurrent task: {task.description}")
        task_agent_message = generate_task_agent_system_message(
            str(task_list), history, task.role, task.description
        )
        history_update = [
            {"role": "system", "content": task_agent_message},
            {"role": "user", "content": task.description}
        ]
        response = generate_response(history_update)
        return response

class TaskImprover:
    """Class for improving its own output based on feedback"""

    def execute_task(self, task, task_list, history, feedback, last_output):
        print_section_header(f"Role: {task.role}\nImproving current task: {task.description}")
        task_agent_message = generate_task_improver_agent_system_message(
            str(task_list), history, task.role, task.description, feedback, last_output
        )
        history_update = [
            {"role": "system", "content": task_agent_message},
            {"role": "user", "content": feedback}
        ]
        response = generate_response(history_update)
        return response

class TaskReviewer:
    """Class for reviewing task outputs."""

    def review_task(self, output, task):
        print_section_header(f"Reviewing output...")
        reviewer_message = generate_reviewer_system_message(user_input, output, task)
        history = [
            {"role": "system", "content": reviewer_message},
            {"role": "user", "content": output}
        ]
        response = generate_response(history)
        return response

class Finalizer:
    """Class for compiling the final output."""
    
    def compile_final_output(self, file_path):
        print_section_header("Finalizing the answer...")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        history = [
            {"role": "system", "content": "You are a finalizer. Now, please create 1 single coherent output that uses ALL the content that is generated throughout the given content.(If the content is mainly code, show the full final code based on all the codesnippets. If the content is a story, write the full complete story based on all the content, If the content is a PRD, write the full PRD based on all the snippets, etc...). Here is the content:"},
            {"role": "user", "content": content}
        ]
        response = generate_response(history)
        return response

### Functions ###
def generate_response(messages, temperature=0.7):
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

def write_to_file(file_path, text):
    """Writes text to a file."""
    
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


def main():
    st.set_page_config(
        page_title="Local devai",
        page_icon=":clipboard:",
        initial_sidebar_state="auto",
        menu_items={
            "About": (
                "## Local devai - Task Planner and Executor\n\n"
                "Local devai is an AI-powered task planner and executor designed to assist users "
                "in generating comprehensive task plans and executing them efficiently. With its "
                "intelligent agents, Local devai guides users through the task planning process, "
                "provides step-by-step execution instructions, and offers insightful reviews to "
                "ensure tasks are completed successfully.\n\n"
                "Key Features:\n"
                "- Generate task plans based on user input\n"
                "- Execute tasks with intelligent agents\n"
                "- Review task outputs for accuracy and completeness\n\n"
                "Local devai simplifies complex workflows and empowers users to achieve their goals "
                "effectively. It can be seamlessly integrated with local Language Model (LLM) models "
                "such as LM Studio, LlamaCPP, or oLlama, enabling users to leverage the power of "
                "advanced language models for task planning and execution. Explore its capabilities "
                "and streamline your task management today!"
            )
        }
    )


    st.title("Local Autonomous Development AI")

    user_input = st.text_area("Tell the AI what it should make:")

    if st.button("Plan Tasks", key="plan_button"):
        with st.spinner("Generating task plan..."):
            task_planner = TaskPlanner(user_input)
            task_list_json = task_planner.generate_plan()

        task_list = TaskList()
        for task_info in task_list_json:
            task = Task(task_info['ID'], task_info['Description'], task_info['Type'], task_info['Role'])
            task_list.add_task(task)

        task_progress = []

        for task in task_list.tasks:
            st.subheader(f"Task: {task.description}")

            with st.expander("Task Executor"):
                agent = TaskExecutor()
                with st.spinner("Executing task..."):
                    execution_result = agent.execute_task(task, task_list, history)
                st.code(execution_result, language='plaintext')

            with st.expander("Task Reviewer"):
                reviewer = TaskReviewer()
                with st.spinner("Reviewing task output..."):
                    review_result = reviewer.review_task(execution_result, task)
                satisfied = check_if_satisfied(review_result)

                if not satisfied:
                    st.warning("Task needs adjustment based on review feedback.")
                    agent = TaskImprover()
                    with st.spinner("Improving task based on feedback..."):
                        execution_result = agent.execute_task(task, task_list, history, review_result, execution_result)
                    with st.spinner("Reviewing adjusted output..."):
                        review_result = reviewer.review_task(execution_result, task)
                    satisfied = check_if_satisfied(review_result)

                st.success("Task execution is satisfactory based on review.")

            task_progress.append(f"Result for task: {task.description}\n######################################\n\n{execution_result}\n######################################\n\n")

        st.success("Task plan generated successfully!")

        with st.expander("Finalizer"):
            with st.spinner("Finalizing the endresult..."):
                finalizer = Finalizer()
                final_output = finalizer.compile_final_output(task_progress)

if __name__ == "__main__":
    # List of packages to install
    packages_to_install = ["openai", "python-dotenv", "colorama"]

    # Install each package
    for package in packages_to_install:
        print(f"Installing {package}...")
        install_package(package)

    print("Installation complete.")
    main()
