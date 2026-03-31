"""
tests/test_pawpal.py — Unit tests for PawPal+ logic layer
Run: python -m pytest
"""

from datetime import date, timedelta
import pytest

from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask


# ---------------------------------------------------------------------------
# Helpers — reusable fixtures
# ---------------------------------------------------------------------------

def make_owner(**kwargs):
    defaults = dict(name="Jordan", available_minutes_per_day=120, preferred_schedule="morning")
    defaults.update(kwargs)
    return Owner(**defaults)

def make_pet(**kwargs):
    defaults = dict(name="Mochi", species="dog", age_years=3)
    defaults.update(kwargs)
    return Pet(**defaults)


# ===========================================================================
# PHASE 2 TESTS (existing)
# ===========================================================================

# ---------------------------------------------------------------------------
# Test: mark_complete() changes the task's status
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


# ---------------------------------------------------------------------------
# Test: adding a task to a Pet increases that pet's task count
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = make_pet()

    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding",  duration_minutes=10, priority="high"))
    pet.add_task(Task(title="Grooming", duration_minutes=15, priority="medium"))
    assert len(pet.tasks) == 2


# ===========================================================================
# PHASE 3 TESTS — Sorting, Recurrence, Conflict Detection, Edge Cases
# ===========================================================================

# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks added out-of-order must come back sorted by start_minute."""
    owner = make_owner()
    pet   = make_pet()

    tasks = [
        Task("Evening walk",   duration_minutes=25, priority="low",    preferred_time="evening"),
        Task("Breakfast",      duration_minutes=10, priority="high",   preferred_time="morning"),
        Task("Afternoon play", duration_minutes=20, priority="medium", preferred_time="afternoon"),
    ]

    scheduler = Scheduler(owner=owner, pet=pet)
    scheduler.build_schedule(tasks)
    sorted_plan = scheduler.sort_by_time()

    start_minutes = [e.start_minute for e in sorted_plan]
    assert start_minutes == sorted(start_minutes), (
        "sort_by_time() must return entries in ascending start_minute order"
    )


def test_sort_by_time_on_empty_plan_returns_empty():
    """sort_by_time() on a scheduler with no plan should return an empty list."""
    scheduler = Scheduler(owner=make_owner(), pet=make_pet())
    assert scheduler.sort_by_time() == []


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_day_occurrence():
    """A completed daily task must spawn a new task due tomorrow."""
    today = date.today()
    task = Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        due_date=today,
    )

    next_task = task.mark_complete()

    assert task.completed is True
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.frequency == "daily"


def test_weekly_task_creates_next_week_occurrence():
    """A completed weekly task must spawn a new task due in 7 days."""
    today = date.today()
    task = Task(
        title="Grooming",
        duration_minutes=20,
        priority="medium",
        frequency="weekly",
        due_date=today,
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_once_task_returns_none_on_complete():
    """A one-off task must return None — no follow-up instance."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high", frequency="once")
    result = task.mark_complete()
    assert result is None


def test_recurring_task_inherits_title_and_priority():
    """The spawned next-occurrence task must preserve title, priority, and notes."""
    task = Task(
        title="Medication",
        duration_minutes=5,
        priority="high",
        frequency="daily",
        due_date=date.today(),
        notes="pill in treat",
    )
    next_task = task.mark_complete()

    assert next_task.title    == task.title
    assert next_task.priority == task.priority
    assert next_task.notes    == task.notes


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap must produce at least one warning."""
    entry_a = ScheduledTask(
        task=Task(title="Walk",    duration_minutes=30, priority="high"),
        start_minute=7 * 60,   # 07:00–07:30
        pet_name="Mochi",
    )
    entry_b = ScheduledTask(
        task=Task(title="Feeding", duration_minutes=10, priority="high"),
        start_minute=7 * 60 + 15,  # 07:15 — overlaps Walk by 15 min
        pet_name="Mochi",
    )

    warnings = Scheduler.detect_conflicts([entry_a, entry_b])

    assert len(warnings) >= 1
    assert "CONFLICT" in warnings[0]


def test_detect_conflicts_no_warning_when_sequential():
    """Back-to-back (non-overlapping) tasks must produce zero warnings."""
    entry_a = ScheduledTask(
        task=Task(title="Walk",    duration_minutes=30, priority="high"),
        start_minute=7 * 60,       # 07:00–07:30
        pet_name="Mochi",
    )
    entry_b = ScheduledTask(
        task=Task(title="Feeding", duration_minutes=10, priority="high"),
        start_minute=7 * 60 + 30,  # 07:30 — starts exactly when Walk ends
        pet_name="Mochi",
    )

    warnings = Scheduler.detect_conflicts([entry_a, entry_b])
    assert warnings == []


def test_detect_conflicts_empty_plan_returns_no_warnings():
    """An empty plan must return an empty warnings list."""
    assert Scheduler.detect_conflicts([]) == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_tasks_by_completed_false():
    """filter_tasks(completed=False) should return only pending tasks."""
    done    = Task(title="Done task",    duration_minutes=10, priority="low")
    pending = Task(title="Pending task", duration_minutes=10, priority="low")
    done.mark_complete()

    result = Scheduler.filter_tasks([done, pending], completed=False)
    assert result == [pending]


def test_filter_tasks_by_pet_object():
    """filter_tasks(pet=...) should return only tasks registered on that pet."""
    pet   = make_pet()
    other = make_pet(name="Luna", species="cat")

    t1 = Task(title="Walk",    duration_minutes=20, priority="high")
    t2 = Task(title="Feeding", duration_minutes=10, priority="high")
    pet.add_task(t1)
    other.add_task(t2)

    result = Scheduler.filter_tasks([t1, t2], pet=pet)
    assert result == [t1]


# ---------------------------------------------------------------------------
# Edge cases — pet with no tasks / budget exhausted
# ---------------------------------------------------------------------------

def test_schedule_with_no_tasks_produces_empty_plan():
    """Building a schedule with an empty task list must return an empty plan."""
    scheduler = Scheduler(owner=make_owner(), pet=make_pet())
    plan = scheduler.build_schedule([])
    assert plan == []


def test_tasks_exceeding_budget_are_skipped():
    """Tasks that overflow the time budget must land in skipped, not the plan."""
    owner = make_owner(available_minutes_per_day=20)
    pet   = make_pet()
    tasks = [
        Task("Short task", duration_minutes=10, priority="high"),
        Task("Long task",  duration_minutes=60, priority="high"),
    ]

    scheduler = Scheduler(owner=owner, pet=pet)
    scheduler.build_schedule(tasks)

    scheduled_titles = [e.task.title for e in scheduler.plan]
    skipped_titles   = [t.title for t, _ in scheduler.skipped]

    assert "Short task" in scheduled_titles
    assert "Long task"  in skipped_titles


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_invalid_priority_raises_value_error():
    """Creating a Task with an unrecognised priority must raise ValueError."""
    with pytest.raises(ValueError, match="priority"):
        Task(title="Bad task", duration_minutes=10, priority="urgent")


def test_invalid_frequency_raises_value_error():
    """Creating a Task with an unrecognised frequency must raise ValueError."""
    with pytest.raises(ValueError, match="frequency"):
        Task(title="Bad task", duration_minutes=10, priority="low", frequency="hourly")


def test_zero_duration_raises_value_error():
    """A Task with duration_minutes=0 must raise ValueError."""
    with pytest.raises(ValueError, match="duration_minutes"):
        Task(title="Zero task", duration_minutes=0, priority="low")
