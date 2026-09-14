import random

from LogisticRegression import (
    possibleChamps,
    demo_one_step_recommendation,
)
from greedy import GreedyDraft


def print_header():
    """Print a small League-of-Legends-style header."""
    print("=" * 60)
    print("      League of Legends – Draft Recommendation Assistant")
    print("=" * 60)
    print()


def print_menu():
    """Print the main menu options."""
    print("What would you like to do?")
    print("  [1] Quick last-pick recommendation demo")
    print("  [2] Full greedy draft vs random enemy team")
    print("  [3] Full greedy draft vs custom enemy team")
    print("  [0] Exit")
    print()


def run_greedy_random(greedy: GreedyDraft):
    """
    Use GreedyDraft to build a team against a random enemy + random bans.
    """
    enemy = random.sample(possibleChamps, 5)
    bans = random.sample([c for c in possibleChamps if c not in enemy], 10)

    print("\n--- Greedy draft vs RANDOM enemy team ---")
    print("Enemy team:", ", ".join(enemy))
    print("Bans:      ", ", ".join(bans))

    ally_team, final_p = greedy.greedy_draft(
        enemy_team=enemy,
        bans=bans,
        k_per_step=1,
        verbose=True,
    )

    print("\nYour final team:", ", ".join(ally_team))
    print(f"Predicted win probability: {final_p:.3f}")
    print()


def ask_custom_enemy_team() -> list[str]:
    """
    Ask the user to enter exactly 5 champions.
    Names must be valid (in possibleChamps). If a name is invalid,
    show which one(s) are wrong and ask again.
    """
    print("\nEnter the enemy team (5 champions).")
    print("Example: Ahri, Camille, Lux, Darius, Ezreal")

    while True:
        raw = input("Enemy team: ").strip()

        if not raw:
            print("No input given, falling back to a random enemy team.\n")
            return random.sample(possibleChamps, 5)

        # Split and clean
        names = [name.strip() for name in raw.split(",") if name.strip()]

        # Check count
        if len(names) != 5:
            print(f"You entered {len(names)} names; expected 5. Try again.\n")
            continue

        # Validate names
        invalid = [n for n in names if n not in possibleChamps]
        if invalid:
            print("The following names are not valid champions:")
            for n in invalid:
                print(f"  - {n} (not an option)")
            print("Please enter all 5 names again.\n")
            continue

        # All good
        return names


def run_greedy_custom(greedy: GreedyDraft):
    """
    Use GreedyDraft against a user-provided enemy team.
    Bans are chosen randomly from the remaining champions.
    """
    enemy = ask_custom_enemy_team()

    bans_pool = [c for c in possibleChamps if c not in enemy]
    if len(bans_pool) < 10:
        bans = bans_pool
    else:
        bans = random.sample(bans_pool, 10)

    print("\n--- Greedy draft vs CUSTOM enemy team ---")
    print("Enemy team:", ", ".join(enemy))
    print("Bans:      ", ", ".join(bans))

    ally_team, final_p = greedy.greedy_draft(
        enemy_team=enemy,
        bans=bans,
        k_per_step=1,
        verbose=True,
    )

    print("\nYour final team:", ", ".join(ally_team))
    print(f"Predicted win probability: {final_p:.3f}")
    print()


def main():
    """Main control flow for the program."""
    print_header()

    # Create a GreedyDraft engine using the champions from the dataset
    greedy = GreedyDraft(possibleChamps)

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            print("\n>>> Running one-step recommendation demo...\n")
            demo_one_step_recommendation(seed=0)
            print()
        elif choice == "2":
            run_greedy_random(greedy)
        elif choice == "3":
            run_greedy_custom(greedy)
        elif choice == "0":
            print("\ngg, gl next")
            break
        else:
            print("Invalid choice. Please pick 0, 1, 2, or 3.\n")


if __name__ == "__main__":
    main()