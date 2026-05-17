from pathlib import Path

import numpy as np

from dynamic_pricing.env import MicroloanPricingEnv, RATE_BUCKETS
from dynamic_pricing.train import save_model_artifacts


def test_seeded_environment_is_reproducible():
    env_a = MicroloanPricingEnv()
    env_b = MicroloanPricingEnv()

    obs_a, _ = env_a.reset(seed=123)
    obs_b, _ = env_b.reset(seed=123)

    assert np.array_equal(obs_a, obs_b)

    next_a, reward_a, terminated_a, truncated_a, info_a = env_a.step(2)
    next_b, reward_b, terminated_b, truncated_b, info_b = env_b.step(2)

    assert np.array_equal(next_a, next_b)
    assert reward_a == reward_b
    assert terminated_a == terminated_b
    assert truncated_a == truncated_b
    assert info_a == info_b


def test_repaid_reward_is_interest_income_only():
    env = MicroloanPricingEnv()
    env.reset(seed=123)
    env._client = np.array([0.8, 0.5, 0.4, 0.5, 1.0], dtype=np.float32)
    env._repayment_prob = lambda rate: 1.0

    reward = env._compute_reward(2)

    assert reward == float(RATE_BUCKETS[2] * 0.4)


def test_fairness_metrics_are_only_emitted_on_terminal_step():
    env = MicroloanPricingEnv(max_steps=2)
    env.reset(seed=123)

    _, _, terminated, _, info = env.step(0)

    assert not terminated
    assert info == {}

    _, _, terminated, _, info = env.step(1)

    assert terminated
    assert "fairness" in info

    env.reset(seed=123)
    _, _, terminated, _, info = env.step(0)

    assert not terminated
    assert info == {}


def test_save_model_artifacts_creates_output_dir(tmp_path: Path):
    class FakeModel:
        def save(self, path: str) -> None:
            Path(path).write_text("model")

    class FakeEnv:
        def save(self, path: str) -> None:
            Path(path).write_text("normalizer")

    output_dir = tmp_path / "missing" / "models"

    save_model_artifacts(FakeModel(), FakeEnv(), output_dir)

    assert (output_dir / "ppo_microloan.zip").read_text() == "model"
    assert (output_dir / "vec_normalize.pkl").read_text() == "normalizer"
