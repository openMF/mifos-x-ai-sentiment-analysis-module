from stable_baselines3 import DQN
from training.rl_models.ppo.train import LoggingCallback
import os

def train_dqn(env, db_session, total_timesteps=1000, callback=None, experiment_id=None, **kwargs):
    learning_rate = kwargs.get("learning_rate", 0.0001)
    batch_size = kwargs.get("batch_size", 32)
    gamma = kwargs.get("gamma", 0.99)
    
    # DQN is for discrete action spaces
    model = DQN("MlpPolicy", env, verbose=1, learning_rate=learning_rate, batch_size=batch_size, gamma=gamma)
    
    cbs = [LoggingCallback(db_session, "DQN")]
    if callback:
        cbs.extend(callback if isinstance(callback, list) else [callback])
        
    model.learn(total_timesteps=total_timesteps, callback=cbs)
    
    filename = f"dqn_experiment_{experiment_id}.zip" if experiment_id else "dqn_model.zip"
    save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models', filename)
    model.save(save_path)
    return model


