import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from datetime import datetime
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

class AppointmentPredictor:
    def __init__(self, data_file="appointment_data.csv"):
        # Get absolute path to data file
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = os.path.join(BASE_DIR, "data", "appointment_data.csv")
        self.model = None
        self.is_trained = False
        self._train_model()

    def _train_model(self):
        """Trains the Random Forest model on initialization."""
        if not os.path.exists(self.data_file):
            # FIXED: Better error handling and logging
            logging.error(f"CRITICAL: Data file {self.data_file} not found!")
            logging.error("ML predictions will default to 'available' - model not trained")
            logging.error(f"Expected file location: {self.data_file}")
            logging.warning("To enable ML predictions, create the data file with appointment history")
            return

        try:
            df = pd.read_csv(self.data_file, parse_dates=['date'], dayfirst=True)
            
            # Feature engineering
            df['weekday'] = df['date'].dt.dayofweek
            df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour
            
            # Features and Target
            X = df[['weekday', 'hour', 'duration']]
            y = df['status']

            # constant split for reproducibility, though re-training on full data might be better for production
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
            self.is_trained = True
            logging.info("Appointment Prediction Model trained successfully.")
            
        except Exception as e:
            # FIXED: Better error handling
            logging.error(f"CRITICAL: Failed to train ML model: {e}")
            logging.error("ML predictions will default to 'available'")
            self.is_trained = False

    def predict_availability(self, date_str, time_str, duration):
        """
        Predicts if an appointment slot is likely to be confirmed or cancelled/unavailable.
        
        Args:
            date_str (str): Date in 'YYYY-MM-DD' format.
            time_str (str): Time in 'HH:MM' format.
            duration (int): Duration in minutes.
            
        Returns:
            tuple: (is_available (bool), message (str))
        """
        if not self.is_trained:
             return True, "Model not trained, assuming available."

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
            logging.error(f"Prediction error: {e}")
            return True, f"Error in prediction: {e}"

# Global instance
appointment_predictor = AppointmentPredictor()
