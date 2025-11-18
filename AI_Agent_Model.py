import numpy as np
import yfinance as yf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import warnings

warnings.filterwarnings("ignore")

def predict_stock(symbol: str, epochs: int = 3, min_history: int = 150):

    # 1️⃣ ROBUST DATA DOWNLOAD (CLOUD SAFE)
    data = yf.download(
        symbol,
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if data is None or data.empty:
        print("⚠ No data returned from Yahoo Finance")
        return None

    if "Close" not in data.columns:
        print("⚠ Close column missing")
        return None

    close_series = data["Close"].dropna()
    if len(close_series) < min_history:
        print("⚠ Not enough history")
        return None

    close = close_series.values.reshape(-1, 1)

    # 2️⃣ SCALING
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(close)

    # 3️⃣ CREATE SEQUENCES
    seq_len = 60
    X, y = [], []
    for i in range(seq_len, len(scaled)):
        X.append(scaled[i-seq_len:i, 0])
        y.append(scaled[i, 0])

    X = np.array(X).reshape(-1, seq_len, 1)
    y = np.array(y)

    # 4️⃣ LIGHTWEIGHT MODEL FOR STREAMLIT CLOUD
    model = Sequential([
        LSTM(32, return_sequences=True, input_shape=(seq_len, 1)),
        Dropout(0.1),
        LSTM(32),
        Dropout(0.1),
        Dense(16, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=epochs, batch_size=32, verbose=0)

    # 5️⃣ NEXT DAY PREDICTION
    last_seq = scaled[-seq_len:].reshape(1, seq_len, 1)
    next_scaled = model.predict(last_seq, verbose=0)[0][0]
    next_price = float(scaler.inverse_transform([[next_scaled]])[0][0])

    # 6️⃣ EVALUATION (LAST 20 DAYS)
    test_size = 20
    actual = close[-test_size:].flatten()
    X_test = X[-test_size:]

    pred_scaled = model.predict(X_test, verbose=0)
    preds = scaler.inverse_transform(pred_scaled).flatten()

    dates = close_series.index[-test_size:]

    mae = np.mean(np.abs(preds - actual))
    score = max(0, 1 - mae / (np.mean(np.abs(actual)) + 1e-9))

    return score, float(close[-1]), next_price, (actual, preds, dates)
