import random

from LogisticRegression import possibleChamps, recommend_next_pick, probability


class GreedyDraft:
    """Simple greedy drafting engine using the trained model."""

    def __init__(self, champs):
        """Store the list of all available champions."""
        self.champs = champs

    def greedy_draft(self, enemy_team, bans=None, k_per_step=1, verbose=True):
        """
        Build a 5-champ ally team by always choosing the next best pick.

        Parameters
        ----------
        enemy_team : list[str]
            The 5 champions picked by the enemy team.
        bans : list[str] or None
            Banned champions.
        k_per_step : int
            Number of recommended picks to evaluate (usually 1).
        verbose : bool
            If True, prints each pick step.
        
        Returns
        -------
        ally_team : list[str]
            The completed 5-champ ally composition.
        final_prob : float
            Predicted win probability for the final team.
        """
        bans = bans or []
        ally_team = []

        step = 0
        while len(ally_team) < 5:
            step += 1

            top_recos = recommend_next_pick(
                enemyTeam=enemy_team,
                currentPicks=ally_team,
                bans=bans,
                k=k_per_step
            )

            if not top_recos:
                if verbose:
                    print("No legal champions left to pick.")
                break

            best_champ, best_prob = top_recos[0]
            ally_team.append(best_champ)

            if verbose:
                print(f"Step {step}: picked {best_champ} (prob={best_prob:.3f})")

        final_prob = probability(ally_team, enemy_team, bans)
        return ally_team, final_prob
    
def main():
    """
    Small local test to verify the greedy draft works.
    """
   
    greedy = GreedyDraft(possibleChamps)

    # Create a random enemy team and bans just for testing
    enemy = random.sample(possibleChamps, 5)
    bans = random.sample([c for c in possibleChamps if c not in enemy], 10)

    print("=== Greedy Draft Self-Test ===")
    print("Enemy team:", ", ".join(enemy))
    print("Bans:", ", ".join(bans))

    team, prob = greedy.greedy_draft(enemy_team=enemy, bans=bans, verbose=True)

    print("\nFinal ally team:", ", ".join(team))
    print(f"Final win probability: {prob:.3f}")


if __name__ == "__main__":
    main()