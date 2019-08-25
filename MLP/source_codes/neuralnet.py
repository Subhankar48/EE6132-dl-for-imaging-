import numpy as np
import sys
from activations import map_of_functions
from derivatives import map_of_derivatives
import downloader
import random
import matplotlib.pyplot as plt
import evaluations as ev

# for the network mentioned in the assignment

class layer(object):
    def __init__(self, no_of_neurons, activation_function='sigmoid'):
        self.size = no_of_neurons

        if activation_function in ["sigmoid", "ReLU", "softmax", "tanh"]:
            self.activation = map_of_functions[activation_function]
            self.derivative = map_of_derivatives[activation_function]

        else:
            print("The activation function mentioned does not exist.")
            sys.exit(0)


class network(object):

    layer_sizes = []
    weights = []
    biases = []
    training_data = []
    test_data = []
    feed_forward_activations = []
    z_values = []
    weight_gradients = []
    bias_gradients = []
    number_of_layers = 0
    minibatch_losses = []
    _accuracy = 0
    _precision = 0
    _recall = 0
    _f1_score = 0
    minibatch_size = 64

    def __init__(self, sizes):
        if (len(sizes) > 0):
            self.layer_sizes = sizes
        else:
            print("There is no hidden layer. Not a valid neural network.")
            sys.exit(0)

    def initialize_weights(self):
        weights = []
        biases = []
        for layer_number in range(len(self.layer_sizes)-1):
            fan_in = self.layer_sizes[layer_number]
            fan_out = self.layer_sizes[layer_number+1]
            self.weights.append(self.glorot_initialization(fan_in, fan_out))
            self.biases.append(np.asarray(
                np.zeros((fan_out, 1)), dtype=np.float64))
            weights.append(self.glorot_initialization(fan_in, fan_out))
            biases.append(np.asarray(np.zeros((fan_out, 1)), dtype=np.float64))
        self.number_of_layers = len(self.weights)+1
        return weights, biases

    def get_data(self):
        self.training_data, self.test_data = downloader.download()

    def glorot_initialization(self, fan_in, fan_out):
        dl = np.sqrt(6/(fan_in+fan_out))
        return np.asarray(np.random.uniform(-dl, dl, (fan_out, fan_in)), dtype=np.float64)

    def cross_entropy_loss(self, x, y):
        return -(y*np.log(x)).mean()

    def initialize_gradients(self):
        for weight in self.weights:
            self.weight_gradients.append(np.zeros_like(weight))
        for bias in self.biases:
            self.bias_gradients.append(np.zeros_like(bias))

    def feed_forward(self, x, weights, biases):
        self.feed_forward_activations = []
        zvals = []
        avals = []
        avals.append(x)
        temp = x
        for count in range(self.number_of_layers-1):
            z = np.asanyarray(np.dot(
                weights[count], temp))+biases[count]
            zvals.append(z)
            a = map_of_functions["softmax"](
                z) if count == self.number_of_layers-2 else map_of_functions["sigmoid"](z)
            avals.append(a)
            temp = a
        return zvals, avals

    def cross_entropy_derivative_with_softmax(self, y_pred, y_true):
        return y_pred-y_true

    def backprop(self, x, y, weights, biases):
        z_vals, a_vals = self.feed_forward(x, weights, biases)
        # self.initialize_gradients()
        weight_gradients = []
        bias_gradients = []
        for count in range(len(weights)):
            weight_gradients.append(np.zeros_like(weights[count]))
            bias_gradients.append(np.zeros_like(biases[count]))
        delta = self.cross_entropy_derivative_with_softmax(a_vals[-1], y)
        bias_gradients[-1] = np.mean(delta, axis=1, keepdims=True)
        weight_gradients[-1] = np.dot(delta, np.transpose(a_vals[-2]))
        for layer_number in range(2, self.number_of_layers):
            delta = np.dot(np.transpose(weights[-layer_number+1]), delta) * \
                map_of_derivatives["sigmoid"](
                    np.asanyarray(z_vals[-layer_number]))
            bias_gradients[-layer_number] = np.mean(
                delta, axis=1, keepdims=True)
            weight_gradients[-layer_number] = np.dot(
                delta, np.transpose(a_vals[-layer_number-1]))
        return weight_gradients, bias_gradients

    def train_network(self, data, weights, biases, learning_rate=0.001, number_of_epochs=7, minibatch_size=64):
        weights_to_use = weights
        biases_to_use = biases
        pixel_values = data[0]
        labels = data[1]
        temp_list = list(zip(pixel_values, labels))
        for epoch in range(number_of_epochs):
            print(epoch+1, " epoch is running")
            print("--------------------------------")
            random.shuffle(temp_list)
            pixel_values, labels = zip(*temp_list)

            input_batches = [pixel_values[k:k+minibatch_size]
                             for k in range(0, len(pixel_values), minibatch_size)]
            label_batches = [labels[k:k+minibatch_size]
                             for k in range(0, len(labels), minibatch_size)]
            for counter in range(len(input_batches)):
                _input = np.transpose(input_batches[counter])
                one_hot_encoded_vectors = np.transpose(label_batches[counter])
                temp_zvals, temp_avals = self.feed_forward(
                    _input, weights_to_use, biases_to_use)
                loss = self.cross_entropy_loss(
                    temp_avals[-1], one_hot_encoded_vectors)
                w_grad, b_grad = self.backprop(
                    _input, one_hot_encoded_vectors, weights_to_use, biases_to_use)
                for count in range(len(weights_to_use)):
                    prev_weight = np.copy(weights_to_use[count])
                    weights_to_use[count] -= learning_rate * \
                        w_grad[count]/self.minibatch_size
                    # print("************************************")
                    # print("Wgrads", np.max(np.max(np.abs(w_grad[count]))))
                    # print("Wself", np.max(np.max(np.abs(self.weights[count]))))
                    biases_to_use[count] -= learning_rate * \
                        b_grad[count]
                    # print("Bgrads", np.max(np.max(np.abs(b_grad[count]))))
                    # print("Bself", np.max(np.max(np.abs(self.biases[count]))))
                    # print("************************************")
                    print("------------------------------------------")
                    print("bias in loop ----------------",
                          biases_to_use[count][:5])
                    print("Gradient ---------------", learning_rate *
                          b_grad[count][:5])
                    print("------------------------------------------")
                # self.minibatch_losses.append(loss)
                # print(f"Loss is ------------ = {loss}")

    def predict(self, inputs):
        temp = inputs
        for count in range(len(self.weights)):
            z = np.dot(np.transpose(
                self.weights[count]), temp)+self.biases[count]
            a = map_of_functions["softmax"](
                z) if count == self.number_of_layers-2 else map_of_functions["sigmoid"](z)
            temp = a
        return (temp == np.max(temp, axis=0))*np.ones_like(temp)

    def plotter(self):
        plt.plot(self.minibatch_losses)
        plt.show()

    def model_performance(self):
        predictions = self.predict(self.test_data[0])
        y_vals = np.transpose(self.test_data[1])
        self._accuracy = ev.accuracy(predictions, y_vals)
        self._precision = ev.precision(predictions, y_vals)
        self._recall = ev.recall(predictions, y_vals)
        self._f1_score = ev.f1_score(predictions, y_vals)


a = network([784, 500, 250, 100, 10])
a.get_data()
a.initialize_gradients()
weights, biases = a.initialize_weights()
a.train_network(a.training_data, weights, biases)
# a.plotter()
