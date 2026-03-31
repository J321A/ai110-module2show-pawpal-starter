"""
main.py — Demo / testing ground for PawPal+ logic
Run: python3 main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask

DIVIDER = "=" * 55

# ---------------------------------------------------------------------------
# Setup — Owner and two Pets
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes_per_day=180, preferred_schedule="morning")

mochi = Pet(name="Mochi", species="dog",    age_years=3)
luna  = Pet(name="Luna",  species="cat",    age_years=5, special_needs=["thyroid medication"])

owner.add_pet(mochi)
owner.add_pet(luna)

print(DIVIDER)
print("PAWPAL+ DEMO")
print(DIVIDER)
print(f"Owner : {owner}")
print(f"Pets  : {mochi}")
print(f"        {luna}\n")

# ---------------------------------------------------------------------------
# Tasks — added OUT OF ORDER on purpose (to demo sort_by_time)
# Mix of frequencies and priorities across both pets
# ---------------------------------------------------------------------------
tasks = [
    # Evening tasks listed first — deliberately out of order
    Task("Evening walk",        duration_minutes=25, priority="low",    preferred_time="evening",   frequency="daily",  due_date=date.today()),
    Task("Brushing / grooming", duration_minutes=15, priority="medium", preferred_time="afternoon", frequency="weekly", due_date=date.today()),

    # Morning high-priority tasks
    Task("Morning walk",        duration_minutes=30, priority="high",   preferred_time="morning",   frequency="daily",  due_date=date.today()),
    Task("Breakfast feeding",   duration_minutes=10, priority="high",   preferred_time="morning"),
    Task("Luna's medication",   duration_minutes=5,  priority="high",   preferred_time="morning",   frequency="daily",  due_date=date.today(),
         notes="thyroid pill hidden in treat"),

    # Afternoon tasks
    Task("Midday playtime",     duration_minutes=20, priority="medium", preferred_time="afternoon"),
    Task("Training session",    duration_minutes=15, priority="medium", preferred_time="morning"),
]

# Register tasks on the appropriate pet
for t in tasks:
    if "Luna" in t.title:
        luna.add_task(t)
    else:
        mochi.add_task(t)

# ---------------------------------------------------------------------------
# Step 2a — Sort tasks by preferred_time before scheduling
# ---------------------------------------------------------------------------
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
sorted_by_time = sorted(tasks, key=lambda t: TIME_ORDER.get(t.preferred_time or "evening", 2))

print("TASKS SORTED BY PREFERRED TIME (before scheduling):")
for t in sorted_by_time:
    print(f"  {t}")
print()

# ---------------------------------------------------------------------------
# Step 2b — Filter: pending tasks only / Luna's tasks only
# ---------------------------------------------------------------------------
pending = Scheduler.filter_tasks(tasks, completed=False)
print(f"PENDING TASKS ({len(pending)} of {len(tasks)}):")
for t in pending:
    print(f"  {t.title}")
print()

lunas_tasks = Scheduler.filter_tasks(tasks, pet=luna)
print(f"LUNA'S TASKS ({len(lunas_tasks)}):")
for t in lunas_tasks:
    print(f"  {t.title}")
print()

# ---------------------------------------------------------------------------
# Step 3 — Recurring task: mark "Morning walk" complete, get next occurrence
# ---------------------------------------------------------------------------
morning_walk = next(t for t in tasks if t.title == "Morning walk")
next_walk = morning_walk.mark_complete()

print("RECURRING TASK DEMO:")
print(f"  '{morning_walk.title}' marked complete (due {morning_walk.due_date})")
if next_walk:
    print(f"  Next occurrence auto-created: due {next_walk.due_date} (frequency: {next_walk.frequency})")
print()

# Replace the completed task with its next occurrence in the task list
# so the scheduler sees a fresh "Morning walk" for today's plan
tasks_for_schedule = [t for t in tasks if not t.completed]
if next_walk:
    tasks_for_schedule.append(next_walk)

# ---------------------------------------------------------------------------
# Step 4 — Conflict detection
# Build two separate scheduler plans then merge them to test overlaps
# ---------------------------------------------------------------------------
mochi_scheduler = Scheduler(owner=owner, pet=mochi)
mochi_plan = mochi_scheduler.build_schedule(
    [t for t in tasks_for_schedule if t not in luna.tasks]
)

luna_scheduler = Scheduler(owner=owner, pet=luna)
luna_plan = luna_scheduler.build_schedule(luna.tasks)

# Manually place Luna's medication at the same start time as Mochi's walk
# to trigger a conflict warning
conflict_demo: list[ScheduledTask] = list(mochi_plan)
if luna_plan:
    forced_conflict = ScheduledTask(
        task=luna_plan[0].task,
        start_minute=mochi_plan[0].start_minute,   # same start = guaranteed overlap
        reason="forced overlap for conflict demo",
        pet_name="Luna",
    )
    conflict_demo.append(forced_conflict)

conflicts = Scheduler.detect_conflicts(conflict_demo)
print("CONFLICT DETECTION DEMO:")
if conflicts:
    for warning in conflicts:
        print(f"  ⚠  {warning}")
else:
    print("  No conflicts detected.")
print()

# ---------------------------------------------------------------------------
# Today's Schedule — sorted by actual start time
# ---------------------------------------------------------------------------
print("TODAY'S SCHEDULE (Mochi)")
print(mochi_scheduler.explain_plan())
print()

sorted_plan = mochi_scheduler.sort_by_time()
print("SAME PLAN SORTED BY START TIME:")
for entry in sorted_plan:
    print(f"  {entry}")
print()

# Filter: show only completed tasks after the run
completed_tasks = Scheduler.filter_tasks(tasks, completed=True)
print(f"COMPLETED TASKS THIS SESSION ({len(completed_tasks)}):")
for t in completed_tasks:
    print(f"  ✓ {t.title} (was due {t.due_date})")
