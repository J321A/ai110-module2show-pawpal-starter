# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

UML Class Design: 
1. Pet - represents the pet being cared for.
Attributes: 
name: str
species: str
age: int
special_needs: str
Methods: 
update-info()
display_info()

2. Task - Represent a care activity
Attributes:
name: str (e.g., walk, feed)
duration: int (minutes)
priority: int (higher = more important)
time_constraint: optional tuple (start, end)
Methods:
update_task()
is_within_time()

3. Owner - Represents the user
Attributes: 
name: str
available_time: int (minutes per day)
preferences: dict
Methods:
update_preferences()

4. Scheduler - Core logic class (the brain)
Attributes:
tasks: list [task]
owner: owner
Methods:
generate_schedule()
sort_tasks_by_priority()
apply_constraints()

5. DailyPlan - Represents the generated schedule.
Attributes:
scheduled_tasks: list [task]
total_time: int
Methods:
display_plan()
explain_plan()



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. I removed DailyPlan because it is not a core data model, it's just a result/representaion of scheduling. Instead of a separate class, I let Scheduler return the plan directly, as list or structured data. 

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Builds a prioritised daily care schedule for an owner and their pet.

    Algorithm (greedy by priority):
      1. Sort tasks by priority (high → low); break ties by preferred_time
         alignment with the owner's preferred_schedule.
      2. Walk through tasks and assign start times sequentially, stopping
         when the owner's available time budget is exhausted.
      3. Record a plain-English reason for each accepted or skipped task.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: Greedy priority ordering over true time-window optimization**

The scheduler uses a greedy algorithm — it sorts tasks by priority once, then assigns them sequentially without ever going back to reconsider earlier decisions. If a high-priority 30-minute task is placed first and leaves only 10 minutes at the end of the day, a medium-priority 15-minute task gets skipped even though swapping their order would have fit both.

A more optimal approach (dynamic programming or backtracking) could find the arrangement that fits the most tasks within the time budget. But that adds significant complexity for a pet care scenario where the number of daily tasks is small (typically under 20). With a small task list, the greedy result is almost always the same as the optimal result — and it is far easier to explain to a pet owner why their dog's walk was scheduled before grooming ("high priority, morning preference") than to justify a computed permutation. Readability and trust matter more here than squeezing out the last few minutes of utilization.

The conflict detection added in Phase 3 partially compensates for this tradeoff: even if the scheduler does not reorder tasks to avoid overlaps, it at least surfaces warnings so the owner can intervene manually.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Claude AI across every phase: brainstorming the initial four-class architecture, generating class stubs from the UML description, refactoring the `Scheduler` to add `sort_by_time`, `filter_tasks`, and `detect_conflicts`, writing the full pytest suite, and wiring the Streamlit UI to the backend logic. AI was most useful as a "first draft" generator — it produced working code quickly that I could then read, understand, and decide whether to keep.

- What kinds of prompts or questions were most helpful?

The most effective prompts were specific and structural: providing the four class names with their attributes and methods up-front gave the AI a clear contract to implement against. Asking "why" questions — "why use `timedelta` here instead of adding 1 to the day number?" — also produced useful explanations that helped me understand the code rather than just accept it.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

The AI initially used `python` in the Bash commands to run scripts, which failed on my machine because the Python 3 binary is registered as `python3`. I caught this because I read the error output carefully instead of assuming the suggestion was correct. I verified by running `python3 --version` myself, confirmed the correct command, and noted it as a reminder that AI suggestions are environment-agnostic and always need to be checked against the actual machine.

A second example: when the AI drafted the `filter_tasks` method using a `pet_name` string substring match, I evaluated whether that approach was precise enough. Because two pets could share a name prefix, I added the `pet=` keyword argument that matches by object identity (`id(t) in pet_task_ids`) instead — a more reliable filter for the actual data model.

**c. VS Code Copilot feature effectiveness**

- Which Copilot features were most effective for building your scheduler?

