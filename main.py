"""
main.py — Demo / testing ground for PawPal+ logic
Run: python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# 1. Create Owner
# ---------------------------------------------------------------------------
owner = Owner(
    name="Jordan",
    available_minutes_per_day=120,
    preferred_schedule="morning",
)

# ---------------------------------------------------------------------------
# 2. Create two Pets and register them with the owner
# ---------------------------------------------------------------------------
mochi = Pet(name="Mochi", species="dog", age_years=3)
luna  = Pet(name="Luna",  species="cat", age_years=5, special_needs=["thyroid medication"])

owner.add_pet(mochi)
owner.add_pet(luna)

print("=" * 55)
print("PAWPAL+ DEMO")
print("=" * 55)
print(f"Owner : {owner}")
print(f"Pets  : {mochi}")
print(f"        {luna}")
print()

# ---------------------------------------------------------------------------
# 3. Define tasks — different times and priorities
# ---------------------------------------------------------------------------
tasks = [
    Task("Morning walk",       duration_minutes=30, priority="high",   preferred_time="morning"),
    Task("Breakfast feeding",  duration_minutes=10, priority="high",   preferred_time="morning"),
    Task("Luna's medication",  duration_minutes=5,  priority="high",   preferred_time="morning",
         notes="thyroid pill hidden in treat"),
    Task("Midday playtime",    duration_minutes=20, priority="medium", preferred_time="afternoon"),
    Task("Brushing / grooming",duration_minutes=15, priority="medium", preferred_time="afternoon"),
    Task("Evening walk",       duration_minutes=25, priority="low",    preferred_time="evening"),
]

# ---------------------------------------------------------------------------
# 4. Build and print Today's Schedule (using Mochi as the primary pet)
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner=owner, pet=mochi)
scheduler.build_schedule(tasks)

print("TODAY'S SCHEDULE")
print(scheduler.explain_plan())
