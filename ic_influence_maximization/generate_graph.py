import networkx as nx
import numpy as np

def generate_graph(rand=None,
                   num_nodes_min_max=[10, 11],
                   rate=0.4,
                   weight_min_max=[0, 0.1],
                   directed=False):
    """Creates a connected graph.

    Args:
        rand: A random seed for the graph generator. Default= None.
        num_nodes_min_max: A sequence [lower, upper) number of nodes per graph.
        weight_min_max: A sequence [lower, upper) transition probabilities for the 
            edges in the graph

    Returns:
        The graph.
    """
    
    if rand is None:
        seed = 2
        rand = np.random
        rand.seed(seed)
        
    
    # Sample num_nodes.
    num_nodes = rand.randint(*num_nodes_min_max)

    # Create geographic threshold graph.
    rand_graph = nx.fast_gnp_random_graph(num_nodes, rate, directed=directed)
    weights = np.random.uniform(weight_min_max[0], 
                                weight_min_max[1], 
                                rand_graph.number_of_edges())
    weights_dict = dict(zip(rand_graph.edges, 
                            weights))
    log_weights_dict = dict(zip(rand_graph.edges, 
                                -np.log(weights)))
    
    nx.set_edge_attributes(rand_graph, weights_dict, 'transition_proba')
    nx.set_edge_attributes(rand_graph, log_weights_dict, 'log_transition_proba')
    
    return rand_graph