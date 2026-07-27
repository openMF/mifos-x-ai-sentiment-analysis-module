from stable_baselines3 import SAC
from training.rl_models.ppo.train import LoggingCallback
import os

def train_sac(env, db_session, total_timesteps=1000, callback=None, experiment_id=None, **kwargs):
    learning_rate = kwargs.get("learning_rate", 0.0003)
    batch_size = kwargs.get("batch_size", 256)
    gamma = kwargs.get("gamma", 0.99)
    ent_coef = kwargs.get("ent_coef", "auto")
    
    # SAC is for continuous action spaces
    model = SAC("MlpPolicy", env, verbose=1, learning_rate=learning_rate, batch_size=batch_size, gamma=gamma, ent_coef=ent_coef)
    
    cbs = [LoggingCallback(db_session, "SAC")]
    if callback:
        cbs.extend(callback if isinstance(callback, list) else [callback])
        
    model.learn(total_timesteps=total_timesteps, callback=cbs)
    
    filename = f"sac_experiment_{experiment_id}.zip" if experiment_id else "sac_model.zip"
    save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models', filename)
    model.save(save_path)
    return model


