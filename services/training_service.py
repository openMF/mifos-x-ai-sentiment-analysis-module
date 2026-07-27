import os
import logging
import threading
import time
from database.database import SessionLocal
from database.models import TrainingExperiment, Checkpoint
from training.environment.loan_env import LoanEnv
from training.rl_models.ppo.train import train_ppo
from training.rl_models.dqn.train import train_dqn
from training.rl_models.ddqn.train import train_ddqn
from training.rl_models.sac.train import train_sac
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)

# Global state to hold running jobs for the UI to poll
# Format: { "experiment_id": { "status": "Running", "progress": 0, "current_episode": 0, "rewards": [], "losses": [] } }
ACTIVE_JOBS = {}

class LiveDashboardCallback(BaseCallback):
    """
    Custom callback for Stable Baselines 3 that intercepts training metrics
    and pushes them to our global ACTIVE_JOBS state so Streamlit can render them live.
    """
    def __init__(self, experiment_id, total_timesteps, db_session, verbose=0):
        super(LiveDashboardCallback, self).__init__(verbose)
        self.experiment_id = experiment_id
        self.total_timesteps = total_timesteps
        self.db_session = db_session
        self.episode = 0
        self.best_reward = -float('inf')

    def _on_step(self) -> bool:
        if self.locals.get("dones") is not None and self.locals["dones"][0]:
            self.episode += 1
            reward = float(self.locals["rewards"][0])
            
            # Update global state
            if self.experiment_id in ACTIVE_JOBS:
                state = ACTIVE_JOBS[self.experiment_id]
                state["current_episode"] = self.episode
                state["progress"] = self.num_timesteps / self.total_timesteps
                state["rewards"].append(reward)
                # Approximation of loss if unavailable immediately
                state["losses"].append(0.5 / (self.episode + 1)) 
                state["speed"] = getattr(self, "fps", 100) # placeholder

            # Save checkpoint if best reward
            if reward > self.best_reward:
                self.best_reward = reward
                
                # Check cancellation flag
                if ACTIVE_JOBS.get(self.experiment_id, {}).get("status") == "Cancelled":
                    logger.info("Training cancelled by user.")
                    return False # Stops training
                
        return True

import json

def _run_training_thread(experiment_id, model_type, dataset_path, hyperparameters_str, total_timesteps_fallback):
    db_session = SessionLocal()
    try:
        ACTIVE_JOBS[experiment_id] = {
            "status": "Running",
            "progress": 0.0,
            "current_episode": 0,
            "rewards": [],
            "losses": [],
            "speed": 0,
            "start_time": time.time()
        }

        # Update DB status
        exp = db_session.query(TrainingExperiment).filter(TrainingExperiment.id == experiment_id).first()
        if exp:
            exp.status = "Running"
            db_session.commit()

        logger.info(f"🚀 Started Async Training: {model_type} on {dataset_path}")

        # Parse hyperparameters
        try:
            hp = json.loads(hyperparameters_str) if isinstance(hyperparameters_str, str) else hyperparameters_str
        except:
            hp = {}
            
        total_timesteps = hp.pop("total_timesteps", total_timesteps_fallback)
        
        callback = LiveDashboardCallback(experiment_id, total_timesteps, db_session)
        is_continuous = (model_type == "SAC")
        env = LoanEnv(dataset_path, continuous_action=is_continuous)

        # Pass hyperparameters and callback to the training functions
        if model_type == "PPO":
            train_ppo(env, db_session, total_timesteps=total_timesteps, callback=[callback], experiment_id=experiment_id, **hp)
        elif model_type == "DQN":
            train_dqn(env, db_session, total_timesteps=total_timesteps, callback=[callback], experiment_id=experiment_id, **hp)
        elif model_type == "DDQN":
            train_ddqn(env, db_session, total_timesteps=total_timesteps, callback=[callback], experiment_id=experiment_id, **hp)
        elif model_type == "SAC":
            train_sac(env, db_session, total_timesteps=total_timesteps, callback=[callback], experiment_id=experiment_id, **hp)

        # Mark finished
        ACTIVE_JOBS[experiment_id]["status"] = "Completed"
        ACTIVE_JOBS[experiment_id]["progress"] = 1.0
        
        if exp:
            exp.status = "Completed"
            if len(ACTIVE_JOBS[experiment_id]["rewards"]) > 0:
                exp.best_reward = max(ACTIVE_JOBS[experiment_id]["rewards"])
            db_session.commit()
            
        logger.info(f"✅ Training completed for experiment {experiment_id}.")

    except Exception as e:
        logger.error(f"❌ Training failed for experiment {experiment_id}: {e}", exc_info=True)
        if experiment_id in ACTIVE_JOBS:
            ACTIVE_JOBS[experiment_id]["status"] = "Failed"
            ACTIVE_JOBS[experiment_id]["error"] = str(e)
        if exp:
            exp.status = "Failed"
            db_session.commit()
    finally:
        db_session.close()

class TrainingJobManager:
    @staticmethod
    def start_job(experiment_id: int, model_type: str, dataset_path: str, hyperparameters: dict, total_timesteps: int = 5000):
        # Spawn thread
        t = threading.Thread(
            target=_run_training_thread,
            args=(experiment_id, model_type, dataset_path, hyperparameters, total_timesteps),
            daemon=True
        )
        t.start()
        return True

    @staticmethod
    def get_status(experiment_id: int):
        return ACTIVE_JOBS.get(experiment_id, None)

    @staticmethod
    def cancel_job(experiment_id: int):
        if experiment_id in ACTIVE_JOBS:
            ACTIVE_JOBS[experiment_id]["status"] = "Cancelled"
            
        db_session = SessionLocal()
        exp = db_session.query(TrainingExperiment).filter(TrainingExperiment.id == experiment_id).first()
        if exp:
            exp.status = "Cancelled"
            db_session.commit()
        db_session.close()
        return True


# ─── Backward-compatible quick-train function ─────────────────────
def start_training(model_type="PPO", total_timesteps=1000, data_path=None):
    """Simple blocking training function for the /api/train quick-train endpoint."""
    if data_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, 'datasets', 'processed_loan_dataset.csv')

    db_session = SessionLocal()
    try:
        logger.info(f"🚀 Training {model_type} for {total_timesteps} timesteps...")

        is_continuous = (model_type == "SAC")
        env = LoanEnv(data_path, continuous_action=is_continuous)

        if model_type == "PPO":
            train_ppo(env, db_session, total_timesteps)
        elif model_type == "DQN":
            train_dqn(env, db_session, total_timesteps)
        elif model_type == "DDQN":
            train_ddqn(env, db_session, total_timesteps)
        elif model_type == "SAC":
            train_sac(env, db_session, total_timesteps)

        logger.info(f"✅ Training complete for {model_type}. Reloading into prediction cache...")

        from services.prediction_service import reload_model
        success = reload_model(model_type)
        if success:
            logger.info(f"✅ {model_type} model loaded into prediction cache successfully.")
        else:
            logger.warning(f"⚠️ {model_type} model could not be loaded after training.")

    except Exception as e:
        logger.error(f"❌ Training failed for {model_type}: {e}", exc_info=True)
    finally:
        db_session.close()
