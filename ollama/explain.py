import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma2:2b"

def generate_explanation(applicant_data: dict, prediction_data: dict, model=DEFAULT_MODEL) -> dict:
    """
    Calls local Ollama API to generate human-readable explanations of the RL decision.
    """
    prompt = f"""
    You are an expert AI Banking Assistant. The Reinforcement Learning (RL) ensemble has made a loan decision.
    Your job is ONLY to explain this decision clearly. NEVER change the interest rate or decision.

    Applicant Data:
    {json.dumps(applicant_data, indent=2)}

    RL Engine Prediction:
    {json.dumps(prediction_data, indent=2)}

    Please provide a JSON response with exactly these keys:
    1. "customer_friendly_explanation": A polite, simple explanation for the customer.
    2. "officer_technical_explanation": A detailed technical explanation for the loan officer justifying the risk vs reward.
    3. "suggested_improvements": What the applicant can do to get a better rate next time.
    
    Return ONLY valid JSON.
    """

    try:
        # Auto-detect available model if the requested one is missing
        try:
            tags_res = requests.get("http://localhost:11434/api/tags", timeout=2)
            if tags_res.status_code == 200:
                local_models = [m['name'] for m in tags_res.json().get('models', [])]
                if local_models and model not in local_models:
                    model = local_models[0]
                    logger.info(f"Model not found locally, falling back to {model}")
        except:
            pass

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "{}")
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Ollama")
                return {
                    "customer_friendly_explanation": "[FALLBACK] Error parsing AI response.",
                    "officer_technical_explanation": response_text,
                    "suggested_improvements": "N/A"
                }
        else:
            logger.error(f"Ollama API Error: {response.text}")
            return {"error": "Ollama API returned an error."}
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama is not running locally on port 11434.")
        rate = prediction_data.get("recommended_interest_rate")
        status = "APPROVED" if rate else "REJECTED"
        credit = applicant_data.get("credit_score", 0)
        debt = applicant_data.get("existing_debt", 0)
        income = applicant_data.get("income", 1)
        model_used = prediction_data.get("best_model", "RL Ensemble")
        
        customer_msg = f"Your application was {status}."
        if rate:
            customer_msg += f" You have been offered an interest rate of {rate}%. This is based on your credit score of {credit} and debt-to-income profile."
        else:
            customer_msg += " Unfortunately, we could not offer you a loan at this time due to your risk profile."
            
        tech_msg = f"Engine: {model_used}. Decision: {status}. "
        tech_msg += f"Key metrics: Credit={credit}, Debt/Income ratio={round(debt/income, 2)}. "
        tech_msg += "The agent balanced the applicant's risk against expected reward to select this continuous rate."
        
        return {
            "customer_friendly_explanation": f"[FALLBACK] {customer_msg}",
            "officer_technical_explanation": f"[FALLBACK] {tech_msg}",
            "suggested_improvements": "[FALLBACK] Lower your existing debt ratio and improve your credit score to secure a better rate in the future."
        }
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return {"error": str(e)}

def analyze_training_run(algorithm: str, hyperparameters: dict, best_reward: float, status: str, model=DEFAULT_MODEL) -> str:
    """
    Calls local Ollama API to generate a brief summary of how well the model trained based on hyperparameters.
    """
    prompt = f"""
    You are an expert Machine Learning Engineer specializing in Reinforcement Learning.
    Please write a brief 2-3 sentence analysis of the following RL training experiment.
    
    Algorithm: {algorithm}
    Hyperparameters: {json.dumps(hyperparameters)}
    Final Status: {status}
    Best Reward Achieved: {best_reward}
    
    Keep the explanation technical but concise. 
    Explain what the hyperparameters mean for this specific algorithm and if the reward is reasonable.
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Analysis not generated.")
        return "[Error: Ollama API returned an error.]"
    except requests.exceptions.ConnectionError:
        return f"[FALLBACK] The {algorithm} model reached a best reward of {best_reward}. The hyperparameters used were {json.dumps(hyperparameters)}. This indicates the model learned a policy to some degree, but further tuning of learning rate and batch size might be required to achieve convergence."
    except Exception as e:
        return f"[Error connecting to Ollama: {str(e)}]"

def generate_portfolio_summary(stats: dict, model=DEFAULT_MODEL) -> str:
    """
    Calls local Ollama API to generate an Executive Summary for the portfolio report.
    """
    prompt = f"""
    You are an expert Chief Risk Officer at a modern AI-driven bank.
    Please write a 2 paragraph Executive Summary of the following portfolio data:
    
    Total Applications: {stats.get('total_apps')}
    Approval Rate: {stats.get('approval_rate')}%
    Average Risk Score: {stats.get('avg_risk')}
    Most Common Loan Purpose: {stats.get('top_purpose')}
    Dominant AI Model: {stats.get('top_model')}
    
    Keep the tone professional and analytical. State if the portfolio looks healthy or risky.
    """
    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "")
        return "[Error generating summary]"
    except requests.exceptions.ConnectionError:
        return "[FALLBACK] The portfolio shows an approval rate of {:.1f}% across {} applications. The average risk score is {:.2f}, indicating standard market conditions.".format(stats.get('approval_rate', 0), stats.get('total_apps', 0), stats.get('avg_risk', 0))
    except Exception as e:
        return f"[Error: {str(e)}]"

def generate_fairness_audit_summary(audit_metrics: dict, model=DEFAULT_MODEL) -> str:
    """
    Calls local Ollama API to generate a brief summary for the fairness audit.
    """
    prompt = f"""
    You are a Regulatory Compliance Officer (ECOA specialist).
    Review these Disparate Impact (Four-Fifths rule) metrics for our AI loan models:
    
    {json.dumps(audit_metrics, indent=2)}
    
    (Note: A ratio < 0.8 means potential bias against the protected class).
    Write a 1-paragraph summary on whether the model is fair and legally compliant, or if urgent retraining is needed.
    """
    try:
        payload = {"model": model, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "")
        return "[Error generating audit]"
    except requests.exceptions.ConnectionError:
        return "[FALLBACK] Automated audit check completed. If any metric is below 0.8, the AI model exhibits disparate impact and must be reviewed immediately to ensure ECOA compliance."
    except Exception as e:
        return f"[Error: {str(e)}]"
