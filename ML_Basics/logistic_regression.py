from sklearn.datasets import make_classification
from config import Config
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt


class CustomLogisticRegression:

    def __init__(self, num_iters, lr, threshold=0.5):
        self.lr = lr
        self.num_iters = num_iters
        self.threshold = threshold

    def _sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def _train_model_parameters(self):
        A = self._sigmoid(self.X_train.dot(self.W) + self.b)
        error = np.reshape(A - self.y_train.T, self.m)
        dW = np.dot(self.X_train.T, error) / self.m
        db = np.sum(error) / self.m
        self.W -= self.lr * dW
        self.b -= self.lr * db

    def train(self, X_train, y_train, display_wts=True):
        self.X_train, self.y_train = X_train, y_train
        self.m, self.n = X_train.shape
        self.W = np.ones(self.n)
        self.b = 0
        for _ in tqdm(range(self.num_iters)):
            self._train_model_parameters()
        if display_wts:
            print('Trained weights:', self.W)
            print('Trained bias:', self.b)

    def predict(self, X):
        return np.where(self._sigmoid(X.dot(self.W) + self.b) > self.threshold, 1, 0)


def prepare_data(n_samples=200, split_ratio=0.8, plot=True):
    X, y = make_classification(
        n_samples=n_samples,
        n_features=5,
        n_repeated=0,
        n_redundant=0,
        n_informative=2,
        random_state=0,
        class_sep=10,
    )
    if plot:
        plt.figure(figsize=(7.5, 3.5))
        plt.scatter(X[:, 0], X[:, 1], marker='x', c=y, s=20, cmap='bwr')
        plt.title('Binary classification dataset')
        plt.show()
    split = round(len(X) * split_ratio)
    return X[:split], y[:split], X[split:], y[split:]


def run():
    conf = Config()
    X_train, y_train, X_test, y_test = prepare_data(n_samples=200)
    model = CustomLogisticRegression(conf.NUM_ITERATIONS, conf.LR, conf.THRESHOLD)
    model.train(X_train, y_train)
    accuracy = np.mean(model.predict(X_test) == y_test) * 100
    print(f'Test accuracy: {accuracy:.2f}%')


if __name__ == '__main__':
    run()
