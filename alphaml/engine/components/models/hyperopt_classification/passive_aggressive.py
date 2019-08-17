import numpy as np

from hyperopt import hp

from alphaml.utils.constants import *
from alphaml.utils.model_util import softmax
from alphaml.utils.common import check_none, check_for_bool
from alphaml.engine.components.models.base_model import BaseClassificationModel, IterativeComponentWithSampleWeight


class PassiveAggressive(
    IterativeComponentWithSampleWeight,
    BaseClassificationModel,
):
    def __init__(self, C, fit_intercept, tol, loss, average, random_state=None):
        self.C = C
        self.fit_intercept = fit_intercept
        self.average = average
        self.tol = tol
        self.loss = loss
        self.random_state = random_state
        self.estimator = None

    def iterative_fit(self, X, y, n_iter=2, refit=False, sample_weight=None):
        from sklearn.linear_model.passive_aggressive import \
            PassiveAggressiveClassifier

        # Need to fit at least two iterations, otherwise early stopping will not
        # work because we cannot determine whether the algorithm actually
        # converged. The only way of finding this out is if the sgd spends less
        # iterations than max_iter. If max_iter == 1, it has to spend at least
        # one iteration and will always spend at least one iteration, so we
        # cannot know about convergence.

        if refit:
            self.estimator = None

        if self.estimator is None:
            self.fully_fit_ = False

            self.average = check_for_bool(self.average)
            self.fit_intercept = check_for_bool(self.fit_intercept)
            self.tol = float(self.tol)
            self.C = float(self.C)

            call_fit = True
            self.estimator = PassiveAggressiveClassifier(
                C=self.C,
                fit_intercept=self.fit_intercept,
                max_iter=n_iter,
                tol=self.tol,
                loss=self.loss,
                shuffle=True,
                random_state=self.random_state,
                warm_start=True,
                average=self.average,
            )
            self.classes_ = np.unique(y.astype(int))
        else:
            call_fit = False

        # Fallback for multilabel classification
        if len(y.shape) > 1 and y.shape[1] > 1:
            import sklearn.multiclass
            self.estimator.max_iter = 50
            self.estimator = sklearn.multiclass.OneVsRestClassifier(
                self.estimator, n_jobs=1)
            self.estimator.fit(X, y)
            self.fully_fit_ = True
        else:
            if call_fit:
                self.estimator.fit(X, y)
            else:
                self.estimator.max_iter += n_iter
                self.estimator.max_iter = min(self.estimator.max_iter,
                                              1000)
                self.estimator._validate_params()
                lr = "pa1" if self.estimator.loss == "hinge" else "pa2"
                self.estimator._partial_fit(
                    X, y,
                    alpha=1.0,
                    C=self.estimator.C,
                    loss="hinge",
                    learning_rate=lr,
                    max_iter=n_iter,
                    classes=None,
                    sample_weight=sample_weight,
                    coef_init=None,
                    intercept_init=None
                )
                if (
                        self.estimator.max_iter >= 1000
                        or n_iter > self.estimator.n_iter_
                ):
                    self.fully_fit_ = True

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
            raise NotImplementedError()
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()

        df = self.estimator.decision_function(X)
        return softmax(df)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'PassiveAggressive Classifier',
                'name': 'Passive Aggressive Classifier',
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'input': (DENSE, SPARSE, UNSIGNED_DATA),
                'output': (PREDICTIONS,)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        space = {'C': hp.loguniform("pa_C", np.log(1e-5), np.log(10)),
                 'fit_intercept': hp.choice('pa_fit_intercept', ["True"]),
                 'loss': hp.choice('pr_loss', ["hinge", "squared_hinge"]),
                 'tol': hp.loguniform('pr_tol', np.log(1e-5), np.log(1e-1)),
                 'average': hp.choice('pr_average', ["False", "True"])}

        init_trial = {'C': 1, 'fit_intercept': "True", 'loss': "hinge",
                      'tol': 1e-4, 'average': "False"}

        return space