The most effective feature was using `#codebase` or `#file:pawpal_system.py` in Copilot Chat to ground the AI's suggestions in the actual implementation. Without that context, suggestions were generic; with it, the AI could reference specific class names, method signatures, and the existing algorithm. Inline Chat on specific methods (like `mark_complete`) was also efficient for targeted additions without losing the surrounding context.

- Give one example of an AI suggestion you rejected or modified.

The AI's first draft of `detect_conflicts` checked only for exact `start_minute` equality between tasks, which would miss cases where a 30-minute task starting at 07:00 overlaps a task starting at 07:15. I replaced it with the consecutive-pair overlap check (`a.end_minute > b.start_minute`) which catches all duration-based overlaps with the same O(n log n) complexity.

- How did using separate chat sessions for different phases help you stay organized?

Keeping the testing session separate from the implementation session prevented the AI's context from mixing concerns. When focused only on tests, Copilot's suggestions stayed within the pytest idioms and edge-case mindset. If the same session had also contained the algorithm implementation, the AI might have started suggesting implementation changes instead of test coverage improvements.

**d. Being the lead architect**

Working with AI made it clear that the human's role is to hold the design invariants. The AI is fast at producing code that works in isolation but does not automatically know that `pet.add_task()` and `st.session_state.tasks` needed to stay in sync, or that the `filter_tasks` identity-based approach was safer than substring matching. Every time I accepted a suggestion without reading it carefully, I introduced a subtle inconsistency. The lesson: AI accelerates execution, but the architect is still responsible for coherence.

---

## 4. Testing and Verification

**a. What you tested**

The test suite in `tests/test_pawpal.py` covers 18 behaviors across four categories:

1. **Task lifecycle** — `mark_complete()` sets `completed=True`; `Pet.add_task()` increments task count
2. **Sorting** — tasks added out-of-order are returned in ascending `start_minute` order; empty plan returns empty list
3. **Recurrence** — daily tasks produce a next instance due tomorrow (via `timedelta(days=1)`); weekly tasks produce one due in 7 days; one-off tasks return `None`
4. **Conflict detection** — overlapping windows produce a `"CONFLICT"` warning string; sequential tasks produce none; empty plan produces no warnings
5. **Filtering** — `completed=False` excludes done tasks; `pet=` filters by object identity
6. **Budget enforcement** — tasks exceeding available minutes land in `scheduler.skipped`
7. **Validation** — invalid priority, invalid frequency, and zero duration all raise `ValueError`

These tests are important because they verify the four algorithmic features independently of the Streamlit UI, so a bug in the UI cannot mask a logic error in the backend.

**b. Confidence**

⭐⭐⭐⭐ (4 / 5) — The suite is thorough for the current feature set. Edge cases I would add next:
- A task whose `duration_minutes` exactly equals the remaining budget (boundary condition)
- A recurring task with no `due_date` set (falls back to `date.today()` — test that branch explicitly)
- A multi-pet schedule where conflicts span two different pets' tasks

---

## 5. Reflection

**a. What went well**

The clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`) worked well throughout the project. Because the four classes had no Streamlit imports, every algorithm could be tested in a plain terminal session without launching the UI. When it came time to wire up the Streamlit app, there were no logic changes needed — just display decisions.

**b. What you would improve**

The `Scheduler` currently handles one pet at a time. A real pet owner with two pets needs a combined schedule that interleaves both pets' tasks and detects cross-pet conflicts automatically, rather than requiring the developer to merge two separate plans manually (as done in `main.py`'s conflict demo). A `MultiPetScheduler` wrapper that accepts a list of `(pet, tasks)` pairs and merges the plans would be the next design iteration.

**c. Key takeaway**

The most important lesson was that AI collaboration works best when you design first and generate second. Every time I gave the AI a clear specification — the class name, its attributes, and what the method should return — the output was usable with minor edits. Every time I asked the AI to "figure out what I need," the output required more rework than writing it from scratch. Design clarity is not just good engineering practice; it is also the most effective prompt engineering strategy.
