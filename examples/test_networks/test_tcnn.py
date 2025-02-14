import sys
sys.path.append('../..')

import tensorflow as tf
import numpy as np
import time

from deatf.network import TCNNDescriptor
from deatf.evolution import Evolving

from aux_functions_testing import select_evaluation, load_dataset

import tensorflow.keras.optimizers as opt
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
from sklearn.metrics import mean_squared_error

import matplotlib.pyplot as plt

optimizers = [opt.Adadelta, opt.Adagrad, opt.Adam]

def test_TCNN_all_datasets(eval_func=None, batch_size=150, population=5, 
                      generations=10, iters=100, max_num_layers=10, max_num_neurons=20,
                      evol_alg='mu_plus_lambda', sel='best', lrate=0.01, cxp=0, mtp=1,
                      seed=None, sel_kwargs={}, max_filter=4, max_stride=3):
    """
    Tests the TCNN network with all the possible datasets and with the specified parameter selection.

    :param eval_func: Evaluation function for evaluating each network.
    :param batch_size: Batch size of the data during the training of the networks.
    :param population: Number of individuals in the populations in the genetic algorithm.
    :param generations: Number of generations that will be done in the genetic algorithm.
    :param iters: Number of iterations that each network will be trained.
    :param max_num_layers: Maximum number of layers allowed in the networks.
    :param max_num_neurons: Maximum number of neurons allowed in the networks.
    :param max_filter: Maximum size of the filter allowed in the networks.
    :param max_stride: Maximum size of the stride allowed in the networks.
    :param evol_alg: Evolving algorithm that will be used during the genetic algorithm.
    :param sel: Selection method that will be used during the genetic algorithm.
    :param sel_kwargs: Arguments for selection method.
    :param lrate: Learning rate that will be used during training.
    :param cxp: Crossover probability that will be used during the genetic algorithm.
    :param mtp: Mutation probability that will be used during the genetic algorithm.
    :param seed: Seed that will be used in every random method.
    """

    dataset_collection = ['mnist', 'kmnist', 'cmaterdb', 'fashion_mnist', 'cifar10', 'rock_paper_scissors']
   
    for dataset in dataset_collection:
        
        print('\nEvaluating the {} dataset with the following configuration:'.format(dataset),
              '\nBatch size:  {}\nPopulation of networks:  {}\nGenerations:  {}'.format(batch_size, population, generations),
              '\nIterations in each network:  {}\nMaximum number of layers:  {}'.format(iters, max_num_layers),
              '\nMaximum number of neurons in each layer: {}'.format(max_num_neurons))

        init_time = time.time()
        
        try:
            x = test_TCNN(dataset, eval_func=eval_func, batch_size=batch_size, 
                 population=population, generations=generations, iters=iters, 
                 max_num_layers=max_num_layers, max_num_neurons=max_num_neurons,
                 evol_alg=evol_alg, sel=sel, lrate=lrate, cxp=cxp, mtp=mtp,
                 seed=seed, sel_kwargs=sel_kwargs, max_filter=max_filter, max_stride=max_stride)
            print(x)
        except Exception as e:
            print('An error ocurred executing the {} dataset.'.format(dataset))    
            print(e)
            
        print('Time: ', time.time() - init_time)

