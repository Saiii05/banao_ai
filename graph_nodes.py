from graph_state import AgentState
from agents import PlanAgent, TaskRefinerAgent, ToolAgent

# Instantiate agents globally for the nodes to use
# In a real app, these might be initialized differently (e.g., passed in, configured)
plan_agent = PlanAgent()
refiner_agent = TaskRefinerAgent()
tool_agent = ToolAgent()

def plan_generation_node(state: AgentState) -> AgentState:
    print("\n--- Executing Node: Plan Generation ---")
    user_query = state["user_query"]
    plan = plan_agent.create_plan(user_query)

    # Reset relevant parts of state for a new plan
    return {
        **state,
        "plan": plan,
        "current_task_index": 0,
        "task_results": [],
        "feedback_history": [], # Clear history for new plan
        "error_count": 0
    }

def plan_refinement_node(state: AgentState) -> AgentState:
    print("\n--- Executing Node: Plan Refinement ---")
    current_plan = state["plan"]
    # For now, feedback for refinement is minimal, could be more complex
    # e.g., based on overall progress or specific failure patterns
    feedback_for_refinement = state["feedback_history"][-1] if state["feedback_history"] else {}

    refined_plan = refiner_agent.refine_plan(list(current_plan), feedback_for_refinement.get("details"))

    # If plan changes, we might want to reset task index or handle it more gracefully
    # For now, if plan is refined, let's assume we might re-evaluate from the current task or restart.
    # This logic will be more controlled by the graph edges.
    # If the plan length changes, or tasks are reordered, current_task_index might become invalid.
    # For simplicity, if plan changes, let's reset the index. A more robust way would be to map old tasks to new ones.
    if refined_plan != current_plan:
        print("Plan was refined. Resetting current_task_index to 0.")
        state["current_task_index"] = 0 # Or adjust based on where refinement happened
        state["task_results"] = [] # Clear results if plan fundamentally changed

    return {
        **state,
        "plan": refined_plan
    }

def tool_execution_node(state: AgentState) -> AgentState:
    print("\n--- Executing Node: Tool Execution ---")
    current_task_index = state["current_task_index"]
    plan = state["plan"]

    if current_task_index >= len(plan):
        print("ToolExecutionNode: All tasks executed or index out of bounds.")
        # This case should ideally be handled by graph logic before calling the node
        return state

    task_to_execute = plan[current_task_index]
    print(f"Executing task: {task_to_execute} (Index: {current_task_index})")

    try:
        result = tool_agent.execute_task(task_to_execute)
        current_results = list(state.get("task_results", [])) # Ensure it's a list
        current_results.append(result)

        new_state = {**state, "task_results": current_results}
        if result.get("status") == "failure":
            new_state["error_count"] = state.get("error_count", 0) + 1
            print(f"Task {task_to_execute} failed. Error count: {new_state['error_count']}")
        else:
            # Reset error count on success for the current task attempt series
            new_state["error_count"] = 0
        return new_state
    except Exception as e:
        print(f"Error during tool execution for task {task_to_execute}: {e}")
        error_count = state.get("error_count", 0) + 1
        current_results = list(state.get("task_results", []))
        current_results.append({
            "task": task_to_execute,
            "status": "critical_failure",
            "result": f"Node-level error: {str(e)}"
        })
        return {**state, "task_results": current_results, "error_count": error_count}


