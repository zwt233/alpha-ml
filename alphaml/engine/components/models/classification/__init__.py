import os
from alphaml.engine.components.models.base_model import BaseClassificationModel
from alphaml.utils.class_loader import find_components

"""
Load the buildin classifiers.
"""
classifiers_directory = os.path.split(__file__)[0]
_classifiers = find_components(__package__, classifiers_directory, BaseClassificationModel)