def test_TCNN(dataset_name, eval_func=None, batch_size=150, population=5, 
             generations=10, iters=100, max_num_layers=10, max_num_neurons=20,
             evol_alg='mu_plus_lambda', sel='best', lrate=0.01, cxp=0, mtp=1,
             seed=None, sel_kwargs={}, max_filter=4, max_stride=3):
    """
    Tests the TCNN network with the specified dataset and parameter selection.

    :param dataset_name: Name of the dataset that will be used in the genetic algorithm.
    :param eval_func: Evaluation function for evaluating each network.
    :param batch_size: Batch size of the data during the training of the networks.
    :param population: Number of individuals in the populations in the genetic algorithm.
    :param generations: Number of generations that will be done in the genetic algorithm.
    :param iters: Number of iterations that each network will be trained.
    :param max_num_layers: Maximum number of layers allowed in the networks.
    :param max_num_neurons: Maximum number of neurons allowed in the networks.
    :param max_filter: Maximum size of the filter allowed in the networks.
    :param max_stride: Maximum size of the stride allowed in the networks.
    :param evol_alg: Evolving algorithm that will be used during the genetic algorithm.
    :param sel: Selection method that will be used during the genetic algorithm.
    :param sel_kwargs: Arguments for selection method.
    :param lrate: Learning rate that will be used during training.
    :param cxp: Crossover probability that will be used during the genetic algorithm.
    :param mtp: Mutation probability that will be used during the genetic algorithm.
    :param seed: Seed that will be used in every random method.
    :return: The last generation, a log book (stats) and the hall of fame (the best 
                 individuals found).
    """

    x_train, x_test, x_val, _, _, _, mode = load_dataset(dataset_name)
    
    x_train = x_train[:5000]/255
    x_test = x_test[:2500]/255
    x_val = x_val[:2500]/255
    
    train_noise = np.random.normal(size=(x_train.shape[0], 7, 7, 1))
    test_noise = np.random.normal(size=(x_test.shape[0], 7, 7, 1))
    val_noise = np.random.normal(size=(x_val.shape[0], 7, 7, 1))
    
    input_shape = train_noise.shape[1:]
    output_shape = x_train.shape[1:]
    
    if eval_func == None:
        eval_func = select_evaluation(mode)
    
    e = Evolving(evaluation=eval_func, 
			 desc_list=[TCNNDescriptor], 
			 x_trains=[train_noise], y_trains=[x_train], 
			 x_tests=[val_noise], y_tests=[x_val],
			 n_inputs=[input_shape],
			 n_outputs=[output_shape],
			 batch_size=batch_size,
			 population=population,
			 generations=generations,
			 iters=iters, 
			 max_num_layers=max_num_layers, 
			 max_num_neurons=max_num_neurons,
             hyperparameters={"lrate": [0.1, 0.5, 1], "optimizer": [0, 1, 2]})   
     
    a = e.evolve()
    return a 

def eval_tcnn(nets, train_inputs, train_outputs, batch_size, iters, test_inputs, test_outputs, hypers):
    """
    Evaluation method for the TCNN. Noise is given to the model and mean squared
    error is used to calculate how the recostruction of the data has been done.
    
    :param nets: Dictionary with the networks that will be used to build the 
                 final network and that represent the individuals to be 
                 evaluated in the genetic algorithm.
    :param train_inputs: Input data for training, this data will only be used to 
                         give it to the created networks and train them.
    :param train_outputs: Output data for training, it will be used to compare 
                          the returned values by the networks and see their performance.
    :param batch_size: Number of samples per batch are used during training process.
    :param iters: Number of iterations that each network will be trained.
    :param test_inputs: Input data for testing, this data will only be used to 
                        give it to the created networks and test them. It can not be used during
                        training in order to get a real feedback.
    :param test_outputs: Output data for testing, it will be used to compare 
                         the returned values by the networks and see their real performance.
    :param hypers: Hyperparameters that are being evolved and used in the process.
    :return: Mean squared error obtained with the test data that evaluates the true
             performance of the network.
    """

    inp = Input(shape=train_inputs["i0"].shape[1:])
    out = nets["n0"].building(inp)
    
    model = Model(inputs=inp, outputs=out)
    model.summary()
    opt = optimizers[hypers["optimizer"]](learning_rate=hypers["lrate"])
    model.compile(loss=tf.losses.mean_squared_error, optimizer=opt, metrics=[])
    
    model.fit(train_inputs['i0'], train_outputs['o0'], epochs=iters, batch_size=batch_size, verbose=0)

    pred = model.predict(test_inputs["i0"])
    
    ev = mean_squared_error(pred.flatten(), test_outputs["o0"].flatten())
    return ev,
    
if __name__ == "__main__":
    test_TCNN_all_datasets(eval_func=eval_tcnn, batch_size=150, population=2, generations=4, iters=10)