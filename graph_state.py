from typing import List, Dict, Any, TypedDict

class AgentState(TypedDict):
    user_query: str
    plan: List[str]
    current_task_index: int
    task_results: List[Dict[str, Any]]
    feedback_history: List[Dict[str, Any]] # Stores feedback and refinement decisions
    error_count: int
    max_retries: int

if __name__ == '__main__':
    # Example of how the state might look
    initial_state: AgentState = {
        "user_query": "Book a flight to Mars and a hotel there.",
        "plan": [],
        "current_task_index": 0,
        "task_results": [],
        "feedback_history": [],
        "error_count": 0,
        "max_retries": 3
    }
    print("Initial AgentState example:")
    print(initial_state)

    initial_state["plan"] = ["book_flight_mars", "book_hotel_mars_crater_view"]
    initial_state["task_results"].append({"task": "book_flight_mars", "status": "success", "result": "Ticket to Mars confirmed."})
    initial_state["current_task_index"] = 1
    initial_state["feedback_history"].append({"task_id": 0, "feedback": "User wants window seat", "action": "re_booked_with_window_seat"})

    print("\nUpdated AgentState example:")
    print(initial_state)