def feedback_node(state: AgentState) -> AgentState:
    print("\n--- Executing Node: Feedback ---")
    last_result = state["task_results"][-1] if state["task_results"] else None

    if not last_result:
        print("FeedbackNode: No task result found to process.")
        # This might happen if tool execution failed critically before producing a result structure
        # Or if it's called prematurely.
        feedback_entry = {
            "task_id": state["current_task_index"],
            "feedback_content": "No actionable result from previous step.",
            "decision": "request_plan_refinement", # Or escalate error
            "details": {"error": "Missing task result"}
        }
        state["feedback_history"].append(feedback_entry)
        return state

    task_name = last_result.get("task")
    status = last_result.get("status")

    feedback_entry = {
        "task_id": state["current_task_index"],
        "task_name": task_name,
        "status": status,
        "feedback_content": "",
        "decision": "" # e.g., 'proceed', 'retry_task', 'refine_plan'
    }

    if status == "success":
        feedback_entry["feedback_content"] = f"Task {task_name} completed successfully."
        feedback_entry["decision"] = "proceed_to_next_task"
    elif status == "failure":
        feedback_entry["feedback_content"] = f"Task {task_name} failed. Result: {last_result.get('result')}"
        if state["error_count"] < state["max_retries"]:
            feedback_entry["decision"] = "retry_task"
        else:
            feedback_entry["decision"] = "request_plan_refinement" # Max retries reached
            feedback_entry["details"] = {"reason": "Max retries reached for task", "task_name": task_name}
    elif status == "critical_failure":
        feedback_entry["feedback_content"] = f"Task {task_name} failed critically. Result: {last_result.get('result')}"
        feedback_entry["decision"] = "request_plan_refinement" # Or escalate / halt
        feedback_entry["details"] = {"reason": "Critical failure in task execution", "task_name": task_name}
    else:
        feedback_entry["feedback_content"] = f"Unknown status for task {task_name}: {status}"
        feedback_entry["decision"] = "request_plan_refinement"
        feedback_entry["details"] = {"reason": "Unknown task status", "task_name": task_name}

    print(f"Feedback decision: {feedback_entry['decision']}")
    current_feedback_history = list(state.get("feedback_history", []))
    current_feedback_history.append(feedback_entry)
    return {**state, "feedback_history": current_feedback_history}

if __name__ == '__main__':
    # Test the nodes
    test_state: AgentState = {
        "user_query": "book a flight and then a hotel",
        "plan": [],
        "current_task_index": 0,
        "task_results": [],
        "feedback_history": [],
        "error_count": 0,
        "max_retries": 2
    }
    print("Initial test state:", test_state)

    # 1. Plan Generation
    state_after_planning = plan_generation_node(test_state)
    print("\nState after planning:", state_after_planning)

    # 2. Tool Execution (first task)
    state_after_tool_exec1 = tool_execution_node(state_after_planning)
    print("\nState after 1st tool exec:", state_after_tool_exec1)

    # 3. Feedback on first task
    state_after_feedback1 = feedback_node(state_after_tool_exec1)
    print("\nState after 1st feedback:", state_after_feedback1)

    # Assume first task succeeded, advance index for next test
    if state_after_feedback1["feedback_history"][-1]["decision"] == "proceed_to_next_task":
        state_after_feedback1["current_task_index"] += 1
        state_after_feedback1["error_count"] = 0 # Reset for next task

    # 4. Tool Execution (second task) - let's manually make it fail for testing retry
    # To simulate failure, we would need to control the ToolAgent's behavior or modify the state
    # For this basic test, we'll assume it might fail based on ToolAgent's randomness
    if state_after_feedback1["current_task_index"] < len(state_after_feedback1["plan"]):
        state_after_tool_exec2 = tool_execution_node(state_after_feedback1)
        print("\nState after 2nd tool exec:", state_after_tool_exec2)

        state_after_feedback2 = feedback_node(state_after_tool_exec2)
        print("\nState after 2nd feedback:", state_after_feedback2)

        # Test refinement path (if feedback suggested it)
        if state_after_feedback2["feedback_history"][-1]["decision"] == "request_plan_refinement":
            # Pass the specific feedback that triggered refinement
            # The current refiner agent doesn't use granular feedback yet.
            state_after_refinement = plan_refinement_node(state_after_feedback2)
            print("\nState after plan refinement:", state_after_refinement)
    else:
        print("\nSkipping second task execution as plan might be too short or previous task failed hard.")

    print("\n--- Node testing complete ---")
