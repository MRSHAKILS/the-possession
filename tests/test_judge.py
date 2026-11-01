import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_data import apply_judge
from judge import parse_verdict


class ParseVerdictTests(unittest.TestCase):
    def test_reads_yes_and_no(self):
        self.assertIs(parse_verdict("Yes"), True)
        self.assertIs(parse_verdict(" no."), False)
        self.assertIs(parse_verdict("**Yes**, it does."), True)

    def test_unclear_replies_stay_unclear(self):
        self.assertIsNone(parse_verdict(""))
        self.assertIsNone(parse_verdict("Perhaps"))


class ApplyJudgeTests(unittest.TestCase):
    def test_replaces_scores_and_drops_unclear_trials(self):
        trials = [{"haunted": 0.9}, {"haunted": 0.1}, {"haunted": 0.9}]
        judged = apply_judge(trials, {"verdicts": [False, True, None]})
        self.assertEqual([t["haunted"] for t in judged], [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
