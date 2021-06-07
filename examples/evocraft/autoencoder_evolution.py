import sys
sys.path.append('../..')

import numpy as np
import tensorflow as tf

from deatf.evolution import Evolving
from deatf.network import MLP, MLPDescriptor
from deatf.metrics import accuracy_error

from tensorflow.keras.layers import Input, Reshape, Softmax
from tensorflow.keras.models import Model
import tensorflow.keras.optimizers as opt

from visualize_networks import evaluate_with_visualization
from create_model_based_data import creating_data_and_population

from deap import tools

optimizers = [opt.Adadelta, opt.Adagrad, opt.Adam]


def eval_model(nets, train_inputs, train_outputs, batch_size, iters, test_inputs, __, hypers):  

    
    # In the autoencoder would be the flattened representation of the solutions 
    inp = Input(shape=train_inputs['i0'].shape[1:])
    out = nets['n0'].building(inp)
    out = Softmax()(out)
    out = Reshape((np.prod(bounds), n_wanted_blocks))(out)
    model = Model(inputs=inp, outputs=out)
    
    #model.summary()

    opt = optimizers[hypers["optimizer"]](learning_rate=hypers["lrate"])
    model.compile(loss=tf.nn.softmax_cross_entropy_with_logits, optimizer=opt, metrics=[])
    
    model.fit(train_inputs['i0'], train_outputs['o0'], epochs=iters, batch_size=batch_size, verbose=0)
    
    res = model.predict(train_inputs['i0'])

    ev = accuracy_error(train_outputs["o0"], res)

    return ev,

def evolve_with_population(evolving_alg, population):

    hall_of = tools.HallOfFame(evolving_alg.population_size)
    stats = tools.Statistics(lambda ind: ind.fitness.values)

    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    result, log_book = evolving_alg.ev_alg(population, evolving_alg.toolbox, 
                                           ngen=evolving_alg.generations, 
                                           **evolving_alg.evol_kwargs, verbose=1, 
                                           stats=stats, halloffame=hall_of)

    return result, log_book, hall_of

if __name__ == "__main__":
    
    num_models = 50
    max_layers = 10
    max_neurons = 12
    layer_size = 4
    center_layer = int(layer_size/2)-1

    bounds = [layer_size,max_layers,layer_size]
    
    #wanted_blocks = [23,45,64,22,33]      
    wanted_blocks = [-1,23,45,64,22,200,105,75,61]
    n_wanted_blocks = len(wanted_blocks)
    
    aux_data = np.zeros(bounds)

    # This evolving object is auxiliar, only for createing the data and population
    e = Evolving(desc_list=[MLPDescriptor], x_trains=[aux_data], y_trains=[aux_data], 
                 x_tests=[aux_data], y_tests=[aux_data], evaluation=eval_model, 
                 batch_size=150, population=num_models, generations=10, iters=10, 
                 max_num_layers=max_layers, max_num_neurons=max_neurons,
                 n_inputs=[np.prod(bounds)], n_outputs=[n_wanted_blocks*np.prod(bounds)], 
                 cxp=0., mtp=1., hyperparameters={"lrate": [0.1, 0.5, 1], "optimizer": [0, 1, 2]}, 
                 batch_norm=True, dropout=True)
    
    data, noisy_data, net_population = creating_data_and_population(e, wanted_blocks, bounds, center_layer, layer_size)

    x_train = noisy_data

    y_train = np.copy(data)
    for i, block in enumerate(wanted_blocks):   
        y_train = np.where(y_train == block, i, y_train)
    
    num_samples = list(y_train.shape) + [-1]
    y_train = y_train.flatten()
    
    y_train = np.reshape(y_train, (-1, 1))
    y_train = tf.keras.utils.to_categorical(y_train, num_classes=n_wanted_blocks)
    y_train = np.reshape(y_train, num_samples)

    e = Evolving(desc_list=[MLPDescriptor], x_trains=[x_train], y_trains=[y_train], 
                 x_tests=[x_train], y_tests=[y_train], evaluation=eval_model, 
                 batch_size=150, population=num_models, generations=2, iters=100, 
                 max_num_layers=max_layers, max_num_neurons=max_neurons,
                 n_inputs=[np.prod(bounds)], n_outputs=[n_wanted_blocks*np.prod(bounds)], 
                 cxp=0., mtp=1., hyperparameters={"lrate": [0.1, 0.5, 1], "optimizer": [0, 1, 2]}, 
                 batch_norm=True, dropout=True)

    a = evolve_with_population(e, net_population)
    print(a[-1])

    mlp_descriptor = a[2].items[-1].descriptor_list['n0']
    network = MLP(mlp_descriptor)
        
    learning_rate = a[2].items[-1].descriptor_list['hypers']['lrate']
    optimizer = optimizers[a[2].items[-1].descriptor_list['hypers']['optimizer']]
    
    inp = Input(shape=x_train.shape[1:])
    out = network.building(inp)
    out = Softmax()(out)
    out = Reshape((np.prod(bounds), n_wanted_blocks))(out)
    model = Model(inputs=inp, outputs=out)
    
    #model.summary()

    opt = optimizer(learning_rate=learning_rate)
    model.compile(loss=tf.nn.softmax_cross_entropy_with_logits, optimizer=opt, metrics=[])
    
    model.fit(x_train, y_train, epochs=100, batch_size=150, verbose=1)
    
    res = model.predict(x_train)

    evaluate_with_visualization(res, bounds, wanted_blocks, evaluate=False)

 

    