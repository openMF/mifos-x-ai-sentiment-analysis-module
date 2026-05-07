import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback

from dynamic_pricing.env import MicroloanPricingEnv


class FairnessLoggingCallback(BaseCallback):
    """Logs episode-level reward and fairness metrics after each rollout."""

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards: list[float] = []
        self._current_rewards: list[float] = []

    def _on_step(self) -> bool:
        self._current_rewards.append(self.locals["rewards"][0])
        infos = self.locals.get("infos", [{}])
        dones = self.locals["dones"]

        if dones[0]:
            ep_reward = sum(self._current_rewards)
            self.episode_rewards.append(ep_reward)
            fm = infos[0].get("fairness", {})
            avg = float(np.mean(self.episode_rewards[-20:]))
            n = len(self.episode_rewards)
            disp = fm.get("disparity", 0.0)
            high_r = fm.get("avg_rate_high_credit", 0.0)
            low_r = fm.get("avg_rate_low_credit", 0.0)
            print(
                f"Episode {n:>4d} | avg_reward(last 20): {avg:>7.2f} | "
                f"disp: {disp:.4f} | "
                f"high_rate: {high_r:.3f} low_rate: {low_r:.3f}"
            )
            self._current_rewards = []
        return True


def train():
    env = DummyVecEnv([lambda: MicroloanPricingEnv(max_steps=100)])
    env = VecNormalize(env, norm_obs=True, norm_reward=False)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=0,
    )

    callback = FairnessLoggingCallback()
    model.learn(total_timesteps=20_000, callback=callback)

    model.save("models/ppo_microloan.zip")
    env.save("models/vec_normalize.pkl")

    print("\n--- Training complete ---")
    print(f"Total episodes: {len(callback.episode_rewards)}")
    print(f"Final avg reward (last 20): {np.mean(callback.episode_rewards[-20:]):.2f}")


if __name__ == "__main__":
    train()
