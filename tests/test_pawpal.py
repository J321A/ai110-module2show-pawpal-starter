"""
tests/test_pawpal.py — Unit tests for PawPal+ logic layer
Run: python -m pytest
"""

from pawpal_system import Task, Pet


# ---------------------------------------------------------------------------
# Test 1: mark_complete() changes the task's status
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    # Before: task should not be complete
    assert task.completed is False

    task.mark_complete()

    # After: task should be marked complete
    assert task.completed is True


# ---------------------------------------------------------------------------
# Test 2: adding a task to a Pet increases that pet's task count
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age_years=3)

    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feeding",  duration_minutes=10, priority="high"))
    pet.add_task(Task(title="Grooming", duration_minutes=15, priority="medium"))

    assert len(pet.tasks) == 2
