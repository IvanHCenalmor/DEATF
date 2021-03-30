
import numpy as np
from Network import initializations, activations


class Mutation:
    
    def __init__(self, ev_hypers, max_lay, batch_normalization, drop, individual):
        self.ev_hypers = ev_hypers
        self.max_lay = max_lay
        self.batch_normalization = batch_normalization
        self.drop = drop
        self.individual = individual
        
    def apply_random_mutation(self, network, custom_mutation_list):
        
        if not custom_mutation_list:
            custom_mutation_list = self.methods()
            
        type_mutation = np.random.choice(custom_mutation_list)
        
        self.apply_mutation(type_mutation, network)
        
    def apply_mutation(self, mutation, network):
        
        if mutation in self.methods():
            eval('self.' + mutation + '(network)')
        else:
            raise ValueError('The mutation {} is not defined'.format(mutation))
        
    def methods(self):
        
        method_list = [method for method in dir(self.__class__) if not method.startswith('__')]
        
        method_list.remove('methods')
        method_list.remove('apply_mutation')
        method_list.remove('apply_random_mutation')
        
        
        if len(self.ev_hypers) == 0:
            method_list.remove('mut_hyper')
        if self.batch_normalization:
            method_list.remove('mut_batch_norm')
        if self.drop:
            method_list.remove('mut_dropout')
        
        return method_list
       
    def mut_weight_init(self, network):             # We change weight initialization function in all layers
        layer_pos = np.random.randint(network.number_hidden_layers)
        init_w_function = initializations[np.random.randint(len(initializations))]
        network.change_weight_init(layer_pos, init_w_function)


    def mut_activation(self, network):             # We change the activation function in layer
        layer_pos = np.random.randint(network.number_hidden_layers)
        init_a_function = activations[np.random.randint(len(activations))]
        network.change_activation(layer_pos, init_a_function)
        
    def mut_dropout(self, network):
        network.change_dropout()

    def mut_batch_norm(self, network):
        network.change_batch_norm() 
        
    def mut_hyper(self, network):                # We change the value of a hyperparameter for another value
        h = np.random.choice(list(self.ev_hypers.keys()))  # We select the hyperparameter to be mutated
        # We choose two values, just in case the first one is the one already selected
        new_value = np.random.choice(self.ev_hypers[h], size=2, replace=False)
        if self.individual.descriptor_list["hypers"][h] == new_value[0]:
            self.individual.descriptor_list["hypers"][h] = new_value[1]
        else:
            self.individual.descriptor_list["hypers"][h] = new_value[0]
           
            
class MLP_Mutation(Mutation):
    
    def __init__(self, ev_hypers, max_lay, batch_normalization, drop, individual):
        super().__init__(ev_hypers, max_lay, batch_normalization, drop, individual)
        
    def mut_add_layer(self, network):           # We add one layer
        layer_pos = np.random.randint(network.number_hidden_layers)+1
        lay_dims = np.random.randint(self.max_lay)+1
        init_w_function = initializations[np.random.randint(len(initializations))]
        init_a_function = activations[np.random.randint(len(activations))]
        if not self.drop:
            dropout = np.random.randint(0, 2)
            drop_prob = np.random.rand()
        else:
            dropout = 0
            drop_prob = 0
        if not self.batch_normalization:
            batch_norm = np.random.randint(0, 2)
        else:
            batch_norm = 0
    
        network.add_layer(layer_pos, lay_dims, init_w_function, init_a_function, dropout, drop_prob, batch_norm)
        
    
    def mut_del_layer(self, network): # We remove one layer
        network.remove_random_layer()

    def mut_dimension(self, network):              # We change the number of neurons in layer
        network.change_layer_dimension(self.max_lay)
     
        
class CNN_Mutation(Mutation):

    def __init__(self, ev_hypers, max_lay, batch_normalization, drop, individual):
        super().__init__(ev_hypers, max_lay, batch_normalization, drop, individual)

    def mut_add_conv_layer(self, network):
        if network.shapes[-1][0] > 2 and network.shapes[-1][1] > 2:
            network.add_layer(np.random.randint(0, network.number_hidden_layers), np.random.randint(0, 3), [1, np.random.randint(2, 4), np.random.choice(activations[1:]), np.random.choice(initializations[1:])])
    
    def mut_del_conv_layer(self, network):
        if network.number_hidden_layers > 1:
            network.remove_random_layer()
    
    def mut_stride_conv(self, network):
        layer = np.random.randint(0, network.number_hidden_layers)
        if network.strides[layer][0] == 1 and network.shapes[-1][0] >= 4:
            network.change_stride(layer, 2)
        elif network.strides[layer][0] == 2:
            network.change_stride(layer, 1)
    
    def mut_filter_conv(self, network):
        layer = np.random.randint(0, network.number_hidden_layers)
        channels = np.random.randint(0, 65)
        if network.filters[layer][0] == 2 and network.shapes[-1][0] >= 3:
            network.change_filters(layer, 3, channels)
        elif network.filters[layer][0] == 3:
            network.change_filters(layer, 2, channels)
            

class TCNN_Mutation(Mutation):

    def __init__(self, ev_hypers, max_lay, batch_normalization, drop, individual):
        super().__init__(ev_hypers, max_lay, batch_normalization, drop, individual)
         
    def mut_add_deconv_layer(self, network):
        network.add_layer(np.random.randint(0, network.number_hidden_layers), [1, np.random.randint(2, 4), np.random.choice(activations[1:]), np.random.choice(initializations[1:])])
    
    def mut_del_deconv_layer(self, network):
        network.remove_random_layer()
    
    def mut_stride_deconv(self, network):
        layer = np.random.randint(0, network.number_hidden_layers)
        if network.strides[layer][1] == 2 and network.output_shapes[-1][1] / 2 >= network.output_dim[1]:
            network.change_stride(layer, 1)
        elif network.strides[layer][1] == 1:
            network.change_stride(layer, 2)
    
    def mut_filter_deconv(self, network):
        layer = np.random.randint(0, network.number_hidden_layers)
    
        if network.filters[layer][1] == 3 and network.output_shapes[-1][1] - 6 >= network.output_dim[1]:
            network.change_filters(layer, 2, np.random.randint(0, 65))
        elif network.filters[layer][1] == 2:
            network.change_filters(layer, 3, np.random.randint(0, 65))
    


