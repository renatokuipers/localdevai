# Local Devai: Advanced Task Planner and Executor

Local Devai revolutionizes task management by integrating AI-driven planning, execution, and review into a single, streamlined application. Built on Streamlit and leveraging OpenAI's cutting-edge language models, this application transforms user-defined goals into actionable plans, executes these plans through intelligent automation, and ensures output quality with a sophisticated review system.

## Key Features

- **Dynamic Task Planning**: Automates the breakdown of user-inputted goals into detailed, actionable tasks and optional sub-tasks, laying out a clear roadmap for project completion.
- **Intelligent Execution Agents**: Employs AI agents to autonomously execute tasks, adaptable for a wide range of projects including coding, content creation, and more.
- **Automated Quality Reviews**: Incorporates an AI-based review mechanism to assess task outputs, guaranteeing they meet set quality standards and perfectly align with the initial objectives.
- **Iterative Output Refinement**: Supports feedback-driven output refinement, allowing for continuous improvement based on comprehensive review feedback.
- **User-Centric Design**: Offers a simple, intuitive Streamlit-based UI that guides users through each project phase, from planning through finalization.

## Repository Contents

- `.env` - Template for environment variables, customize to configure application settings.
- `README.md` - This file, containing documentation and setup instructions.
- `execution_output.txt` - Sample file showing the output of task executions.
- `final_output.txt` - Sample file demonstrating the final, compiled output after all tasks and reviews.
- `localdevai.py` - The main Python script powering the Local Devai application.
- `requirements.txt` - A list of Python packages required to run the application.

## Getting Started

### Prerequisites

- Python 3.9+
- An internet connection for API calls to OpenAI (for local development, a model running locally can be used as well)

### Installation

1. Clone the repository to your local machine:
```bash
git clone https://github.com/renatokuipers/localdevai.git
```

2. Navigate to the Local Devai directory:
```bash
cd localdevai
```

3. Install the necessary Python packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Running Local Devai

Launch the application with Streamlit:
```bash
streamlit run localdevai.py
```
Access the application via your web browser at the URL provided by Streamlit.

## How to Use

1. **Start Local Devai**: Open the application in your browser and input your project goal in the provided text area.
2. **Task Planning**: Adjust the settings for your project's complexity and scope as needed. The system will guide you through planning, executing, and reviewing your tasks.
3. **Execution and Review**: Follow the application's prompts to review the AI-generated tasks and their execution outputs.
4. **Finalization**: Once all tasks are completed and reviewed, Local Devai compiles the final outputs for your project, ready for review and download.

## Contributing

Your contributions are welcome! If you have suggestions for improving Local Devai, please fork the repository, make your changes, and submit a pull request. You can also open issues with the tag "enhancement" for feature requests or suggestions.

## License

Local Devai is open-sourced under the MIT License. See the [LICENSE](https://github.com/renatokuipers/localdevai/blob/main/LICENSE) file in the repository for more information.

## Acknowledgments

- Thanks to OpenAI for the GPT models that power the intelligent aspects of Local Devai.
- Streamlit, for the fantastic framework that makes interactive web applications straightforward to build.
- The SQLite team, for the reliable database management system used in this project.

Start your journey with Local Devai today and transform how you approach task management and execution in your projects!
