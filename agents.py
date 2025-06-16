import random

class PlanAgent:
    def create_plan(self, user_query: str) -> list[str]:
        print(f"PlanAgent: Creating plan for query: {user_query}")
        # Mock plan creation
        tasks = []
        if "flight" in user_query.lower():
            tasks.append("task_book_flight")
        if "hotel" in user_query.lower():
            tasks.append("task_book_hotel")
        if "car" in user_query.lower():
            tasks.append("task_rent_car")

        if not tasks:
            tasks.append("task_generic_inquiry")

        print(f"PlanAgent: Generated plan: {tasks}")
        return tasks

class TaskRefinerAgent:
    def refine_plan(self, plan: list[str], feedback: dict = None) -> list[str]:
        print(f"TaskRefinerAgent: Refining plan: {plan} with feedback: {feedback}")
        if feedback and feedback.get("needs_verification"):
            if "task_verify_all" not in plan:
                plan.append("task_verify_all")
                print(f"TaskRefinerAgent: Added verification task. New plan: {plan}")

        # Example modification: if a flight and hotel are booked, add a task to link them
        if "task_book_flight" in plan and "task_book_hotel" in plan and "task_link_reservations" not in plan:
            try:
                flight_idx = plan.index("task_book_flight")
                hotel_idx = plan.index("task_book_hotel")
                insert_idx = max(flight_idx, hotel_idx) + 1
                plan.insert(insert_idx, "task_link_reservations")
                print(f"TaskRefinerAgent: Added task_link_reservations. New plan: {plan}")
            except ValueError:
                # Should not happen if tasks are in plan
                pass
        return plan

class ToolAgent:
    def execute_task(self, task: str) -> dict:
        print(f"ToolAgent: Executing task: {task}")
        # Mock task execution
        # Simulate some tasks failing occasionally
        if task == "task_book_hotel" and random.random() < 0.3: # 30% chance of failure for hotel booking
            print(f"ToolAgent: Task {task} failed.")
            return {"task": task, "status": "failure", "result": f"Failed to complete {task} due to unexpected error."}

        if task == "task_verify_all" and random.random() < 0.2: # 20% chance of failure for verification
            print(f"ToolAgent: Task {task} failed.")
            return {"task": task, "status": "failure", "result": f"Verification failed for {task}."}

        result_message = f"Successfully completed {task}."
        if task == "task_book_flight":
            result_message = "Flight to SFO booked for tomorrow."
        elif task == "task_book_hotel":
            result_message = "Hotel California booked for 2 nights."
        elif task == "task_rent_car":
            result_message = "Tesla Model S rented."
        elif task == "task_link_reservations":
            result_message = "Flight and hotel reservations linked."
        elif task == "task_generic_inquiry":
            result_message = "Processed generic inquiry."

        print(f"ToolAgent: Task {task} succeeded.")
        return {"task": task, "status": "success", "result": result_message}

if __name__ == '__main__':
    # Basic test
    plan_agent = PlanAgent()
    refiner_agent = TaskRefinerAgent()
    tool_agent = ToolAgent()

    query = "I want to book a flight and a hotel for my trip to SFO."
    initial_plan = plan_agent.create_plan(query)
    print(f"Initial plan: {initial_plan}")

    refined_plan = refiner_agent.refine_plan(initial_plan)
    print(f"Refined plan (1st pass): {refined_plan}")

    refined_plan_with_feedback = refiner_agent.refine_plan(refined_plan, feedback={"needs_verification": True})
    print(f"Refined plan (with feedback): {refined_plan_with_feedback}")

    for task_item in refined_plan_with_feedback:
        execution_result = tool_agent.execute_task(task_item)
        print(f"Execution result for {task_item}: {execution_result}")
