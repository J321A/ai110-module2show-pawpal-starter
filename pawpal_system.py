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
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

VALID_PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    """A single pet care task."""

    title: str
    duration_minutes: int
    priority: str = "medium"          # "low" | "medium" | "high"
    preferred_time: Optional[str] = None   # e.g. "morning", "afternoon", "evening"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

    @property
    def priority_rank(self) -> int:
        """Numeric rank for sorting (higher = more urgent)."""
        return PRIORITY_RANK[self.priority]

    def __str__(self) -> str:
        time_hint = f" [{self.preferred_time}]" if self.preferred_time else ""
        return f"{self.title}{time_hint} ({self.duration_minutes} min, {self.priority} priority)"


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

    def __str__(self) -> str:
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
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferred_schedule = preferred_schedule
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def __str__(self) -> str:
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

    @property
    def end_minute(self) -> int:
        return self.start_minute + self.task.duration_minutes

    def time_label(self) -> str:
        """Human-readable HH:MM start time."""
        h, m = divmod(self.start_minute, 60)
        return f"{h:02d}:{m:02d}"

    def __str__(self) -> str:
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
    """

    # Rough minute offsets for time-of-day slots
    TIME_SLOT_START = {"morning": 7 * 60, "afternoon": 13 * 60, "evening": 18 * 60}

    def __init__(self, owner: Owner, pet: Pet) -> None:
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
            self.plan.append(ScheduledTask(task=task, start_minute=cursor, reason=reason))
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
    # Helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """High priority first; prefer tasks matching owner's schedule."""
        preferred = self.owner.preferred_schedule

        def sort_key(t: Task) -> tuple:
            time_match = 0 if t.preferred_time == preferred else 1
            return (-t.priority_rank, time_match)

        return sorted(tasks, key=sort_key)

    def _explain(self, task: Task) -> str:
        parts = [f"{task.priority} priority"]
        if task.preferred_time == self.owner.preferred_schedule:
            parts.append(f"matches {self.owner.name}'s {self.owner.preferred_schedule} preference")
        if task.notes:
            parts.append(task.notes)
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Quick smoke-test (run: python pawpal_system.py)
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
