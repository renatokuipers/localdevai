import os
import re
import json
from openai import OpenAI
import streamlit as st
import sqlite3

### Constants ###
# Local constants:#
MODEL_LOCAL = "local_model" # No specific name has to be given... 
API_KEY = "not-needed" # local models don't have an API key...
# BASE_URL = "http://localhost:1234/v1" # for local use...
BASE_URL = "http://82.170.246.151:1234/v1" # for external use..

# OpenAI constants: (these cost money!!!)#
# BASE_URL = "https://api.openai.com/v1"
# MODEL_LOCAL = "gpt-4-0125-preview"
# API_KEY = "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"

### Initializations ###
chat_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

### Initialize or update session state variables ###
if 'history' not in st.session_state:
    st.session_state['history'] = ""
if 'chunks' not in st.session_state:
    st.session_state['chunks'] = []
if 'temp_memory' not in st.session_state:
    st.session_state['temp_memory'] = ""
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""
if 'agent_output' not in st.session_state:
    st.session_state['agent_output'] = ""
if 'already_written' not in st.session_state:
    st.session_state['already_written'] = False
if 'temperature' not in st.session_state:
    temperature = 0.7
if 'current_output' not in st.session_state:
    st.session_state['current_output'] = ""
if 'completed_tasks' not in st.session_state:
    st.session_state['completed_tasks'] = []
if 'current_task' not in st.session_state:
    st.session_state['current_task'] = ""
if 'all_tasks_done' not in st.session_state:
    st.session_state['all_tasks_done'] = False
if 'output' not in st.session_state:
    st.session_state['output'] = ""
if 'action_amount' not in st.session_state:
    st.session_state['action_amount1'] = 5
if 'action_amount2' not in st.session_state:
    st.session_state['action_amount2'] = 3
if 'pressed_submit' not in st.session_state:
    st.session_state['pressed_submit'] = False
if 'task_list2' not in st.session_state:
    st.session_state["task_list2"] = []
if 'task_list' not in st.session_state:    
    st.session_state["task_list"] = []
if 'coding_task' not in st.session_state:
    st.session_state['coding_task'] = False
if 'task_list_json' not in st.session_state:
    st.session_state['task_list_json'] = []

### Classes ###
class Task:
    """Class representing a task."""
    def __init__(self, task_id, description, task_type, role):
        self.task_id = task_id
        self.description = description
        self.task_type = task_type
        self.role = role
        self.completed = False

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
        print_section_header("Task Planning...")
        history = [
            {"role": "system", "content": generate_ceo_system_message(self.user_input, st.session_state['action_amount1'])},
            {"role": "user", "content": "Now, proceed to outline your strategic plan as instructed. It's imperative that you strictly follow the provided format and guidelines for each task. This precision is essential for creating a clear, actionable plan that aligns with the goal. Let's ensure that the plan is thoughtfully structured and contributes effectively towards achieving the objective."}
        ]
        with st.chat_message("ai"):
            plan = generate_response(history, self.temperature)
            return plan

class SecondTaskPlanner:
    """Class for planning tasks."""
    
    def __init__(self, user_input, temperature, secondtaskplanner):
        self.user_input = user_input
        self.temperature = temperature
        self.second_task_planner = secondtaskplanner

    def generate_plan(self, temperature, second_task_planner):
        print_section_header("Task Planning...")
        history = [
            {"role": "system", "content": generate_subtask_planner_system_message(self.user_input, st.session_state['action_amount1'], self.second_task_planner)},
            {"role": "user", "content": "Now, proceed to outline your strategic plan as instructed. It's imperative that you strictly follow the provided format and guidelines for each subtasks. This precision is essential for creating a clear, actionable plan that aligns with the goal. Let's ensure that the plan is thoughtfully structured and contributes effectively towards achieving the objective."}
        ]
        with st.chat_message("ai"):
            plan = generate_response(history, self.temperature)
            return plan
    
class JsonFormatter:
    """Class for planning tasks."""
    
    def __init__(self, plan, temperature):
        self.user_input = plan
        self.temperature = temperature

    def reformat(self, temperature):
        print_section_header("JSON Formatting...")
        systemmessage = (
            "Your task is to accurately transform a textual plan into a structured JSON object. "
            "The plan outlines a series of tasks, each uniquely identified by 'ID', and described with 'Description', 'Type', and 'Role'. "
            "You are to create a JSON array where each element is an object representing a task. "
            "These objects must include the keys: 'ID', 'Description', 'Type', and 'Role', with their respective values derived from the plan.\n"
            "Key requirements are as follows:\n"
            "- 'ID' should be parsed as a numeric value.\n"
            "- 'Description', 'Type', and 'Role' should be treated as strings.\n"
            "- Ensure each task object is distinct and properly encapsulated within the array.\n\n"
            "For example, the plan text should be converted into a JSON format similar to the following:\n"
            "[\n"
            "{'ID': 1, 'Description1': 'Task description1', 'Type1': 'Task type1', 'Role1': 'Task role1'}\n"
            "{'ID': 2, 'Description2': 'Task description2', 'Type2': 'Task type2', 'Role2': 'Task role2'}\n"
            "]\n\n"
            "This is the plan:\n"
            f"{self.user_input}\n\n"
            "Please proceed to convert the provided plan into this JSON format with the utmost precision and care."
        )

        user_message = (
            "Please take the provided plan and convert it into a JSON format as described. "
            "Make sure to structure each task as a separate dictionary within a JSON array, "
            "adhering to the specified keys: 'ID', 'Description', 'Type', and 'Role'. "
            "It's crucial that the 'ID' is numeric, while the other fields are strings. "
            "Each task should be clearly differentiated within the array. Use the given example as a guide "
            "to achieve the correct formatting and structure. Your accuracy and attention to detail in following these instructions "
            "are vital for successfully completing this task."
        )
        history = [
            {"role": "system", "content": systemmessage},
            {"role": "user", "content": user_message}
        ]
        plan = generate_response(history, self.temperature)
        #return parse_plan_to_json(plan)
        return extract_json_from_text(plan)

