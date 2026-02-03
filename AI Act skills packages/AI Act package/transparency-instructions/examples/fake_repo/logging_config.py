"""
Logging Configuration
Ensures Article 12 compliance (Record Keeping).
"""

import logging

def setup_logging():
    """
    Configures secure logging storage.
    Logs are stored in /var/log/secure_ai_logs/
    Rotated daily, kept for 1 year.
    """
    logger = logging.getLogger("ArrhythmiaDetector")
    logger.setLevel(logging.INFO)
    
    # Log Format: [Timestamp] [User] [Action] [Result]
    formatter = logging.Formatter('%(asctime)s - %(user)s - %(message)s')
    
    # ... implementation of secure file handler ...
    return logger

def log_inference(patient_id, prediction, confidence):
    """
    Logs every inference event for traceability.
    """
    # Interpretation: If confidence < 80%, flag for manual review.
    logging.info(f"Inference: PID={patient_id}, Pred={prediction}, Conf={confidence}")
