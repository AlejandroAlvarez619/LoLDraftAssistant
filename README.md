
# League of Legends Automatic Draft Assistant

In League of Legends, the champion draft phase is crucial for securing strategic advantages. However, picking effective team compositions is difficult because of the numerous interactions among champions. This study introduces a machine learning based approach to analyze drafts using logistic regression on high-dimensional features representing champion selections, bans, and interactions between teams. Experimental results demonstrate that the model effectively captures meaningful draft-related patterns and consistently outperforms random baselines in ranking and probabilistic evaluations. Although draft-only prediction is inherently limited, the proposed approach offers practical support for making decisions about team composition during the selection phase.


## Installation

First of all, download or clone the repo:

```bash
  git clone https://github.com/skyscrabble/AutomaticDraftAssistant
  cd yourproject
```
Create a virtual environment (optional):

```bash
  python -m venv venv
  source venv/bin/activate      # macOS/Linux
  venv\Scripts\activate         # Windows
```

Then, install dependencies:

```bash
  pip install -r requirements.txt
```

## Usage/Examples

Simply execute the main.py file and wait a few seconds to run the program:
```bash
  python main.py
```

Once in the main menu interface, input the option you want to test:
```bash
  [1] Quick last-pick recommendation demo
  [2] Full greedy draft vs random enemy team
  [3] Full greedy draft vs custom enemy team (write the name of 5 characters separed by commas)
  [0] Exit
```

For training, you can simply run the LogisticRegression.py file and there will be a demo available.
```bash
  python LogisticRegression.py
```

For testing and evaluation, run Evaluation.py and check the ./evaluation folder.
```bash
  python Evaluation.py
```

You can try with different models changing the hyperparameters in LogisticRegression.py. Reproducible models are available in
./evaluation/models.txt


## Authors

- [@skyscrabble](https://www.github.com/skyscrabble)
- [@hannahsteindorfer](https://www.github.com/hannahsteindorfer)
- [@Luca08-edu](https://www.github.com/Luca08-edu)
- [@AlejandroAlvarez619](https://www.github.com/AlejandroAlvarez619)

## Appendix

For detailed info about the project and the utilized formulas, check the 'doc' folder within the repo.

