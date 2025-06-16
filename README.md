# LangGraph Agentic Workflow

This project demonstrates a basic agentic workflow built using LangGraph in Python. It showcases how to orchestrate multiple agents (PlanAgent, TaskRefinerAgent, ToolAgent) to process a user query through planning, execution, and refinement stages, including a feedback loop.

## Features

*   **Modular Agent Design**: Separate classes for planning, task refinement, and tool execution.
*   **Dynamic Planning**: A `PlanAgent` splits a user query into sub-tasks.
*   **Iterative Refinement**: A `TaskRefinerAgent` modifies the plan based on feedback or predefined logic.
*   **Simulated Tool Use**: A `ToolAgent` mimics the execution of tasks, returning success or failure.
*   **Feedback Loop**: The system can re-check results and re-run tasks or refine the plan if needed.
*   **LangGraph Orchestration**: Uses LangGraph to define and run the workflow as a state machine.
*   **Error Handling**: Basic error counting and retry mechanisms for tasks.
*   **Command-Line Interface**: Accepts user queries via the command line.

## File Structure

*   `agents.py`: Contains the definitions for `PlanAgent`, `TaskRefinerAgent`, and `ToolAgent`. These simulate the core logic of different agent capabilities.
*   `graph_state.py`: Defines the `AgentState` TypedDict, which represents the shared state passed between nodes in the LangGraph.
*   `graph_nodes.py`: Implements the functions that act as nodes in the LangGraph (e.g., `plan_generation_node`, `tool_execution_node`). These functions use the agents to modify the state.
*   `main_graph.py`: Sets up the LangGraph, defines the edges and conditional logic between nodes, compiles the graph, and provides the main entry point to run the workflow from a user query.

## Dependencies

This project primarily uses LangGraph. You'll need Python 3.8+ installed.

To install the necessary Python packages, run:

```bash
pip install langgraph langchain-core
```
*(`langchain-core` is a peer dependency of `langgraph`)*

You might also want to install `pygraphviz` and `matplotlib` if you wish to generate a visual representation of the graph (the code for this is commented out in `main_graph.py`):
```bash
# Optional, for graph visualization
pip install pygraphviz matplotlib
```

## How to Run

You can run the agentic workflow from your terminal using the `main_graph.py` script.

1.  Navigate to the project directory in your terminal.
2.  Run the script with a user query as an argument:

    ```bash
    python main_graph.py "your user query here"
    ```

    For example:
    ```bash
    python main_graph.py "I need to book a flight and then reserve a hotel room."
    ```
    Or to test a scenario that might involve retries or refinement:
    ```bash
    python main_graph.py "book a hotel and then verify everything"
    ```

3.  **Command-line options**:
    *   `user_query` (required): The query for the agent system to process.
    *   `--max_retries <number>` (optional): Set the maximum number of retries for a failing task. Defaults to 2.
        ```bash
        python main_graph.py "book a car" --max_retries 1
        ```
    *   `--no_stream` (optional): Disable live event streaming for a cleaner final output. The detailed logs from agents and nodes will still print, but the per-event state dump will be skipped.
        ```bash
        python main_graph.py "plan a trip to the moon" --no_stream
        ```

## Workflow Overview

1.  **Input**: The workflow starts with a `user_query` provided via the CLI.
2.  **Plan Generation (`plan_generator` node)**: The `PlanAgent` takes the query and creates an initial list of tasks.
3.  **Plan Refinement (`plan_refiner` node)**: The `TaskRefinerAgent` reviews the plan. It can add, modify, or remove tasks. This step is always called after initial planning and can be revisited if tasks fail critically or feedback suggests a need for replanning.
4.  **Tool Execution (`tool_executor` node)**: For each task in the (refined) plan, the `ToolAgent` attempts to execute it. The agent simulates success or failure.
5.  **Feedback Processing (`feedback_processor` node)**: After each task execution, this node evaluates the outcome:
    *   **Success**: If the task succeeded, the workflow moves to the next task or ends if all tasks are done.
    *   **Failure**: If the task failed, the system checks the `error_count`.
        *   If `error_count` < `max_retries`, the task is sent back to the `tool_executor` node for another attempt.
        *   If `error_count` >= `max_retries`, the failure is deemed significant, and the workflow is routed back to the `plan_refiner` node to potentially alter the plan or handle the persistent failure.
6.  **Loop/End**: The workflow continues executing tasks, getting feedback, and potentially refining the plan until all tasks are successfully completed or a terminal condition (like an unrecoverable error or empty plan) is met. The final state, including all task results and feedback, is then printed.

This iterative process allows the system to adapt to challenges and attempt to fulfill the user's query robustly.
