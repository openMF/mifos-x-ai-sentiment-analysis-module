import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional

RATE_BUCKETS = np.array([0.05, 0.10, 0.15, 0.20, 0.25], dtype=np.float32)


class MicroloanPricingEnv(gym.Env):
    """
    Gymnasium environment for dynamic micro-loan pricing.

    State (5-dim, all normalized 0-1):
        [credit_score, income, loan_amount, term, is_returning]

    Action: Discrete(5) → interest rate buckets {5%, 10%, 15%, 20%, 25%}

    Reward per step:
        profit = interest_income if repaid else -loan_amount

    Episode ends after `max_steps` clients.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, max_steps: int = 100, render_mode: Optional[str] = None):
        super().__init__()

        self.max_steps = max_steps
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(5,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(len(RATE_BUCKETS))

        self.step_count = 0
        self._client = None

        # Fairness tracking (snapshot survives VecEnv auto-reset)
        self._group_rates: dict[str, list[float]] = {"high": [], "low": []}
        self._last_fairness: dict | None = None

    def _generate_client(self) -> np.ndarray:
        credit_score = np.random.uniform(0.3, 1.0)
        income = np.random.uniform(0.2, 1.0)
        loan_amount = np.random.uniform(0.1, 1.0)
        term = np.random.uniform(0.1, 1.0)
        is_returning = float(np.random.randint(0, 2))
        return np.array(
            [credit_score, income, loan_amount, term, is_returning],
            dtype=np.float32,
        )

    def _repayment_prob(self, rate: float) -> float:
        cs = self._client[0]
        return 1.0 / (1.0 + np.exp(-(cs * 3.0 - rate * 2.0)))

    def _compute_reward(self, action: int) -> float:
        rate = RATE_BUCKETS[action]
        loan = float(self._client[2])
        prob = self._repayment_prob(rate)
        repaid = np.random.random() < prob
        if repaid:
            return (1.0 + rate) * loan
        else:
            return -loan

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[dict] = None
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self.step_count = 0
        self._client = self._generate_client()
        self._group_rates = {"high": [], "low": []}
        return self._client.copy(), {}

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        assert self._client is not None, "Call reset() before step()."
        rate = float(RATE_BUCKETS[action])
        reward = self._compute_reward(action)

        # Fairness tracking
        group = "high" if self._client[0] >= 0.6 else "low"
        self._group_rates[group].append(rate)

        self.step_count += 1
        terminated = self.step_count >= self.max_steps
        truncated = False

        if terminated:
            self._last_fairness = self.get_fairness_metrics()

        self._client = self._generate_client()
        info = {"fairness": self._last_fairness} if self._last_fairness else {}
        return self._client.copy(), reward, terminated, truncated, info

    def get_fairness_metrics(self) -> dict:
        avg_high = np.mean(self._group_rates["high"]) if self._group_rates["high"] else 0.0
        avg_low = np.mean(self._group_rates["low"]) if self._group_rates["low"] else 0.0
        return {
            "avg_rate_high_credit": float(avg_high),
            "avg_rate_low_credit": float(avg_low),
            "disparity": float(abs(avg_high - avg_low)),
            "count_high": len(self._group_rates["high"]),
            "count_low": len(self._group_rates["low"]),
        }

    def render(self):
        if self.render_mode == "human":
            print(
                f"Step {self.step_count}/{self.max_steps} | "
                f"client: cs={self._client[0]:.2f} income={self._client[1]:.2f}"
            )
