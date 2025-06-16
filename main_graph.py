from langgraph.graph import StateGraph, END
from graph_state import AgentState
from graph_nodes import (
    plan_generation_node,
    plan_refinement_node,
    tool_execution_node,
    feedback_node
)

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("plan_generator", plan_generation_node)
workflow.add_node("plan_refiner", plan_refinement_node)
workflow.add_node("tool_executor", tool_execution_node)
workflow.add_node("feedback_processor", feedback_node)

# Set entry point
workflow.set_entry_point("plan_generator")

# Define edges

# After plan generation, go to refinement
workflow.add_edge("plan_generator", "plan_refiner")

# After plan refinement, decide where to go
def decide_after_refinement(state: AgentState) -> str:
    print("\n--- डिसीजन: After Plan Refinement ---")
    if not state["plan"] or state["current_task_index"] >= len(state["plan"]):
        print("Decision: Plan is empty or complete after refinement. Ending workflow.")
        return END # Or a specific "finalize_node"
    print(f"Decision: Plan has tasks. Proceeding to execute task at index {state['current_task_index']}.")
    return "tool_executor"

workflow.add_conditional_edges(
    "plan_refiner",
    decide_after_refinement,
    {
        "tool_executor": "tool_executor",
        END: END
    }
)

# After tool execution, always go to feedback processing
workflow.add_edge("tool_executor", "feedback_processor")

# After feedback processing, decide the next step
def decide_after_feedback(state: AgentState) -> str:
    print("\n--- डिसीजन: After Feedback ---")
    if not state["feedback_history"]:
        print("Decision: No feedback history. Critical error or unexpected state. Ending.")
        return END # Should not happen in normal flow

    last_feedback = state["feedback_history"][-1]
    decision = last_feedback.get("decision")
    print(f"Feedback decision from state: {decision}")

    if decision == "proceed_to_next_task":
        state["current_task_index"] += 1 # Move to next task
        state["error_count"] = 0 # Reset error count for the new task
        if state["current_task_index"] < len(state["plan"]):
            print(f"Decision: Proceeding to next task at index {state['current_task_index']}.")
            return "tool_executor"
        else:
            print("Decision: All tasks completed successfully.")
            return END
    elif decision == "retry_task":
        # error_count should have been incremented by tool_executor or feedback_node
        print(f"Decision: Retrying current task at index {state['current_task_index']}. Error count: {state['error_count']}.")
        return "tool_executor" # Retry the same task
    elif decision == "request_plan_refinement":
        print(f"Decision: Requesting plan refinement. Current task index: {state['current_task_index']}.")
        # Optionally reset error_count here if refinement should give a fresh start for retries
        # state["error_count"] = 0
        return "plan_refiner"
    else:
        print(f"Decision: Unknown feedback decision ('{decision}'). Ending workflow as a fallback.")
        return END # Fallback for unknown decisions

workflow.add_conditional_edges(
    "feedback_processor",
    decide_after_feedback,
    {
        "tool_executor": "tool_executor",
        "plan_refiner": "plan_refiner",
        END: END
    }
)

# Compile the graph
app = workflow.compile()

import argparse
import json # For pretty printing the final state

# (Keep existing imports and graph definition above this block)

def run_workflow(user_query: str, max_retries: int = 2, stream_events: bool = True):
    print(f"\n--- Initializing Workflow for Query: '{user_query}' (Max Retries: {max_retries}) ---")
    initial_config = {"user_query": user_query, "max_retries": max_retries}

    final_state_at_end = None # To capture the state when END is reached

    if stream_events:
        print("\n--- Streaming Workflow Events ---")
        for event in app.stream(initial_config):
            for key, value in event.items():
                print(f"--- Event from Node: {key} ---")
                # value is the full state after this node's execution
                # We're interested in the final state when the graph reaches END
                if key == END: # LangGraph convention for final state
                    final_state_at_end = value
                    print("Workflow has reached END.")
                else:
                    # You can print selective parts of 'value' if it's too verbose
                    print(f"Current plan: {value.get('plan')}")
                    if value.get('task_results'):
                        print(f"Last task result: {value['task_results'][-1]}")
                    if value.get('feedback_history'):
                        print(f"Last feedback: {value['feedback_history'][-1]}")
                print("--------------------")
    else:
        # Non-streaming invocation, gets the final state directly
        print("\n--- Running Workflow (Non-Streaming) ---")
        # The invoke method returns the final state(s) when the graph reaches END.
        # If multiple branches can reach END, it might be a list.
        # For our setup, it's usually the state of the last node that led to END.
        # However, the 'stream' method with capturing END event is more explicit for final state.
        # Let's use 'invoke' which returns the dictionary of outputs of the END node.
        # If END is the terminal node, the output is the final state of the graph.
        final_state_at_end = app.invoke(initial_config)


    print("\n--- Workflow Execution Complete ---")

    if final_state_at_end:
        print("\n--- Final Workflow State ---")
        # Pretty print the dictionary
        print(json.dumps(final_state_at_end, indent=2))

        print("\n--- Summary ---")
        print(f"User Query: {final_state_at_end.get('user_query')}")
        final_plan = final_state_at_end.get('plan', [])
        print(f"Final Plan: {final_plan}")

        task_results = final_state_at_end.get('task_results', [])
        if task_results:
            print("Task Results:")
            for i, res in enumerate(task_results):
                # Check if the task index is within the bounds of the final plan
                task_name_in_plan = final_plan[i] if i < len(final_plan) else "N/A (task may have been removed)"
                # The result itself also contains the task name
                print(f"  - Task (from plan): {task_name_in_plan}, Task (from result): {res.get('task')}, Status: {res.get('status')}, Result: \"{res.get('result')}\"")
        else:
            print("No task results recorded.")

        # Check if all tasks in the final plan were successful
        if final_plan and task_results and len(task_results) == len(final_plan) and all(r['status'] == 'success' for r in task_results):
            print("\nOutcome: All tasks in the final plan completed successfully.")
        elif not final_plan:
            print("\nOutcome: The plan was empty or became empty.")
        else:
            print("\nOutcome: Not all tasks completed successfully or plan/results mismatch.")

    else:
        print("No final state captured. The workflow might not have reached an END state properly or was interrupted.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run an agentic workflow using LangGraph.")
    parser.add_argument("user_query", type=str, help="The user query to process.")
    parser.add_argument("--max_retries", type=int, default=2, help="Maximum number of retries for a failing task.")
    parser.add_argument("--no_stream", action="store_true", help="Disable event streaming for a cleaner final output.")

    args = parser.parse_args()

    print("Compiling the graph...")
    # Optional: Visualization code (commented out as it adds dependencies)
    # try:
    #     img_bytes = app.get_graph().draw_mermaid_png()
    #     with open("graph.png", "wb") as f: f.write(img_bytes)
    #     print("Graph visualization saved to graph.png (requires `pip install pygraphviz matplotlib`)")
    # except Exception as e:
    #     print(f"Could not generate graph visualization: {e}")
    print("Graph compiled.")

    run_workflow(args.user_query, args.max_retries, stream_events=not args.no_stream)
