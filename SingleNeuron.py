import math

def single_neuron_model(features: list[list[float]], labels: list[int], weights: list[float], bias: float) -> (list[float], float):
    probabilities = []
    for x in features:
        z = sum(w * xi for w, xi in zip(weights, x)) + bias
        p = 1 / (1 + math.exp(-z))
        probabilities.append(p)
    mse = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    probabilities = [round(p, 4) for p in probabilities]
    mse = round(mse, 4)
    return probabilities, mse


features = [[0.5, 1.0], [-1.5, -2.0], [2.0, 1.5]]
labels = [0, 1, 0]
weights = [0.7, -0.4]
bias = -0.1

output = single_neuron_model(features, labels, weights, bias)
print(output)

