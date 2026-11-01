"""Run with: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.ghost import haunt


def stub_model(layer_count):
    layers = torch.nn.ModuleList(torch.nn.Identity() for _ in range(layer_count))
    return SimpleNamespace(model=SimpleNamespace(layers=layers))


def stub_ghost(layer_count, clean_mean=0.5):
    vector = torch.tensor([1.0, 0.0, 0.0])
    return {
        layer: {"vector": vector, "scale": 2.0, "clean_mean": clean_mean, "clean_std": 0.5}
        for layer in range(layer_count)
    }


def forward(model, hidden):
    for layer in model.model.layers:
        hidden = layer(hidden)
    return hidden


class HauntTests(unittest.TestCase):
    def setUp(self):
        self.model = stub_model(4)
        self.ghost = stub_ghost(4)
        self.hidden = torch.tensor([[[0.5, 1.0, -1.0]]])

    def test_possession_adds_scaled_vector(self):
        with haunt(self.model, self.ghost, strength=0.5, possess_layers=[1]):
            out = forward(self.model, self.hidden)
        self.assertEqual(out.tolist(), [[[1.5, 1.0, -1.0]]])

    def test_exorcism_restores_clean_projection_without_knowing_strength(self):
        for strength in (0.1, 0.5, 3.0):
            with haunt(self.model, self.ghost, strength=strength, possess_layers=[0], exorcise_layers=[2]):
                out = forward(self.model, self.hidden)
            self.assertAlmostEqual(out[0, 0, 0].item(), 0.5, places=5)
            self.assertEqual(out[0, 0, 1:].tolist(), [1.0, -1.0])

    def test_reading_reports_sigma_from_clean(self):
        reading = {}
        with haunt(self.model, self.ghost, strength=0.5, possess_layers=[1], reading=reading):
            forward(self.model, self.hidden)
        self.assertAlmostEqual(reading[0][0], 0.0)
        self.assertAlmostEqual(reading[1][0], 2.0)

    def test_hooks_are_removed_on_exit(self):
        with haunt(self.model, self.ghost, strength=1.0, possess_layers=[0]):
            pass
        self.assertEqual(forward(self.model, self.hidden).tolist(), self.hidden.tolist())


if __name__ == "__main__":
    unittest.main()
