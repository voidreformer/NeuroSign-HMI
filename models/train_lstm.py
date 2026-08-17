import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import argparse
import os


def load_data(data_path: str):
    data = np.load(data_path)
    X = data['X'].astype(np.float32)
    y = data['y'].astype(np.int32)
    return X, y


def build_model(input_shape: tuple, num_classes: int) -> Sequential:
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=input_shape),
        Dropout(0.3),
        LSTM(64, return_sequences=False),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])
    model.compile(
        optimizer=Adam(),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def convert_to_tflite_int8(model: tf.keras.Model, output_path: str):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    print(f"TFLite INT8 model saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Train LSTM for gesture recognition')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    args = parser.parse_args()

    data_path = 'gestures_dataset.npz'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    X, y = load_data(data_path)
    num_classes = 7

    y_cat = to_categorical(y, num_classes=num_classes)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y_cat, test_size=0.2, random_state=42, stratify=y
    )

    model = build_model(input_shape=X.shape[1:], num_classes=num_classes)
    model.summary()

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=[early_stop],
        verbose=1
    )

    y_pred_probs = model.predict(X_val, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = np.argmax(y_val, axis=1)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=[f'Class {i}' for i in range(num_classes)]))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_true, y_pred)
    print(cm)

    convert_to_tflite_int8(model, 'gesture_lstm_int8.tflite')


if __name__ == '__main__':
    main()