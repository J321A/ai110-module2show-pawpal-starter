import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

# ---------------------------------------------------------------------------
# Section 1: Owner & Pet setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet")

col_o, col_p = st.columns(2)
with col_o:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input("Available minutes/day", min_value=10, max_value=480, value=120)
    preferred_schedule = st.selectbox("Preferred schedule", ["morning", "afternoon", "evening"])
with col_p:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
    age_years = st.number_input("Pet age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)

# Create (or replace) Owner and Pet in session_state whenever inputs change
owner = Owner(
    name=owner_name,
    available_minutes_per_day=int(available_minutes),
    preferred_schedule=preferred_schedule,
)
pet = Pet(name=pet_name, species=species, age_years=age_years)
owner.add_pet(pet)

st.session_state.owner = owner
st.session_state.pet = pet

st.success(f"Owner: {owner}  |  Pet: {pet}")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add tasks  (Task objects stored in session_state)
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

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
    st.session_state.tasks.append(new_task)

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Preferred time": t.preferred_time or "—",
            }
            for t in st.session_state.tasks
        ]
    )
    if st.button("Clear all tasks"):
        st.session_state.tasks = []
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Generate schedule  (calls Scheduler.build_schedule + explain_plan)
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner, pet=st.session_state.pet)
        plan = scheduler.build_schedule(st.session_state.tasks)

        st.session_state.scheduler = scheduler
        st.session_state.plan = plan

if "plan" in st.session_state and st.session_state.plan is not None:
    scheduler = st.session_state.scheduler

    st.success("Schedule generated!")

    plan_data = [
        {
            "Time": entry.time_label(),
            "Task": entry.task.title,
            "Duration (min)": entry.task.duration_minutes,
            "Priority": entry.task.priority,
            "Reason": entry.reason,
        }
        for entry in st.session_state.plan
    ]
    st.table(plan_data)

    if scheduler.skipped:
        st.warning("Skipped tasks (not enough time):")
        for task, reason in scheduler.skipped:
            st.markdown(f"- **{task.title}**: {reason}")

    with st.expander("Full plain-English explanation"):
        st.text(scheduler.explain_plan())
