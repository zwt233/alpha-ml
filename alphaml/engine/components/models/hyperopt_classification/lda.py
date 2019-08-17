from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter, \
    UniformIntegerHyperparameter, CategoricalHyperparameter
from ConfigSpace.conditions import EqualsCondition

from alphaml.engine.components.models.base_model import BaseClassificationModel
from alphaml.utils.common import check_none
from alphaml.utils.constants import *
from alphaml.utils.model_util import softmax


class LDA(BaseClassificationModel):
    def __init__(self, shrinkage, n_components, tol, shrinkage_factor=0.5, random_state=None):
        self.shrinkage = shrinkage
        self.n_components = n_components
        self.tol = tol
        self.shrinkage_factor = shrinkage_factor
        self.estimator = None

    def fit(self, X, Y):
        import sklearn.multiclass
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

        if check_none(self.shrinkage):
            self.shrinkage_ = None
            solver = 'svd'
        elif self.shrinkage == "auto":
            self.shrinkage_ = 'auto'
            solver = 'lsqr'
        elif self.shrinkage == "manual":
            self.shrinkage_ = float(self.shrinkage_factor)
            solver = 'lsqr'
        else:
            raise ValueError(self.shrinkage)

        self.n_components = int(self.n_components)
        self.tol = float(self.tol)

        estimator = LinearDiscriminantAnalysis(
            n_components=self.n_components, shrinkage=self.shrinkage_,
            tol=self.tol, solver=solver)

        if len(Y.shape) == 2 and Y.shape[1] > 1:
            self.estimator = sklearn.multiclass.OneVsRestClassifier(estimator, n_jobs=1)
        else:
            self.estimator = estimator

        self.estimator.fit(X, Y)
        return self

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()

        df = self.estimator.predict_proba(X)
        return softmax(df)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'LDA',
                'name': 'Linear Discriminant Analysis',
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'input': (DENSE, UNSIGNED_DATA),
                'output': (PREDICTIONS,)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        cs = ConfigurationSpace()
        shrinkage = CategoricalHyperparameter(
            "shrinkage", ["None", "auto", "manual"], default_value="None")
        shrinkage_factor = UniformFloatHyperparameter(
            "shrinkage_factor", 0., 1., 0.5)
        n_components = UniformIntegerHyperparameter('n_components', 1, 250, default_value=10)
        tol = UniformFloatHyperparameter("tol", 1e-5, 1e-1, default_value=1e-4, log=True)
        cs.add_hyperparameters([shrinkage, shrinkage_factor, n_components, tol])

        cs.add_condition(EqualsCondition(shrinkage_factor, shrinkage, "manual"))
        return cs