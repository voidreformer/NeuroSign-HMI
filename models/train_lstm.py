import os
import argparse
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import LSTM, Dropout, Dense, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


def load_data(data_path: str):
    """Safely loads training sequences and integer labels using a context manager."""
    with np.load(data_path) as data:
        X = data['X'].astype(np.float32)
        y = data['y'].astype(np.int32)
    return X, y


def build_model(input_shape: tuple, num_classes: int) -> Model:
    """Builds an unrolled 2-layer LSTM compatible with pure TFLite & GPU delegates."""
    inputs = Input(shape=input_shape, name="hand_landmarks_30x63")
    x = LSTM(64, return_sequences=True, unroll=True)(inputs)
    x = Dropout(0.25)(x)
    x = LSTM(32, return_sequences=False, unroll=True)(x)
    x = Dropout(0.25)(x)
    x = Dense(32, activation='relu')(x)
    outputs = Dense(num_classes, activation='softmax', name="gesture_probabilities")(x)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def convert_to_tflite_int8(model: Model, X_sample: np.ndarray, output_path: str):
    """Converts Keras model to pure TFLite INT8 format with representative calibration dataset."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    def representative_dataset():
        for i in range(min(100, len(X_sample))):
            yield [X_sample[i:i+1].astype(np.float32)]

    converter.representative_dataset = representative_dataset
    tflite_model = converter.convert()

    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    print(f"[EXPORT] TFLite model successfully saved to {output_path} ({len(tflite_model)} bytes)")


def main():
    parser = argparse.ArgumentParser(description='Train 1D-LSTM for 3D gesture recognition')
    parser.add_argument('--epochs', type=int, default=30, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    args = parser.parse_args()

    models_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(models_dir, 'gestures_dataset.npz')
    if not os.path.exists(data_path):
        data_path = 'gestures_dataset.npz'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    output_tflite = os.path.join(models_dir, 'gesture_lstm_int8.tflite')
    output_keras = os.path.join(models_dir, 'gesture_lstm.keras')

    X, y = load_data(data_path)
    num_classes = len(np.unique(y))
    print(f"[DATASET] Loaded {len(X)} sequences across {num_classes} gesture classes.")

    # Safe stratification check (requires min 2 samples per class)
    counts = np.bincount(y)
    stratify = y if np.all(counts >= 2) else None

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    model = build_model(input_shape=X.shape[1:], num_classes=num_classes)
    model.summary()

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=[early_stop],
        verbose=1
    )

    # Save native Keras checkpoint
    model.save(output_keras)
    print(f"[EXPORT] Keras model saved to {output_keras}")

    # Evaluate
    y_pred_probs = model.predict(X_val, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = y_val

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=[f'Class {i}' for i in range(num_classes)]))

    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    # Export TFLite with representative dataset calibration
    convert_to_tflite_int8(model, X_train, output_tflite)


if __name__ == '__main__':
    main()