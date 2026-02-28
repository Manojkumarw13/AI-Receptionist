import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import os
import logging
from concurrent.futures import ThreadPoolExecutor

# FIX BUG-N17: Use a module-level logger instead of calling logging.basicConfig().
logger = logging.getLogger(__name__)

# Background thread pool for non-blocking training
_executor = ThreadPoolExecutor(max_workers=1)


class AppointmentPredictor:
    def __init__(self, data_file="appointment_data.csv"):
        if os.path.isabs(data_file):
            self.data_file = data_file
        else:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = os.path.join(BASE_DIR, "data", data_file)
        self.model = None
        self.is_trained = False
        # Fix #3: Train asynchronously so FastAPI startup is not blocked
        _executor.submit(self._train_model)

    def _train_model(self):
        """Trains the Random Forest model (runs in background thread)."""
        if not os.path.exists(self.data_file):
            logger.warning(f"Data file {self.data_file} not found. ML predictions will default to 'available'.")
            return

        try:
            df = pd.read_csv(self.data_file, parse_dates=['date'], dayfirst=True)

            # Feature engineering
            df['weekday'] = df['date'].dt.dayofweek
            df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour

            X = df[['weekday', 'hour', 'duration']]
            y = df['status']

            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            train_accuracy = self.model.score(X, y)
            self.is_trained = True
            logger.info(
                f"ML model trained on {len(df)} samples. Accuracy: {train_accuracy:.2%}"
            )

        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
            self.is_trained = False

    def predict_availability(self, date_str, time_str, duration):
        """
        Predicts if an appointment slot is likely to be confirmed or cancelled.

        Args:
            date_str (str): Date in 'YYYY-MM-DD' format.
            time_str (str): Time in 'HH:MM' format.
            duration (int): Duration in minutes.

        Returns:
            tuple: (is_available (bool), message (str))
        """
        if not self.is_trained:
            return True, "Model not trained yet, assuming available."

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekday = date_obj.weekday()
            hour = datetime.strptime(time_str, '%H:%M').hour

            prediction = self.model.predict([[weekday, hour, duration]])

            if prediction[0] == 'confirmed':
                return True, "Slot appears to be optimal."
            else:
                return False, "This time slot has a high risk of cancellation based on historical data."
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return True, f"Error in prediction: {e}"


# Global instance — training starts in background immediately
appointment_predictor = AppointmentPredictor()

