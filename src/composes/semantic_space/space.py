'''
Created on Sep 21, 2012

@author: georgianadinu
'''

from composes.utils.space_utils import list2dict
from composes.utils.space_utils import assert_dict_match_list
from composes.utils.space_utils import assert_shape_consistent
from composes.utils.space_utils import assert_is_instance 
from composes.matrix.matrix import Matrix
from composes.weighting.weighting import Weighting
from composes.dim_reduction.dimensionality_reduction import DimensionalityReduction
from composes.feature_selection.feature_selection import FeatureSelection
from composes.semantic_space.operation import Operation
from composes.similarity.similarity import Similarity
from composes.utils.space_utils import add_items_to_dict
from warnings import warn

class Space(object):
    """
    This class implements semantic spaces.
    
    A semantic space described a list of targets (words, phrases, etc.)
    in terms of co-occurrence with contextual features. 
    
    A semantic space contains a matrix storing (some type of) co-occurrence
    strength values between targets and contextual features: by convention,
    targets are rows and features are columns.
    
    In addition to this co-occurrence matrix, the space stores structures
    that encode the mappings between the matrix row/column indices and the
    associated target/context-feature strings.
    
    A number of transformations can be applied to a semantic space, with the
    goal of improving the quality of the target representations. 
    Some transformations, such as weighings, only rescale the values
    in the space matrix, while others, such as dimensionality
    reduction, or feature selection, can alter the set of 
    contextual features.
    
    """

    def __init__(self, matrix_, id2row, id2column, row2id=None, column2id=None,
                 **kwargs):
        '''
        Constructor
        '''
        if row2id is None:
            row2id = list2dict(id2row)
        else:    
            assert_dict_match_list(row2id, id2row)
            
        if column2id is None:
            column2id = list2dict(id2column)
        else:
            assert_dict_match_list(column2id, id2column)
            
        assert_shape_consistent(matrix_, id2row, id2column, row2id, column2id)
        
        self._cooccurrence_matrix = matrix_
        self._row2id = row2id
        self._id2row = id2row
        self._column2id = column2id
        self._id2column = id2column
        if "operations" in kwargs:
            self._operations = kwargs["operations"]
        else:
            self._operations = []

      
    def apply(self, transformation):
        
        #TODO , FeatureSelection, DimReduction ..
                                            
        assert_is_instance(transformation, (Weighting, DimensionalityReduction, 
                                            FeatureSelection))
        op = transformation.create_operation()
        new_matrix =  op.apply(self.cooccurrence_matrix)
        
        new_operations = list(self.operations)
        new_operations.append(op)

        id2row, row2id = list(self.id2row), self.row2id.copy() 
        
        if isinstance(transformation, DimensionalityReduction):
            id2column, column2id = [], {}
        elif isinstance(transformation, FeatureSelection):
            id2column = self.id2column[transformation.selected_columns]
            column2id = list2dict(id2column)
        else:
            id2column, column2id = list(self.id2column), self.column2id.copy()
        
        return Space(new_matrix, id2row, id2column,
                     row2id, column2id, operations = new_operations)
        
    def get_sim(self, word1, word2, similarity, space2=None):
        
        assert_is_instance(similarity, Similarity)
        v1 = self.get_row(word1)
        if space2 is None:
            v2 = self.get_row(word2)
        else:
            v2 = space2.get_row(word2)
        
        if v1 is None:
            warn("Row string %s not found, returning 0.0" % (word1))
            return 0.0

        if v2 is None:
            warn("Row string %s not found, returning 0.0" % (word2))
            return 0.0
        
        return similarity.get_sim(v1, v2)
      
    def get_neighbours(self, word, no_neighbours, similarity, 
                       neighbour_space=None):            
       
        assert_is_instance(similarity, Similarity)       
        vector = self.get_row(word)
        if vector is None:
            return []
        
        if neighbour_space is None:
            id2row = self.id2row
            sims_to_matrix = similarity.get_sims_to_matrix(vector, 
                                                          self.cooccurrence_matrix)
        else:
            sims_to_matrix = similarity.get_sims_to_matrix(vector, 
                                         neighbour_space.cooccurrence_matrix)
            id2row = neighbour_space.id2row 
        
        sorted_perm = sims_to_matrix.sorted_permutation(sims_to_matrix.sum, 1)
        no_neighbours = min(no_neighbours, len(id2row))
        result = []
                
        for count in range(no_neighbours):
            i = sorted_perm[count]
            result.append((id2row[i], sims_to_matrix[i,0]))

        return result    

    def vstack(self, space_):
        if self.cooccurrence_matrix.shape[1] != space_.cooccurrence_matrix.shape[1]:
            raise ValueError("Inconsistent shapes: %s, %s" 
                             % (self.cooccurrence_matrix.shape[1], 
                                space_.cooccurrence_matrix.shape[1]))
        
        if self.id2column != space_.id2column:
            raise ValueError("Identical columns required")
        
        new_row2id = add_items_to_dict(self.row2id.copy(), space_.id2row)
        new_id2row = self.id2row + space_.id2row
        new_mat = self.cooccurrence_matrix.vstack(space_.cooccurrence_matrix)
        
        return Space(new_mat, new_id2row, list(self.id2column), new_row2id, 
                     self.column2id.copy(), operations=[])
        
            
    def get_row(self, word):
        if not word in self.row2id:
            return None
        return self.cooccurrence_matrix[self.row2id[word],:]
    
    def get_rows(self, words):
        row_ids = []
        for word in words:
            if not word in self.row2id:
                raise ValueError("Word not found in space rows: %s" % word)
            else:
                row_ids.append(self.row2id[word])
        
        return self.cooccurrence_matrix[row_ids,:]
        
    def set_cooccurrence_matrix(self, matrix_):
        assert_is_instance(matrix_, Matrix)
        self.assert_shape_consistent(matrix_, self.row2id, self.id2row,
                                       self.column2id, self.id2column)
        self._cooccurrence_matrix = matrix_
        
    def get_cooccurrence_matrix(self):
        return self._cooccurrence_matrix
        
    cooccurrence_matrix = property(get_cooccurrence_matrix)
        
    def get_row2id(self):
        return self._row2id
            
    row2id = property(get_row2id)

    def get_id2row(self):
        return self._id2row
            
    id2row = property(get_id2row)

    def get_column2id(self):
        return self._column2id
            
    column2id = property(get_column2id)

    def get_id2column(self):
        return self._id2column
            
    id2column = property(get_id2column)
    
    def get_operations(self):
        return self._operations
            
    operations = property(get_operations)
    