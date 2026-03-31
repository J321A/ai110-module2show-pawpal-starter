"""
pawpal_system.py — PawPal+ logic layer

Four core classes:
  - Task      (dataclass): a single pet care action
  - Pet       (dataclass): the pet being cared for
  - Owner     : the person responsible for care
  - Scheduler : builds and explains a daily care plan
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

VALID_PRIORITIES  = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")
PRIORITY_RANK     = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    """A single pet care task."""

    title: str
    duration_minutes: int
    priority: str = "medium"               # "low" | "medium" | "high"
    preferred_time: Optional[str] = None   # "morning" | "afternoon" | "evening"
    notes: str = ""
    completed: bool = False
    frequency: str = "once"                # "once" | "daily" | "weekly"
    due_date: Optional[date] = None        # date this task is due

    def __post_init__(self) -> None:
        """Validate priority, frequency, and duration after dataclass initialization."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'"
            )
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(
                f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

    # ------------------------------------------------------------------
    # Step 3 — Recurring tasks
    # ------------------------------------------------------------------

    def mark_complete(self) -> Optional[Task]:
        """Mark this task done; return a new next-occurrence Task for recurring tasks.

        Uses timedelta so that:
          - "daily"  tasks recur tomorrow  (due_date + 1 day)
          - "weekly" tasks recur next week (due_date + 7 days)
          - "once"   tasks return None — no follow-up needed
        """
        self.completed = True

        if self.frequency == "once":
            return None

        base = self.due_date or date.today()
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        next_due = base + delta

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
            notes=self.notes,
            completed=False,
            frequency=self.frequency,
            due_date=next_due,
        )

    @property
    def priority_rank(self) -> int:
        """Numeric rank for sorting (higher = more urgent)."""
        return PRIORITY_RANK[self.priority]

    def __str__(self) -> str:
        """Return a concise human-readable description of the task."""
        time_hint = f" [{self.preferred_time}]" if self.preferred_time else ""
        recur     = f" ({self.frequency})" if self.frequency != "once" else ""
        due       = f" due {self.due_date}" if self.due_date else ""
        return f"{self.title}{time_hint}{recur}{due} ({self.duration_minutes} min, {self.priority} priority)"


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet whose care needs are being planned."""

    name: str
    species: str                        # e.g. "dog", "cat", "rabbit"
    age_years: float = 0.0
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a care task to this pet."""
        self.tasks.append(task)

    def __str__(self) -> str:
        """Return a concise summary of the pet including any special needs."""
        needs = f", special needs: {', '.join(self.special_needs)}" if self.special_needs else ""
        return f"{self.name} ({self.species}, {self.age_years} yr{needs})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """The person responsible for the pet's care."""

    def __init__(
        self,
        name: str,
        available_minutes_per_day: int = 120,
        preferred_schedule: str = "morning",   # "morning" | "afternoon" | "evening"
    ) -> None:
        """Initialize an Owner with a daily time budget and schedule preference."""
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferred_schedule = preferred_schedule
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner's care."""
        self.pets.append(pet)

    def __str__(self) -> str:
        """Return a summary of the owner, their time budget, and registered pets."""
        pet_names = ", ".join(p.name for p in self.pets) if self.pets else "no pets yet"
        return (
            f"{self.name} | available: {self.available_minutes_per_day} min/day "
            f"| prefers: {self.preferred_schedule} | pets: {pet_names}"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    """A task placed into the daily plan."""

    task: Task
    start_minute: int    # minutes from the start of the day (0 = midnight)
    reason: str = ""
    pet_name: str = ""   # which pet this task belongs to (used for conflict detection)

    @property
    def end_minute(self) -> int:
        """Return the minute at which this scheduled task finishes."""
        return self.start_minute + self.task.duration_minutes

    def time_label(self) -> str:
        """Human-readable HH:MM start time."""
        h, m = divmod(self.start_minute, 60)
        return f"{h:02d}:{m:02d}"

    def __str__(self) -> str:
        """Format the scheduled task as a single schedule-entry line."""
        return (
            f"{self.time_label()} — {self.task.title} "
            f"({self.task.duration_minutes} min) | {self.reason}"
        )


class Scheduler:
    """
    Builds a prioritised daily care schedule for an owner and their pet.

    Algorithm (greedy by priority):
      1. Sort tasks by priority (high → low); break ties by preferred_time
         alignment with the owner's preferred_schedule.
      2. Walk through tasks and assign start times sequentially, stopping
         when the owner's available time budget is exhausted.
      3. Record a plain-English reason for each accepted or skipped task.

    Additional capabilities (Phase 3):
      - sort_by_time()     : re-order an existing plan by start time
      - filter_tasks()     : filter a task list by completion status or pet name
      - detect_conflicts() : warn about overlapping scheduled tasks
    """

    # Rough minute offsets for time-of-day slots
    TIME_SLOT_START = {"morning": 7 * 60, "afternoon": 13 * 60, "evening": 18 * 60}

    def __init__(self, owner: Owner, pet: Pet) -> None:
        """Bind the scheduler to a specific owner and pet."""
        self.owner = owner
        self.pet = pet
        self.plan: list[ScheduledTask] = []
        self.skipped: list[tuple[Task, str]] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build_schedule(self, tasks: list[Task]) -> list[ScheduledTask]:
        """Sort and schedule tasks within the owner's time budget."""
        self.plan.clear()
        self.skipped.clear()

        sorted_tasks = self._sort_tasks(tasks)
        budget = self.owner.available_minutes_per_day
        cursor = self.TIME_SLOT_START.get(self.owner.preferred_schedule, 7 * 60)
        used = 0

        for task in sorted_tasks:
            if used + task.duration_minutes > budget:
                self.skipped.append(
                    (task, f"not enough time remaining ({budget - used} min left, needs {task.duration_minutes} min)")
                )
                continue

            reason = self._explain(task)
            self.plan.append(
                ScheduledTask(task=task, start_minute=cursor,
                              reason=reason, pet_name=self.pet.name)
            )
            cursor += task.duration_minutes
            used += task.duration_minutes

        return self.plan

    def explain_plan(self) -> str:
        """Return a human-readable summary of the schedule."""
        if not self.plan and not self.skipped:
            return "No tasks have been scheduled yet. Call build_schedule() first."

        lines: list[str] = [
            f"Daily care plan for {self.pet.name} — owner: {self.owner.name}",
            "=" * 55,
        ]

        if self.plan:
            lines.append("SCHEDULED:")
            for entry in self.plan:
                lines.append(f"  {entry}")
        else:
            lines.append("  (no tasks scheduled)")

        if self.skipped:
            lines.append("\nSKIPPED:")
            for task, reason in self.skipped:
                lines.append(f"  ✗ {task.title}: {reason}")

        total = sum(e.task.duration_minutes for e in self.plan)
        lines.append(f"\nTotal time scheduled: {total} / {self.owner.available_minutes_per_day} min")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Step 2 — Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self, entries: Optional[list[ScheduledTask]] = None) -> list[ScheduledTask]:
        """Return scheduled tasks sorted by start_minute (earliest first).

        Uses a lambda as the sort key so HH:MM ordering is exact rather than
        lexicographic — start_minute is already an integer, so no parsing needed.
        If no list is passed, sorts the current plan in place and returns it.
        """
        target = entries if entries is not None else self.plan
        return sorted(target, key=lambda e: e.start_minute)

    # ------------------------------------------------------------------
    # Step 2 — Filtering
    # ------------------------------------------------------------------

    @staticmethod
    def filter_tasks(
        tasks: list[Task],
        *,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
        pet: Optional[Pet] = None,
    ) -> list[Task]:
        """Return a filtered subset of tasks.

        Args:
            tasks:     The task list to filter.
            completed: If True, keep only done tasks; if False, keep only pending.
                       Pass None to skip this filter.
            pet_name:  Keep only tasks whose title contains this pet's name
                       (case-insensitive). Useful when a shared task list mixes
                       tasks for multiple pets.
            pet:       Alternatively, pass a Pet object — its .tasks list is used
                       to match by identity rather than name substring.
        """
        result = tasks

        if completed is not None:
            result = [t for t in result if t.completed == completed]

        if pet is not None:
            pet_task_ids = {id(t) for t in pet.tasks}
            result = [t for t in result if id(t) in pet_task_ids]
        elif pet_name is not None:
            result = [t for t in result if pet_name.lower() in t.title.lower()]

        return result

    # ------------------------------------------------------------------
    # Step 4 — Conflict detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_conflicts(entries: list[ScheduledTask]) -> list[str]:
        """Return warning strings for any two tasks whose time windows overlap.

        Strategy: sort by start_minute, then check each consecutive pair.
        An overlap occurs when entry[i].end_minute > entry[i+1].start_minute.
        This is lightweight — O(n log n) — and never raises; it only warns.
        """
        warnings: list[str] = []
        sorted_entries = sorted(entries, key=lambda e: e.start_minute)

        for i in range(len(sorted_entries) - 1):
            a = sorted_entries[i]
            b = sorted_entries[i + 1]
            if a.end_minute > b.start_minute:
                overlap = a.end_minute - b.start_minute
                warnings.append(
                    f"CONFLICT: '{a.task.title}' ({a.pet_name}, "
                    f"{a.time_label()}–{_minute_to_hhmm(a.end_minute)}) overlaps "
                    f"'{b.task.title}' ({b.pet_name}, starts {b.time_label()}) "
                    f"by {overlap} min"
                )

        return warnings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """High priority first; prefer tasks matching owner's schedule."""
        preferred = self.owner.preferred_schedule
        return sorted(tasks, key=lambda t: (-t.priority_rank,
                                             0 if t.preferred_time == preferred else 1))

    def _explain(self, task: Task) -> str:
        """Build a plain-English reason string for why a task was scheduled."""
        parts = [f"{task.priority} priority"]
        if task.preferred_time == self.owner.preferred_schedule:
            parts.append(f"matches {self.owner.name}'s {self.owner.preferred_schedule} preference")
        if task.frequency != "once":
            parts.append(f"recurring {task.frequency}")
        if task.notes:
            parts.append(task.notes)
        return "; ".join(parts)


def _minute_to_hhmm(minute: int) -> str:
    """Convert an integer minute-of-day to an HH:MM string."""
    h, m = divmod(minute, 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------------
# Quick smoke-test (run: python3 pawpal_system.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pet = Pet(name="Mochi", species="dog", age_years=3)
    owner = Owner(name="Jordan", available_minutes_per_day=90, preferred_schedule="morning")
    owner.add_pet(pet)

    tasks = [
        Task("Morning walk",      duration_minutes=30, priority="high",   preferred_time="morning"),
        Task("Feeding",           duration_minutes=10, priority="high",   preferred_time="morning"),
        Task("Grooming",          duration_minutes=20, priority="medium", preferred_time="afternoon"),
        Task("Training session",  duration_minutes=15, priority="medium", preferred_time="morning"),
        Task("Vet medication",    duration_minutes=5,  priority="high",   notes="must not be skipped"),
        Task("Playtime",          duration_minutes=25, priority="low",    preferred_time="evening"),
    ]

    scheduler = Scheduler(owner=owner, pet=pet)
    scheduler.build_schedule(tasks)
    print(scheduler.explain_plan())
