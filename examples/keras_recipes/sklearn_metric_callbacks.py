"""
Title: Evaluating and exporting scikit-learn metrics in a Keras callback
Author: [lukewood](https://lukewood.xyz)
Date created: 10/07/2021
Last modified: 11/17/2023
Description: This example shows how to use Keras callbacks to evaluate and export non-TensorFlow based metrics.
Accelerator: GPU
"""
"""
## Introduction

[Keras callbacks](https://keras.io/api/callbacks/) allow for the execution of arbitrary
code at various stages of the Keras training process.  While Keras offers first-class
support for metric evaluation, [Keras metrics](https://keras.io/api/metrics/) may only
rely on TensorFlow code internally.

While there are TensorFlow implementations of many metrics online, some metrics are
implemented using [NumPy](https://numpy.org/) or another Python-based numerical computation library.
By performing metric evaluation inside of a Keras callback, we can leverage any existing
metric, and ultimately export the result to TensorBoard.
"""

"""
## Jaccard score metric

This example makes use of a sklearn metric, `sklearn.metrics.jaccard_score()`, and
writes the result to TensorBoard using the `tf.summary` API.

This template can be modified slightly to make it work with any existing sklearn metric.
"""

import os

os.environ["KERAS_BACKEND"] = "tensorflow"

import keras
from keras import ops
from keras import layers
import tensorflow as tf
from sklearn.metrics import jaccard_score
import numpy as np
import os


class JaccardScoreCallback(keras.callbacks.Callback):
    """Computes the Jaccard score and logs the results to TensorBoard."""

    def __init__(self, name, x_test, y_test, log_dir):
        self.x_test = x_test
        self.y_test = y_test
        self.keras_metric = keras.metrics.Mean("jaccard_score")
        self.epoch = 0
        self.summary_writer = tf.summary.create_file_writer(os.path.join(log_dir, name))

    def on_epoch_end(self, batch, logs=None):
        self.epoch += 1
        self.keras_metric.reset_state()
        predictions = self.model.predict(self.x_test)
        jaccard_value = jaccard_score(
            ops.argmax(predictions, axis=-1), self.y_test, average=None
        )
        self.keras_metric.update_state(jaccard_value)
        self._write_metric(
            self.keras_metric.name, self.keras_metric.result().numpy().astype(float)
        )

    def _write_metric(self, name, value):
        with self.summary_writer.as_default():
            tf.summary.scalar(
                name,
                value,
                step=self.epoch,
            )
            self.summary_writer.flush()


"""
## Sample usage

Let's test our `JaccardScoreCallback` class with a Keras model.
"""
# Model / data parameters
num_classes = 10
input_shape = (28, 28, 1)

# The data, split between train and test sets
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

# Scale images to the [0, 1] range
x_train = x_train.astype("float32") / 255
x_test = x_test.astype("float32") / 255
# Make sure images have shape (28, 28, 1)
x_train = ops.expand_dims(x_train, -1)
x_test = ops.expand_dims(x_test, -1)
print("x_train shape:", x_train.shape)
print(x_train.shape[0], "train samples")
print(x_test.shape[0], "test samples")


# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = keras.Sequential(
    [
        keras.Input(shape=input_shape),
        layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ]
)

model.summary()

batch_size = 128
epochs = 15

model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
callbacks = [
    JaccardScoreCallback(model.name, x_test, ops.argmax(y_test, axis=-1), "logs")
]
model.fit(
    x_train,
    y_train,
    batch_size=batch_size,
    epochs=epochs,
    validation_split=0.1,
    callbacks=callbacks,
)

"""
If you now launch a TensorBoard instance using `tensorboard --logdir=logs`, you will
see the `jaccard_score` metric alongside any other exported metrics!

![TensorBoard Jaccard Score](https://i.imgur.com/T4qzrdn.png)
"""

"""
## Conclusion

Many ML practitioners and researchers rely on metrics that may not yet have a TensorFlow
implementation. Keras users can still leverage the wide variety of existing metric
implementations in other frameworks by using a Keras callback.  These metrics can be
exported, viewed and analyzed in the TensorBoard like any other metric.
"""
