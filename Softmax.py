import math

def softmax(scores):
    max_score = max(scores)
    exp_scores = [math.exp(s - max_score) for s in scores]
    total = sum(exp_scores)
    return [e / total for e in exp_scores]

scores = [1, 2, 3]

result = softmax(scores)

print("Softmax output:")
for v in result:
    print(round(v, 4))