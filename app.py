import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — powered by priority, time preferences, and conflict detection.")

# ---------------------------------------------------------------------------
# Session state — create objects once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan", available_minutes_per_day=120, preferred_schedule="morning"
    )
if "pet" not in st.session_state:
    st.session_state.pet = Pet(name="Mochi", species="dog", age_years=3.0)
    st.session_state.owner.add_pet(st.session_state.pet)
if "tasks"     not in st.session_state: st.session_state.tasks     = []
if "plan"      not in st.session_state: st.session_state.plan      = None
if "scheduler" not in st.session_state: st.session_state.scheduler = None

# ===========================================================================
# Section 1 — Owner & Pet profile
# ===========================================================================
st.subheader("Owner & Pet")

col_o, col_p = st.columns(2)
with col_o:
    owner_name        = st.text_input("Owner name", value=st.session_state.owner.name)
    available_minutes = st.number_input(
        "Available minutes/day", min_value=10, max_value=480,
        value=st.session_state.owner.available_minutes_per_day,
    )
    preferred_schedule = st.selectbox(
        "Preferred schedule", ["morning", "afternoon", "evening"],
        index=["morning", "afternoon", "evening"].index(st.session_state.owner.preferred_schedule),
    )
with col_p:
    pet_name  = st.text_input("Pet name", value=st.session_state.pet.name)
    species   = st.selectbox(
        "Species", ["dog", "cat", "rabbit", "other"],
        index=(["dog", "cat", "rabbit", "other"].index(st.session_state.pet.species)
               if st.session_state.pet.species in ["dog", "cat", "rabbit", "other"] else 3),
    )
    age_years = st.number_input(
        "Pet age (years)", min_value=0.0, max_value=30.0,
        value=st.session_state.pet.age_years, step=0.5,
    )

if st.button("Save profile"):
    st.session_state.owner.name                     = owner_name
    st.session_state.owner.available_minutes_per_day = int(available_minutes)
    st.session_state.owner.preferred_schedule       = preferred_schedule
    st.session_state.pet.name                       = pet_name
    st.session_state.pet.species                    = species
    st.session_state.pet.age_years                  = age_years
    st.session_state.plan      = None
    st.session_state.scheduler = None
    st.rerun()

st.info(f"**{st.session_state.owner.name}** — {st.session_state.owner.available_minutes_per_day} min/day "
        f"| prefers {st.session_state.owner.preferred_schedule} | pet: **{st.session_state.pet.name}** "
        f"({st.session_state.pet.species})")

st.divider()

# ===========================================================================
# Section 2 — Add tasks
# ===========================================================================
st.subheader("Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1: task_title    = st.text_input("Task title", value="Morning walk")
with col2: duration      = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3: priority      = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4: preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening"])

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        preferred_time=preferred_time,
    )
    st.session_state.pet.add_task(new_task)
    st.session_state.tasks.append(new_task)

# --- Filter controls ---------------------------------------------------------
if st.session_state.tasks:
    show_filter = st.radio(
        "Show tasks:", ["All", "Pending only", "Completed only"], horizontal=True
    )
    filter_map = {"All": None, "Pending only": False, "Completed only": True}
    visible = Scheduler.filter_tasks(
        st.session_state.tasks, completed=filter_map[show_filter]
    )

    st.write(f"Showing {len(visible)} of {len(st.session_state.tasks)} task(s):")
    st.table(
        [
            {
                "Title":          t.title,
                "Duration (min)": t.duration_minutes,
                "Priority":       t.priority,
                "Preferred time": t.preferred_time or "—",
                "Status":         "Done" if t.completed else "Pending",
            }
            for t in visible
        ]
    )

    if st.button("Clear all tasks"):
        st.session_state.tasks     = []
        st.session_state.pet.tasks = []
        st.session_state.plan      = None
        st.session_state.scheduler = None
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ===========================================================================
# Section 3 — Generate & display schedule
# ===========================================================================
st.subheader("Build Schedule")

col_btn, col_sort = st.columns([2, 1])
with col_btn:
    generate = st.button("Generate schedule", type="primary")
with col_sort:
    sort_by_time = st.toggle("Sort results by time", value=True)

if generate:
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        sched = Scheduler(owner=st.session_state.owner, pet=st.session_state.pet)
        plan  = sched.build_schedule(st.session_state.tasks)
        st.session_state.scheduler = sched
        st.session_state.plan      = plan

if st.session_state.plan is not None:
    sched = st.session_state.scheduler
    plan  = st.session_state.plan

    # --- Conflict detection (Step 4 algorithm surfaced in UI) ----------------
    conflicts = Scheduler.detect_conflicts(plan)
    if conflicts:
        st.error("**Scheduling conflicts detected** — review before following this plan:")
        for warning in conflicts:
            st.warning(f"⚠️ {warning}")
    else:
        st.success(f"Schedule ready — no conflicts found for **{st.session_state.pet.name}**!")

    # --- Sorted plan table ---------------------------------------------------
    display_plan = sched.sort_by_time(plan) if sort_by_time else plan

    st.table(
        [
            {
                "Time":           entry.time_label(),
                "Task":           entry.task.title,
                "Duration (min)": entry.task.duration_minutes,
                "Priority":       entry.task.priority,
                "Reason":         entry.reason,
            }
            for entry in display_plan
        ]
    )

    # --- Skipped tasks -------------------------------------------------------
    if sched.skipped:
        st.warning(
            f"**{len(sched.skipped)} task(s) skipped** — not enough time in the day:"
        )
        for task, reason in sched.skipped:
            st.markdown(f"- **{task.title}** ({task.duration_minutes} min): {reason}")

    # --- Summary metrics -----------------------------------------------------
    total_scheduled = sum(e.task.duration_minutes for e in plan)
    budget          = st.session_state.owner.available_minutes_per_day
    m1, m2, m3 = st.columns(3)
    m1.metric("Tasks scheduled", len(plan))
    m2.metric("Time used",       f"{total_scheduled} min")
    m3.metric("Time remaining",  f"{budget - total_scheduled} min")

    # --- Plain-English explanation -------------------------------------------
    with st.expander("Full plain-English explanation"):
        st.text(sched.explain_plan())
