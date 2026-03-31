# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan daily care tasks for their pet using priority-based scheduling, time-of-day preferences, recurring task logic, and real-time conflict detection.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## Features

| Feature | Description |
|---|---|
| **Priority scheduling** | Tasks are sorted high → low priority; ties broken by alignment with the owner's preferred time of day (morning / afternoon / evening) |
| **Time-of-day sorting** | The final schedule is displayed sorted by actual start time using `Scheduler.sort_by_time()` |
| **Task filtering** | View all, pending-only, or completed-only tasks using `Scheduler.filter_tasks()` |
| **Conflict detection** | `Scheduler.detect_conflicts()` checks for overlapping task windows and surfaces warnings in the UI before the owner follows the plan |
| **Recurring tasks** | Tasks marked `frequency="daily"` or `"weekly"` automatically generate a next-occurrence instance via `Task.mark_complete()` using Python's `timedelta` |
| **Time budget enforcement** | Tasks that exceed the owner's available minutes per day are moved to a "skipped" list with a plain-English reason |
| **Session persistence** | Owner, Pet, and Task objects survive Streamlit reruns via `st.session_state` |
| **Plain-English explanation** | `Scheduler.explain_plan()` narrates why each task was scheduled or skipped |

---

## Project Structure

```
pawpal_system.py   — Logic layer: Owner, Pet, Task, Scheduler, ScheduledTask
app.py             — Streamlit UI wired to the logic layer
main.py            — Terminal demo script (run to verify logic without the UI)
tests/
  test_pawpal.py   — Automated test suite (pytest)
reflection.md      — Design decisions, tradeoffs, and AI collaboration notes
```

---

## Getting Started

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the terminal demo

```bash
python3 main.py
```

---

## Testing PawPal+

### Run tests

```bash
python3 -m pytest tests/ -v
```

### What the tests cover

| Test | What it verifies |
|---|---|
| `test_mark_complete_changes_status` | `completed` flips from `False` to `True` after `mark_complete()` |
| `test_add_task_increases_pet_task_count` | `Pet.add_task()` increments `len(pet.tasks)` |
| `test_sort_by_time_returns_chronological_order` | Tasks added out-of-order are returned sorted by `start_minute` |
| `test_sort_by_time_on_empty_plan_returns_empty` | Edge case: no plan → empty list |
| `test_daily_task_creates_next_day_occurrence` | Daily recurring task spawns a next instance due tomorrow |
| `test_weekly_task_creates_next_week_occurrence` | Weekly recurring task spawns a next instance due in 7 days |
| `test_once_task_returns_none_on_complete` | One-off task returns `None` — no follow-up created |
| `test_recurring_task_inherits_title_and_priority` | Next-occurrence task preserves all metadata from the original |
| `test_detect_conflicts_flags_overlapping_tasks` | Overlapping windows produce at least one `"CONFLICT"` warning |
| `test_detect_conflicts_no_warning_when_sequential` | Back-to-back tasks produce zero warnings |
| `test_detect_conflicts_empty_plan_returns_no_warnings` | Empty plan → empty warnings list |
| `test_filter_tasks_by_completed_false` | Pending filter excludes completed tasks |
| `test_filter_tasks_by_pet_object` | Pet-based filter matches by object identity |
| `test_schedule_with_no_tasks_produces_empty_plan` | Empty task list → empty schedule |
| `test_tasks_exceeding_budget_are_skipped` | Over-budget tasks land in `scheduler.skipped`, not `plan` |
| `test_invalid_priority_raises_value_error` | Bad priority string raises `ValueError` |
| `test_invalid_frequency_raises_value_error` | Bad frequency string raises `ValueError` |
| `test_zero_duration_raises_value_error` | Zero-minute duration raises `ValueError` |

### Confidence level

⭐⭐⭐⭐ (4 / 5)

The 18-test suite covers all four algorithmic features (sorting, filtering, recurrence, conflict detection) plus critical edge cases (empty plan, zero duration, invalid inputs). Confidence would reach 5/5 with integration tests that run the full `build_schedule → sort_by_time → detect_conflicts` pipeline end-to-end against known inputs.

---

## 📸 Demo

<a href="/Users/user/Desktop/image1.png" target="_blank">
  <img src='/Users/user/Desktop/image1.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

---

## Suggested workflow (for students)

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
