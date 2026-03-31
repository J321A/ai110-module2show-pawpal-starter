import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ===========================================================================
# STEP 1: Import is at the top — Owner, Pet, Task, Scheduler are now usable.
# ===========================================================================

# ===========================================================================
# STEP 2: Manage application "memory" with st.session_state.
#
# Streamlit reruns the whole script on every interaction.
# We guard each key with "if not in st.session_state" so objects are created
# only ONCE (on first load) and survive across reruns.
# ===========================================================================

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_minutes_per_day=120,
        preferred_schedule="morning",
    )

if "pet" not in st.session_state:
    st.session_state.pet = Pet(name="Mochi", species="dog", age_years=3.0)
    st.session_state.owner.add_pet(st.session_state.pet)

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "plan" not in st.session_state:
    st.session_state.plan = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Section 1: Owner & Pet profile
# Inputs are pre-filled from session_state; a button commits changes.
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet")

col_o, col_p = st.columns(2)
with col_o:
    owner_name       = st.text_input("Owner name",             value=st.session_state.owner.name)
    available_minutes = st.number_input("Available minutes/day",
                                        min_value=10, max_value=480,
                                        value=st.session_state.owner.available_minutes_per_day)
    preferred_schedule = st.selectbox("Preferred schedule", ["morning", "afternoon", "evening"],
                                      index=["morning", "afternoon", "evening"]
                                      .index(st.session_state.owner.preferred_schedule))
with col_p:
    pet_name  = st.text_input("Pet name",         value=st.session_state.pet.name)
    species   = st.selectbox("Species",           ["dog", "cat", "rabbit", "other"],
                              index=["dog", "cat", "rabbit", "other"]
                              .index(st.session_state.pet.species)
                              if st.session_state.pet.species in ["dog", "cat", "rabbit", "other"] else 3)
    age_years = st.number_input("Pet age (years)", min_value=0.0, max_value=30.0,
                                 value=st.session_state.pet.age_years, step=0.5)

# Commit button: only update session_state objects when the user explicitly saves.
if st.button("Save profile"):
    st.session_state.owner.name                    = owner_name
    st.session_state.owner.available_minutes_per_day = int(available_minutes)
    st.session_state.owner.preferred_schedule      = preferred_schedule
    st.session_state.pet.name                      = pet_name
    st.session_state.pet.species                   = species
    st.session_state.pet.age_years                 = age_years
    # Reset plan so stale results are not shown after a profile change
    st.session_state.plan      = None
    st.session_state.scheduler = None
    st.rerun()

st.info(f"Current owner: {st.session_state.owner}  |  Pet: {st.session_state.pet}")

st.divider()

# ===========================================================================
# STEP 3: Wire UI actions to logic methods.
#
# "Add task" button → calls Task(...) to build the object, then calls
# pet.add_task() to register it on the Pet, and also appends it to
# st.session_state.tasks so the table stays in sync.
# ===========================================================================

st.subheader("Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening"])

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        preferred_time=preferred_time,
    )
    # Wire to logic: pet.add_task() keeps the Pet object in sync
    st.session_state.pet.add_task(new_task)
    # Also keep the flat list for the scheduler input
    st.session_state.tasks.append(new_task)

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Title":          t.title,
                "Duration (min)": t.duration_minutes,
                "Priority":       t.priority,
                "Preferred time": t.preferred_time or "—",
                "Done":           "Yes" if t.completed else "No",
            }
            for t in st.session_state.tasks
        ]
    )
    if st.button("Clear all tasks"):
        st.session_state.tasks       = []
        st.session_state.pet.tasks   = []
        st.session_state.plan        = None
        st.session_state.scheduler   = None
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Generate schedule — calls Scheduler.build_schedule() + explain_plan()
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner, pet=st.session_state.pet)
        plan = scheduler.build_schedule(st.session_state.tasks)
        st.session_state.scheduler = scheduler
        st.session_state.plan      = plan

if st.session_state.plan:
    scheduler = st.session_state.scheduler
    st.success("Schedule generated!")

    st.table(
        [
            {
                "Time":           entry.time_label(),
                "Task":           entry.task.title,
                "Duration (min)": entry.task.duration_minutes,
                "Priority":       entry.task.priority,
                "Reason":         entry.reason,
            }
            for entry in st.session_state.plan
        ]
    )

    if scheduler.skipped:
        st.warning("Skipped tasks (not enough time):")
        for task, reason in scheduler.skipped:
            st.markdown(f"- **{task.title}**: {reason}")

    with st.expander("Full plain-English explanation"):
        st.text(scheduler.explain_plan())
