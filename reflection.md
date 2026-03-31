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
. I used claude ai for brainstorming and refactoring. 

- What kinds of prompts or questions were most helpful?
. Providing the 4 classes core logic with attributes and methods. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When ai runned the bash command with python instead of python3 for my machine.

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
