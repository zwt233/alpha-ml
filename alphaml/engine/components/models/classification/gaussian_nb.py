import numpy as np
from hyperopt import hp
from ConfigSpace.configuration_space import ConfigurationSpace

from alphaml.engine.components.models.base_model import BaseClassificationModel, IterativeComponent
from alphaml.utils.constants import *


class GaussianNB(IterativeComponent, BaseClassificationModel):

    def __init__(self, random_state=None, verbose=0):

        self.random_state = random_state
        self.verbose = int(verbose)
        self.estimator = None
        self.time_limit = None

    def iterative_fit(self, X, y, n_iter=1, refit=False):
        import sklearn.naive_bayes

        if refit:
            self.estimator = None

        if self.estimator is None:
            self.n_iter = 0
            self.fully_fit_ = False
            self.estimator = sklearn.naive_bayes.GaussianNB()
            self.classes_ = np.unique(y.astype(int))

        # Fallback for multilabel classification
        if len(y.shape) > 1 and y.shape[1] > 1:
            import sklearn.multiclass
            self.estimator.n_iter = self.n_iter
            self.estimator = sklearn.multiclass.OneVsRestClassifier(
                self.estimator, n_jobs=1)
            self.estimator.fit(X, y)
            self.fully_fit_ = True
        else:
            for iter in range(n_iter):
                start = min(self.n_iter * 1000, y.shape[0])
                stop = min((self.n_iter + 1) * 1000, y.shape[0])
                if X[start:stop].shape[0] == 0:
                    self.fully_fit_ = True
                    break

                self.estimator.partial_fit(X[start:stop], y[start:stop],
                                           self.classes_)
                self.n_iter += 1

                if stop >= len(y):
                    self.fully_fit_ = True
                    break

        return self

    def configuration_fully_fitted(self):
        if self.estimator is None:
            return False
        elif not hasattr(self, 'fully_fit_'):
            return False
        else:
            return self.fully_fit_

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict_proba(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'GaussianNB',
                'name': 'Gaussian Naive Bayes classifier',
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'input': (DENSE, UNSIGNED_DATA),
                'output': (PREDICTIONS,)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None, optimizer='smac'):
        if optimizer == 'smac':
            cs = ConfigurationSpace()
            return cs
        elif optimizer == 'tpe':
            return {}