class TaskExecutor:
    """Class for executing tasks."""

    def __init__(self):
        self.conn = sqlite3.connect('task_knowledge_base.db')
        self.initialize_db()

    def __del__(self):
        self.conn.close()

    def initialize_db(self):
        """Initializes the database schema if not already present."""
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS tasks (
            description TEXT NOT NULL,
            task_type TEXT NOT NULL,
            role TEXT NOT NULL,
            output TEXT,
            PRIMARY KEY (description, task_type, role)
        )
        '''
        cursor = self.conn.cursor()
        cursor.execute(create_table_query)
        self.conn.commit()

    def query_task_output(self, description, task_type, role):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT output FROM tasks 
            WHERE description=? AND task_type=? AND role=?
        ''', (description, task_type, role))
        result = cursor.fetchone()
        return result[0] if result else None

    def store_task_output(self, description, task_type, role, output):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (description, task_type, role, output) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(description, task_type, role) 
            DO UPDATE SET output=?
        ''', (description, task_type, role, output, output))
        self.conn.commit()

    def execute_task(self, task, task_list, history, temperature):
        stored_output = self.query_task_output(task.description, task.task_type, task.role)
        
        if stored_output:
            print("Using stored output for task:", task.description)
            return stored_output
        else:
            print_section_header(f"Task ID: {task.task_id}\nRole: {task.role}\nCurrent task: {task.description}")
            if st.session_state['coding_task'] == True:
                task_agent_message = generate_task_agent_system_message(
                    str(task_list), history, task.role, task.description
                )
            else:
                task_agent_message = generate_coding_task_agent_system_message(
                    str(task_list), history, task.role, task.description
                )
            history_update = [
                {"role": "system", "content": task_agent_message},
                {"role": "user", "content": "Please proceed to execute your assigned task with the guidance provided. It's imperative to closely follow the outlined instructions and criteria to ensure your work contributes effectively to the overall goal. Remember, the quality of your execution is crucial. Let's aim for excellence in completing your task."}
            ]
            response = generate_response(history_update, temperature)
            self.store_task_output(task.description, task.task_type, task.role, response)
            return response

class TaskImprover:
    """Class for improving its own output based on feedback"""

    def __init__(self):
        self.conn = sqlite3.connect('task_knowledge_base.db')
    
    def __del__(self):
        self.conn.close()

    def update_task_output(self, description, task_type, role, improved_output):
        cursor = self.conn.cursor()
        # Update the task's output in the database with the improved version
        cursor.execute('''
            INSERT INTO tasks (description, task_type, role, output) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(description, task_type, role) 
            DO UPDATE SET output=?
        ''', (description, task_type, role, improved_output, improved_output))
        self.conn.commit()

    def execute_task(self, task, task_list, history, feedback, last_output, temperature):
        print_section_header(f"Role: {task.role}\nImproving current task: {task.description}")
        if st.session_state['coding_task'] == True:
            task_agent_message = generate_task_improver_agent_system_message(
                str(task_list), history, task.role, task.description, feedback, last_output
            )
        else:
            task_agent_message = generate_coding_task_improver_agent_system_message(
                str(task_list), history, task.role, task.description, feedback, last_output
            )
        history_update = [
            {"role": "system", "content": task_agent_message},
            {"role": "user", "content": "Now, it's time to revise, refine, and enhance your last output, taking into account the specific feedback provided. This feedback is crucial for improving the quality and effectiveness of your work. Please carefully incorporate the suggestions to ensure your updated output fully aligns with the expectations."}
        ]
        response = generate_response(history_update, temperature)
        self.update_task_output(task.description, task.task_type, task.role, response)
        
        return response

class TaskReviewer:
    """Class for reviewing task outputs."""

    def review_task(self, output, task, temperature):
        print_section_header(f"Reviewing output...")
        if st.session_state['coding_task'] == True:
            reviewer_message = generate_reviewer_system_message(st.session_state['user_input'], output, task)
        else:
            reviewer_message = generate_coding_reviewer_feedback(st.session_state['user_input'], output, task)
        history = [
            {"role": "system", "content": reviewer_message},
            {"role": "user", "content": "Please proceed to provide your feedback based on the guidelines outlined mentioned before. It's crucial to strictly follow these rules to ensure the feedback is constructive and aligns with the evaluation criteria. Your insights are valuable to us, so please be thorough and precise in your assessment."}
        ]
        response = generate_response(history, temperature)
        return response

class Finalizer:
    """Class for compiling the final output."""
    
    def compile_final_output(self, file_path, temperature):
        print_section_header("Finalizing the answer...")
        content = read_from_file(file_path)
        finalizer_systemmessage = f"""
        As the Finalizer, your pivotal task is to synthesize all provided content into one singular, comprehensive output. 
        This entails integrating various components—whether they are segments of code, narrative elements, or sections of a document—into a coherent and complete final product that aligns with the project's initial goal.

        Content for Finalization:
        The content provided below represents the entirety of work produced throughout the project. 
        Your responsibility is to meticulously merge this content into a unified output that meets the specific project requirements:
        ```
        {content}
        ```

        Task Objective:
        - For a coding project, combine all code snippets and explanations into a fully functional program or system, accompanied by a cohesive documentation that explains the architecture, functionality, and usage.
        - For a narrative project, such as a story or novel, weave all narrative pieces and character developments into a fluid, engaging, and complete narrative.
        - For a document, like a Product Requirements Document (PRD), compile all sections into a well-structured, coherent document that clearly outlines the product's vision, features, and specifications.

        Expected Outcome:
        Your final output must be a polished, professional, and complete version that is ready for presentation, publication, or deployment. 
        It should:
        - Seamlessly integrate all provided content without redundancies.
        - Address the project's goals and objectives as outlined in the initial user input.
        - Be free of placeholders, incomplete thoughts, or skeletal code. Every element must contribute to the overall purpose and functionality of the project.

        Restrictions:
        - Do not introduce new concepts, functionalities, or narrative elements not already included in the provided content.
        - Avoid restructuring the core ideas or altering the project's intended direction.
        - Ensure the final output adheres to the project's theme, technical specifications, and narrative voice (where applicable).

        Your role as the Finalizer is crucial in bringing coherence and completion to the project. This final output is the culmination of all prior efforts and should reflect a deep understanding of the project's objectives and the ability to create a cohesive, impactful final product.
        """
        history = [
            {"role": "system", "content": finalizer_systemmessage},
            {"role": "user", "content": "Armed with the detailed content and precise guidelines provided, your mission now is to synthesize the final, unified output. This crucial phase is where your skills truly shine, as you blend all project elements into a seamless whole. As you embark on this task, prioritize maintaining the integrity of the original project vision, ensuring every piece of content contributes meaningfully to the end goal. Remember, your meticulous effort to integrate, refine, and polish the project's components is essential for delivering an outcome that not only meets but exceeds expectations. Your role is fundamental in turning the project's blueprint into a standout, ready-to-launch masterpiece."}
        ]
        response = generate_response(history, temperature)
        return response

### Functions ###
def generate_response(messages, temperature):
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

def generate_response_no_stream(messages, temperature):
    """Generates a response using OpenAI's API."""
    
    stream = chat_client.chat.completions.create(
        model=MODEL_LOCAL,
        messages=messages,
        stream=True,
        temperature=temperature,
    )
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
            response += chunk.choices[0].delta.content
    st.write("\n")
    return response

def generate_ceo_system_message(input_text, action_amount1):
    """Generates CEO system message based on user input."""

    return (f"""
            Your objective is to create a focused, actionable plan that directly addresses the goal: '{input_text}'. 
            This plan should outline up to {action_amount1} specific actions needed to achieve the goal, with each action being critical to the project's success. 
            These actions should be directly tied to the creation or development of the final output, ensuring a clear path to achieving the user's stated objective.

            Task Format:
            Follow this format closely when detailing each action, to ensure clarity and consistency in your plan:

            ```
            - ID: Assign a unique identifier to each action, using an integer (e.g., 1, 2, 3).
            - Description: Clearly describe the action to be taken. This description should be specific, outlining exactly what will be done to contribute to the final goal.
            - Type: Categorize the action based on its primary focus (e.g., Writing, Coding, Designing). Avoid mentioning preliminary steps like Research or Testing; focus instead on production-oriented categories.
            - Role: Define the role responsible for executing the action. This should describe a task-specific role that an agent can perform.
            ```

            Guidelines:
            - Focus on defining tasks that are essential for producing the final deliverable, whether it's a story, software, product design, etc.
            - Arrange the actions in the sequence they should be carried out, from initial development to final refinement.
            - Limit the action plan to 5 steps to ensure each is impactful and directly contributes to achieving the goal.

            This approach is designed to guide the creation of a concise, direct plan that leads to the tangible completion of the user's request.
            """
    )

def generate_subtask_planner_system_message(task_description, user_input, action_amount2):
    """Generates Subtask Planner system message."""
    
    return (
        f"Based on the goal: '{task_description}', generate a step-by-step plan for developing the goal. "
        f"The plan should include a series at a maximum of {action_amount2} subtasks, each clearly defined to contribute towards achieving this goal and in the correct order of execution. "
        "For each subtasks, STRICTLY AND ONLY provide the list in the following format and nothing else: \n"
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

    return (f"""
            You are assigned a specific role with a task that contributes to achieving the overall goal. Here's the information you need to successfully execute your task:

            1. Overall Goal: This is the ultimate objective that needs to be met.
            ```
            {st.session_state['user_input']}
            ```

            2. Full Tasklist: A comprehensive list of all tasks, providing context for where your task fits within the overall project.
            ```
            {tasklist}
            ```

            3. Previous Actions: A summary of actions previously taken, helping you understand the progression towards the overall goal.
            ```
            {history}
            ```

            4. Your Current Role: '{task_role}'. It defines your responsibilities and the scope of your actions.

            5. Your Current Task: '{task_description}'. This is the specific task you need to focus on and execute to the best of your abilities.

            Execution Guidelines:
            - Base your actions on the overall goal and, more importantly, on the specifics of your current task. It's crucial that your execution aligns closely with the task's requirements.
            - If your task involves coding, ensure that the code you produce is complete and functional, without any placeholders, TODOs, or skeleton structures. It should be production level coding.
            - If your task is to write a story or create content, aim for the highest quality, engaging and fulfilling the task's creative demands to the best of your ability.

            Your contribution is vital to the success of the overall goal. 
            Execute your task with attention to detail and a commitment to quality.
            """
    )

def generate_coding_task_agent_system_message(tasklist, history, task_role, task_description):
    """Generates a system message focused on coding/programming tasks."""

    return (f"""
            As a developer, your coding expertise is crucial for the success of our project. Here's the detailed briefing to guide your development process:

            1. Project Objective: The final goal we aim to achieve with our code.
            ```
            {st.session_state['user_input']}
            ```

            2. Task Breakdown: A detailed enumeration of all programming tasks, helping you understand how your coding task fits into the broader project.
            ```
            {tasklist}
            ```

            3. Development History: A log of previous coding efforts and commits, offering insights into the project's evolution and current state.
            ```
            {history}
            ```

            4. Your Coding Task: '{task_description}'. The specific functionality or feature you are tasked to implement or improve, with a focus on writing clean, efficient, and bug-free code.

            Coding Guidelines:
            - Ensure your code aligns with the project's overall objective and directly contributes to achieving it, paying close attention to the specifics of your assigned task.
            - Write complete and functional code, avoiding placeholders or incomplete implementations. Your code should be ready for integration into the project's codebase.
            - Maintain code quality by following best practices, including clear documentation, adherence to coding standards, and thorough testing to minimize bugs and ensure reliability.

            Your technical skills are key to advancing our project. Approach your task with precision and a commitment to crafting high-quality code.
            """
    )


def generate_task_improver_agent_system_message(tasklist, history, task_role, task_description, feedback, last_output):
    """Generates Task Improver Agent system message."""

    return (f"""
            Your role is crucial in refining the project's output to align more closely with the overall objectives. Use the information and feedback provided to enhance your last output. Here is the context and guidance for your task:

            1. Full Tasklist (For understanding where your task fits within the broader scope of the project.)
            ```
            {tasklist}
            ```

            2. Previous Actions (For reviewing the progression towards the overall goal to inform your improvements.)
            ```
            {history}
            ```

            3. Your Last Output (For reflecting on your previous submission to understand the starting point for improvements.)
            ```
            {last_output}
            ```

            4. Your Current Role: '{task_role}'. (This role defines your specific focus on improving the existing output.)

            5. Your Current Task: '{task_description}'. (This describes what aspect of your last output needs refinement or expansion.)

            6. Feedback (Utilize this targeted feedback to guide your improvements.)
            ```
            {feedback}
            ```

            Execution Guidelines:
            - Focus on addressing the feedback comprehensively, ensuring your revised output aligns more closely with the task requirements and overall goal.
            - For code tasks, ensure your improved code is functional, clean, and devoid of placeholders or incomplete segments.
            - For creative tasks, such as writing, elevate your work by enhancing its quality, depth, and engagement based on the feedback.

            Your meticulous attention to improving your work based on feedback is vital for achieving excellence in the project's outcomes.
            """
    )
    
def generate_coding_task_improver_agent_system_message(tasklist, history, task_role, task_description, feedback, last_output):
    """Generates a system message focused on improving coding/programming tasks."""

    return (f"""
            As a developer tasked with refining our codebase, your insights and improvements are key to enhancing the project's quality and functionality. Here's what you need to know to effectively upgrade your previous work:

            1. Task Breakdown: Understand the full spectrum of programming tasks to see how your improvements contribute to the larger project.
            ```
            {tasklist}
            ```

            2. Development History: Review the coding efforts and milestones achieved so far to contextualize your improvements.
            ```
            {history}
            ```

            3. Your Last Output: Reflect on the code you previously submitted to identify the basis for your enhancements.
            ```
            {last_output}
            ```

            4. Improvement Task: '{task_description}'. Specifies the enhancements, optimizations, or bug fixes you are to implement in your code.

            5. Feedback: Use this detailed feedback to precisely target your code improvements.
            ```
            {feedback}
            ```

            Improvement Guidelines:
            - Prioritize addressing the feedback with a focus on enhancing code quality, functionality, and performance to better meet the project's objectives.
            - Ensure your revised code is thoroughly tested, well-documented, and integrates seamlessly with the existing codebase, maintaining high standards for readability and maintainability.
            - Adopt a proactive approach to identifying and resolving any additional issues or inefficiencies in your code beyond the feedback provided, aiming for robust and scalable solutions.

            Your dedication to refining and perfecting the code is essential for elevating the project's overall quality and success.
            """
    )


def generate_reviewer_system_message(user_input, agent_output, task):
    """Generates Reviewer system message."""

    return (f"""
            Your role is to evaluate the provided agent output against specific criteria to ensure it meets the user's overall goal and the task's requirements. 
            
            Provided Context for Your Review:
            - User's Overall Goal: Understand the user's ultimate objective to ensure the output aligns with achieving this goal.
            ```
            {user_input}
            ```
            - Specific Task Objective: This is what the agent aimed to accomplish in response to the user's request.
            ```
            {st.session_state['current_task']}
            ```
            - Agent's Output for Review: This is the content you need to critically evaluate.
            ```
            {agent_output}
            ```

            Feedback Protocol:
            - Your feedback should focus specifically on how well the agent's output meets the evaluation criteria. Avoid suggesting revisions or providing example content. Instead, clearly identify areas of strength and areas needing improvement.
            - Only choose 1 of the following reactions:
                - Begin your feedback with '### Needs Adjustment ###' if you find areas where the output fails to meet the evaluation criteria. (Can only be once in your output)
                - Begin your feedback with '### Satisfied ###' if the output meets all criteria effectively. (Can only be once in your output)
            - If the user asks for development, coding or programming, the agent's output must be code output in the desired language!
            - Never repeat the agent's output in your answer, only provide the feedback.


            Focus your evaluation on the following aspects:
            
            1. Accuracy: Determine if the agent's output accurately addresses the user's goal and the specifics of the task.
            2. Completeness: Evaluate if the agent's output is thorough and detailed, covering all necessary aspects of the task.
            3. Relevance: Ensure all details in the agent's output are relevant and directly contribute to fulfilling the user's request. (For example: If the user says something about development, coding or programming, the agent's output should contain fully implemented code blocks in the desired language. If the user asks for a story, the agent's output should be a well designed story)
            4. Quality: Assess the overall quality of the agent's output, looking for logical errors, inconsistencies, or any omissions that might affect the output's validity.
            
            Your analysis is vital for maintaining the quality of responses provided to users.
            """)
    
def generate_coding_reviewer_feedback(user_input, agent_output, task_description):
    """Generates feedback focused on evaluating coding or programming output in relation to the user's objectives and the specific task."""

    return (f"""
            As a reviewer, your objective is to provide constructive feedback on the coding output presented by the agent, ensuring it aligns with the user's specified goal and the detailed task requirements. Here’s the basis for your feedback:

            - User’s Objective: Gauge whether the code fulfills the user's intended purpose, keeping their ultimate goal in mind.
            ```
            {user_input}
            ```
            - Task Description: Reflect on the specific coding task the agent was supposed to accomplish, ensuring the output is a direct response to this.
            ```
            {st.session_state['current_task']}
            ```
            - Agent’s Coding Output: Analyze the provided code to assess its effectiveness in meeting the task and user’s needs.
            ```
            {agent_output}
            ```

            Feedback Guidelines:
            - Structure your feedback to highlight whether the agent's coding output successfully meets the user's goal and task requirements. Start your feedback with:
                - '### Needs Adjustment ###' to indicate areas where the code falls short of the task's demands or user's expectations. Provide specific insights into what adjustments are needed. The code should NOT have placeholders, TODO's, Snippets or stubs.
                - '### Satisfied ###' if the code effectively accomplishes the user's goal and the task's specifications.
            - Focus your critique on:
                1. Accuracy: Does the code directly and effectively address the user's goal and the task's specifics?
                2. Completeness: Is the code comprehensive, including all necessary components to fulfill the task? (The code should NOT have placeholders, TODO's, Snippets or stubs.)
                3. Relevance: Does every part of the code contribute towards achieving the user's stated objective?
                4. Quality: Evaluate the code for logical coherence, absence of errors, and overall integrity to ensure high standards.

            Your detailed feedback is crucial for enhancing the quality of the coding output and ensuring it meets the user's needs and expectations.
            """)


def parse_plan_to_json(plan):
    # Enhanced pattern to capture tasks with more variability in formatting
    pattern = re.compile(
        r'(?:(?:\d+:)?\s*-?\s*ID:\s*(\d+))' +  # ID with optional numbering and hyphen
        r'(?:\s*-?\s*Description:\s*([^:]+?))?' +  # Optional Description
        r'(?:\s*-?\s*Type:\s*([^:]+?))?' +  # Optional Type
        r'(?:\s*-?\s*Role:\s*([^:\n]+))?',  # Optional Role
        re.DOTALL
    )

    tasks = []
    for match in pattern.finditer(plan):
        # Filtering empty matches if any field is optional and not present
        if match.group(1):
            task = {
                'ID': match.group(1).strip(),
                'Description': ' '.join(match.group(2).strip().split()) if match.group(2) else "",
                'Type': match.group(3).strip() if match.group(3) else "",
                'Role': match.group(4).strip() if match.group(4) else ""
            }
            tasks.append(task)

    return tasks

def extract_json_from_text(text):
    pattern = r"\{[^{}]*\}"
    json_matches = re.findall(pattern, text)
    extracted_json = []
    for match in json_matches:
        try:
            extracted_json.append(json.loads(match))
        except json.JSONDecodeError:
            pass

    # Return the extracted JSON objects
    return extracted_json

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
    if not st.session_state['already_written']:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text + "\n")
        st.session_state['already_written'] = True
    else:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(text + "\n")

def print_section_header(title):
    """Prints a section header."""
    print(f"\n{'#' * 60}")
    print(f"{title}")
    print(f"{'#' * 60}\n")

def check_if_satisfied(review_result):
    """A check if the result of the task agent is satisfactory or not."""
    adjustment_pattern = r"(###\s*)?Needs\s*Adjustment(\s*###)?"
    return not re.search(adjustment_pattern, review_result, re.IGNORECASE)

def handle_finalization_and_downloads(download_on, execution_result):
    with st.spinner("Creating the final output..."):
        with st.expander("Final Output"):
            finalizer = Finalizer()
            final_output = finalizer.compile_final_output("execution_output.txt", st.session_state['temperature'])
            task = "Armed with the detailed content and precise guidelines provided, your mission now is to synthesize the final, unified output. This crucial phase is where your skills truly shine, as you blend all project elements into a seamless whole. As you embark on this task, prioritize maintaining the integrity of the original project vision, ensuring every piece of content contributes meaningfully to the end goal. Remember, your meticulous effort to integrate, refine, and polish the project's components is essential for delivering an outcome that not only meets but exceeds expectations. Your role is fundamental in turning the project's blueprint into a standout, ready-to-launch masterpiece."

    with st.spinner("Reviewing the final output..."):
            reviewer = TaskReviewer()
            review_result = reviewer.review_task(final_output, task, st.session_state['temperature'])
            satisfied = check_if_satisfied(review_result)

            final_output = finalizer.compile_final_output("execution_output.txt", st.session_state['temperature'])
            write_to_file("final_output.txt", final_output)

    if download_on and final_output:
        st.balloons()
        st.download_button(
            label='Download full execution log',
            data=execution_result,
            file_name='execution_output.txt'
        )
        st.download_button(
            label='Download Final output',
            data=final_output,
            file_name='final_output.txt'
        )

def split_history_into_chunks(max_chunk_size=2000, overlap_size=400):
    if not st.session_state['history'] or max_chunk_size <= overlap_size:
        return st.session_state['history']

    st.session_state['chunks'] = []
    start_index = 0

    while start_index < len(st.session_state['history']):
        if start_index > 0:
            start_index -= overlap_size
        end_index = start_index + max_chunk_size
        if end_index > len(st.session_state['history']):
            end_index = len(st.session_state['history'])

        st.session_state['chunks'].append(st.session_state['history'][start_index:end_index])
        start_index += max_chunk_size

        if start_index >= len(st.session_state['history']):
            break

    return st.session_state['chunks']

def execute_and_review_task(task, task_list, executing, reviewing):
    satisfied = False

    execution_placeholder = executing.empty()
    review_placeholder = reviewing.empty()

    st.session_state['current_output'] = ""
    st.session_state['current_task'] = task.description

    if not satisfied:
        with executing:
            execution_placeholder.header("Task Execution")
            with execution_placeholder.expander(f"Task Execution:",expanded=True):
                with st.spinner("Executing task..."):
                    executor = TaskExecutor()
                    execution_result = executor.execute_task(task, task_list, st.session_state['history'], st.session_state['temperature'])
                    st.session_state['current_output'] = execution_result

        with reviewing:
            review_placeholder.header("Reviewing")
            with review_placeholder.expander(f"Reviewing output", expanded=True):
                with st.spinner("Reviewing Agent output..."):
                    reviewer = TaskReviewer()
                    review_result = reviewer.review_task(st.session_state['current_output'], task, st.session_state['temperature'])
                    satisfied = check_if_satisfied(review_result)

    while not satisfied:
        with execution_placeholder.container(border=True):
            with st.spinner(f"Adjusting Task Based on Feedback"):
                feedback = review_result
                improver = TaskImprover()
                execution_result = st.session_state['current_output'] = improver.execute_task(task, task_list, st.session_state['history'], feedback, st.session_state['current_output'], st.session_state['temperature'])
                st.session_state['current_output'] = execution_result

        with review_placeholder.container(border=True):
            with st.spinner("Reviewing Agent adjustment..."):
                reviewer = TaskReviewer()
                review_result = reviewer.review_task(st.session_state['current_output'], task, st.session_state['temperature'])
                satisfied = check_if_satisfied(review_result)
    else:
        st.success("Task execution is satisfactory based on review.")
        st.session_state['history'] += f"\n{st.session_state['current_output']}"
        write_to_file("execution_output.txt", st.session_state['current_output'])
        execution_placeholder.empty()
        review_placeholder.empty()

    # Update the 'completed_tasks' list and clear 'current_task'
    st.session_state['completed_tasks'].append(st.session_state['current_task'])
    st.session_state['current_task'] = ""
    currenttask = st.session_state['current_task']
    return currenttask

def execute_and_review_subtask(task, task_list, executing, reviewing):
    satisfied = False

    execution_placeholder = executing.empty()
    review_placeholder = reviewing.empty()

    st.session_state['current_output'] = ""
    st.session_state['current_task'] = task.description

    if not satisfied:
        with executing:
            execution_placeholder.header("Task Execution")
            with execution_placeholder.expander(f"Task Execution: {st.session_state['current_task']}",expanded=True):
                with st.spinner("Executing task..."):
                    executor = TaskExecutor()
                    execution_result = executor.execute_task(task, task_list, st.session_state['history'], st.session_state['temperature'])
                    st.session_state['current_output'] = execution_result

        with reviewing:
            review_placeholder.header("Reviewing")
            with review_placeholder.expander(f"Reviewing output", expanded=True):
                with st.spinner("Reviewing Agent output..."):
                    reviewer = TaskReviewer()
                    review_result = reviewer.review_task(st.session_state['current_output'], task, st.session_state['temperature'])
                    satisfied = check_if_satisfied(review_result)

    while not satisfied:
        with execution_placeholder.container(border=True):
            with st.spinner(f"Adjusting Task Based on Feedback for: {st.session_state['current_task']}"):
                feedback = review_result
                improver = TaskImprover()
                execution_result = st.session_state['current_output'] = improver.execute_task(task, task_list, st.session_state['history'], feedback, st.session_state['current_output'], st.session_state['temperature'])
                st.session_state['current_output'] = execution_result

        with review_placeholder.container(border=True):
            with st.spinner("Reviewing Agent adjustment..."):
                reviewer = TaskReviewer()
                review_result = reviewer.review_task(st.session_state['current_output'], task, st.session_state['temperature'])
                satisfied = check_if_satisfied(review_result)
    else:
        st.success("Task execution is satisfactory based on review.")
        st.session_state['history'] += f"\n{st.session_state['current_output']}"
        write_to_file("execution_output.txt", st.session_state['current_output'])
        execution_placeholder.empty()
        review_placeholder.empty()

    # Update the 'completed_tasks' list and clear 'current_task'
    st.session_state['completed_tasks'].append(st.session_state['current_task'])
    st.session_state['current_task'] = ""
    currenttask = st.session_state['current_task']
    return currenttask

def initialize_streamlit_ui():
    st.set_page_config(
        page_title="Local Devai",
        page_icon=":clipboard:",
        initial_sidebar_state="auto",
        layout="wide",
        menu_items={
            "About": """## Local Devai

Local Devai is an AI-powered task planner and executor designed to autonomously generate the goal that the user inputs.
With its intelligent agents, Local Devai shows the user the task planning process, shows a step-by-step execution process, and has internal reviews to ensure tasks are completed successfully.

Key Features:
- Generate task plans based on user input
- Execute tasks with intelligent agents
- Review task outputs from agents for accuracy and completeness

Local Devai simplifies complex workflows and empowers users to achieve their goals with a single input effectively. It can be seamlessly integrated with local Language Model (LLM) models such as LM Studio, LlamaCPP, or oLlama, enabling users to leverage the power of advanced language models for task planning and execution. Explore its capabilities and streamline your task management today!"""
        }
    )

def sidebar_setup():
    st.sidebar.header("Localdevai by Renjestoo.")
    output = ""
    task = ""

    if st.sidebar.button('Clear Session and Start Over', key="Clear_session"):
        st.session_state.clear()
        st.rerun()

    download_on, secondary_tasks, action_amount2, user_input, plan_tasks = handle_adjustable_settings_and_input()
    return download_on, secondary_tasks, action_amount2, user_input, plan_tasks

def handle_adjustable_settings_and_input():
    with st.sidebar.expander("Adjustable Settings", expanded=False):
        download_on = st.checkbox(label="Enable Download", value=False, disabled=False, key="download_on", help="When enabled, in the end, you will have the option to download the full log of the agents and the final output.")
        st.session_state['temperature'] = st.slider(label="Set Agent Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, key="Temperature", help="A lower value makes the program more deterministic, while a higher value will make it more creative")
        st.session_state['action_amount1'] = st.slider(label="How many tasks should the planner make?", min_value=3, max_value=15, value=5, step=1, key="Task Amount", help="This determines how many tasks there will be in the taskplan.")
        secondary_tasks = st.checkbox(label="Secondary tasks", value=False, key="secondary_task_plan", help="When enabled, the program wil create subtasks for each task in the taskplan and will execute these subtasks sequentially")

        action_amount2 = None
        if secondary_tasks:
            action_amount2 = st.session_state['action_amount2'] = st.slider(label="How many secondary tasks should the planner make?", min_value=2, max_value=5, value=3, step=1, key="Secondary Task Amount", help="This determines how many subtasks there will be created for each task in the taskplan. (This will exponentially increase the running time of the program...)")

        coding_task = st.checkbox(label="Coding run?", value=False, key="coding_run", help="When enabled, the program will focus on actually writing the code of the goal")
        if coding_task:
            st.session_state['coding_task'] = True
            coding_enabled = st.session_state['coding_task']

    with st.sidebar.expander("Input", expanded=True):
        user_input = st.text_area("# Enter your goal:", placeholder="Tell the AI what it should make (Be as descriptive as possible)")
        plan_tasks = st.button("Plan Tasks")
        st.session_state['pressed_submit'] = plan_tasks

    return download_on, secondary_tasks, action_amount2, user_input, plan_tasks

def plan_primary_tasks(user_input, temperature):
    st.header("Planning: ")
    with st.spinner("Generating task plan..."):
        with st.expander("Main Planning", expanded=False):
            task_planner = TaskPlanner(user_input, temperature)
            plan_output = task_planner.generate_plan(temperature)
            with st.spinner("Creating JSON Taskplan, please have patience..."):
                json_formatter = JsonFormatter(plan_output, temperature)
                task_list_json = json_formatter.reformat(temperature)
    return task_list_json

def plan_secondary_tasks(task_list_json, temperature, action_amount2):
    for task_info in task_list_json:
        with st.spinner(f"Generating secondary task plan for {task_info['ID']} with objective: {task_info['Description']}..."):
            with st.expander(f"Secondary Planning for task: {task_info['ID']}", expanded=False):
                second_task_planner = SecondTaskPlanner(task_info['Description'], temperature, action_amount2)
                st.session_state['task_list_json'] = second_task_planner.generate_plan(temperature, action_amount2)
                with st.spinner("Creating JSON Taskplan, please have patience..."):
                    json_formatter = JsonFormatter(st.session_state['task_list_json'], temperature)
                    formatted_secondary_tasks = json_formatter.reformat(temperature)
                task_info['subtasks'] = formatted_secondary_tasks
    return task_list_json

def visualize_task_planning(task_list_json, planning):
    for task_info in task_list_json:
        with st.sidebar.status("Current Tasks"):
            if 'subtasks' in task_info and task_info['subtasks']:
                st.header(f"Main Task: {task_info['ID']} - {task_info['Description']}")
                for subtask_info in task_info['subtasks']:
                    st.text(f"Subtask: {subtask_info['ID']} - {subtask_info['Description']}")
            else:
                st.text(f"Task: {task_info['ID']} - {task_info['Description']}")

def execute_tasks_based_on_type(task_list_json, secondary_tasks, executing, reviewing):
    if secondary_tasks:
        output = execute_and_review_subtasks(task_list_json, executing, reviewing)
    else:
        output = execute_and_review_tasks(task_list_json, executing, reviewing)
    return output

def execute_and_review_tasks(task_list_json, executing, reviewing):
    task_list = TaskList()
    placeholder_currenttask = st.empty()
    placeholder_currenttask = st.sidebar.container(border=True)

    with placeholder_currenttask:
        for index, task_info in enumerate(task_list_json):
            st.write(f"Executing Task: {task_info['ID']}")
            st.write(f"{task_info['Description']}")
            st.write(f"")
            task = Task(task_info['ID'], task_info['Description'], task_info['Type'], task_info['Role'])
            task_list.add_task(task)
            st.session_state["task_list"].append({"description": task.description, "completed": False})
            output = execute_and_review_task(task, task_list, executing, reviewing)
            st.session_state['output'] = output
            placeholder_currenttask = st.empty()
            placeholder_currenttask = st.sidebar.container(border=True)
    st.session_state['all_tasks_done'] = True

def execute_and_review_subtasks(task_list_json, executing, reviewing):
    task_list2 = TaskList()

    placeholder_currenttask = st.empty()
    placeholder_currenttask = st.sidebar.container(border=True)

    with placeholder_currenttask:
        for main_task_index, main_task_info in enumerate(task_list_json):
            if 'subtasks' in main_task_info and main_task_info['subtasks']:
                for subtask_index, subtask_info in enumerate(main_task_info['subtasks']):
                    st.write(f"Executing Subtask: {subtask_info['ID']}")
                    st.write(f"{subtask_info['Description']}")
                    st.write(f"")
                    subtask = Task(subtask_info['ID'], subtask_info['Description'], subtask_info['Type'], subtask_info['Role'])
                    task_list2.add_task(subtask)
                    st.session_state["task_list2"].append({"description": subtask.description, "completed": False})
                    output = execute_and_review_subtask(subtask, task_list2, executing, reviewing)
                    st.session_state['output'] = output
                    placeholder_currenttask = st.empty()
                    placeholder_currenttask = st.sidebar.container(border=True) 
    st.session_state['all_tasks_done'] = True

def main():
    initialize_streamlit_ui()
    download_on, secondary_tasks, action_amount2, user_input, plan_tasks = sidebar_setup()

    Planning, Execution, Finalization = st.tabs(tabs=["Planning", "Execution", "Finalization"])

    #planning, executing, reviewing = st.columns(3)

    with Planning:
        if plan_tasks:
            with st.container(border=True):
                st.session_state['task_list_json'] = plan_primary_tasks(user_input, st.session_state['temperature'])
                if secondary_tasks:
                    st.session_state['task_list_json'] = plan_secondary_tasks(st.session_state['task_list_json'], st.session_state['temperature'], action_amount2)
                st.write(st.session_state['task_list_json'])

    with Execution:
        executing, reviewing = st.columns(2)
        #visualize_task_planning(task_list_json, planning)
        execute_tasks_based_on_type(st.session_state['task_list_json'], secondary_tasks, executing, reviewing)


    with Finalization:
        if st.session_state['all_tasks_done']:
            st.balloons()
            handle_finalization_and_downloads(download_on, st.session_state['output'])

if __name__ == "__main__":
    main()
