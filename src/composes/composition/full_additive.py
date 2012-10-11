'''
Created on Oct 5, 2012

@author: georgianadinu
'''

from composition_model import CompositionModel
from composes.utils.space_utils import assert_is_instance
from composes.utils.matrix_utils2 import is_array_or_matrix
from composes.utils.matrix_utils2 import padd_matrix
from composes.utils.matrix_utils2 import to_compatible_matrix_types
from composes.utils.regression_learner import RidgeRegressionLearner
from composes.utils.regression_learner import RegressionLearner

class FullAdditive(CompositionModel):
    '''
    classdocs
    '''
    _name = "full_additive"
    
    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        if "A" in kwargs and "B" in kwargs:
            mat_a = kwargs["A"]
            mat_b = kwargs["B"]
            if not is_array_or_matrix(mat_a):
                raise TypeError("expected matrix type, received: %s" 
                                % type(mat_a))

            if not is_array_or_matrix(mat_b):
                raise TypeError("expected matrix type, received: %s" 
                                % type(mat_b))
                        
            mat_a, mat_b = to_compatible_matrix_types(mat_a, mat_b)                    
            self._mat_a_t = mat_a.transpose()
            self._mat_b_t = mat_b.transpose()
            self._has_intercept = False
            
        else:
            self._regression_learner = RidgeRegressionLearner()
            if "learner" in kwargs:
                self._regression_learner = kwargs["learner"] 
            self._has_intercept = self._regression_learner.has_intercept()
        
        
    def _train(self, arg1_mat, arg2_mat, phrase_mat):

        self._has_intercept = self._regression_learner.has_intercept()
        
        result = self._regression_learner.train(arg1_mat.hstack(arg2_mat), phrase_mat)

        self._mat_a_t = result[0:arg1_mat.shape[1], :]
        self._mat_b_t = result[arg1_mat.shape[1]:, :]

    
    def _compose(self, arg1_mat, arg2_mat):
        if self._has_intercept:
            return arg1_mat * self._mat_a_t + padd_matrix(arg2_mat, 1) * self._mat_b_t
        else:
            return arg1_mat * self._mat_a_t + arg2_mat * self._mat_b_t
        
    def set_regression_learner(self, regression_learner):
        assert_is_instance(regression_learner, RegressionLearner)
        self._regression_learner = regression_learner
        
    def get_regression_learner(self):
        return self._regression_learner
    regression_learner = property(get_regression_learner, set_regression_learner)    

    def _build_id2column(self, arg1_space, arg2_space):
        return []

           
    
