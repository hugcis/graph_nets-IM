from tqdm import tqdm as base_tqdm
from ic_influence_maximization.utils import in_neighbors, pp, miia

def hsh(i, lst):
    return int( str(hash(repr(lst))) + str(hash(i)))
    
def ap(u, S, miia_v_theta, grph, cache={}, cnt=0):
    """ Compute activation probability of node 
    u, from set S and maximum influence in-arboresence
    miia_v_theta.
    """
    n_in = in_neighbors(u, miia_v_theta)
    if u in S:
        return 1.
    elif not len(n_in):
        return 0.
    else:
        base = 1
        for in_neighbor in n_in:
            if hsh(in_neighbor, miia_v_theta) in cache:
                p = cache[hsh(in_neighbor, miia_v_theta)]
            else:
                p =  ap(in_neighbor, S, miia_v_theta, grph, cache)
                cache[hsh(in_neighbor, miia_v_theta)] = p
            base *= (1 - p*pp(in_neighbor, u, grph))
        return 1 - base
    
def naive_greedy_algorithm(n_source, grph, tqdm_function=base_tqdm):
    s = []

    for _ in tqdm_function(range(n_source)):
        max_influence = 0
        max_node = 0
        shared_cache = {}
        for node in tqdm_function(range(grph.number_of_nodes())):
            if not node in s:
                influence = sum(
                    ap(i, s + [node], 
                       miia(i, 0.001, grph), 
                       grph, 
                       cache=shared_cache) 
                    for i in range(grph.number_of_nodes()))
        
                if influence > max_influence:
                    max_node = node
                    max_influence = influence
        s.append(max_node)
    
    return s