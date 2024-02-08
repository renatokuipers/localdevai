# Local Devai: Task Planning and Execution System

Local Devai is an AI-powered application designed to streamline the process of task planning, execution, and review. Built with Streamlit and powered by OpenAI's GPT models, Local Devai enables users to input their goals and automatically generates a detailed task plan, executes these tasks with intelligent agents, and reviews the outputs to ensure quality and alignment with the initial objectives.

## Features

- **Automated Task Planning**: Generate detailed task plans based on user input, including primary and optional secondary tasks for comprehensive coverage.
- **Intelligent Task Execution**: Utilize intelligent agents to autonomously execute planned tasks, supporting both coding and general project tasks.
- **Quality Review Process**: Includes an automated review system to evaluate task outputs, ensuring they meet predefined quality standards and align with user goals.
- **Iterative Improvement**: Facilitates feedback loops, allowing for the iterative refinement of task outputs based on review outcomes.
- **Flexible Workflow**: Supports a range of tasks from coding projects to general planning and content creation, with customizable settings for task complexity and depth.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.9 or newer

### Installation

1. Clone the repository:
```bash
git clone https://github.com/renatokuipers/localdevai.git
```

2. Navigate to the project directory:
```bash
cd localdevai
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the application by running:
```bash
streamlit run localdevai.py
```
Navigate to the displayed URL in your web browser to interact with the application.

## Usage

Upon launching Local Devai, you will be greeted with a simple UI where you can input your project goal. The system then guides you through the following steps:

1. **Planning Phase**: Enter your goal and specify any additional settings related to the task complexity and execution.
2. **Task Execution**: The system autonomously generates and executes tasks based on the planning phase, with options to review and adjust tasks as needed.
3. **Finalization**: After all tasks are completed and reviewed, the final output is compiled and presented, ready for download or further action.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

Don't forget to give the project a star! Thanks again!

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- OpenAI for providing the GPT models.
- Streamlit for the interactive web application framework.
- SQLite for the database management system.
