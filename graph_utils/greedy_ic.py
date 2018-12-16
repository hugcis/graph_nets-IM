from graph_utils.utils import in_neighbors, pp

def hsh(i, lst):
    return int( str(hash(repr(lst))) + str(hash(i)))
    
def ap(u, S, miia_v_theta, grph, cache={}):
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
            if hsh(in_neighbor,miia_v_theta) in cache:
                p = cache[hsh(in_neighbor,miia_v_theta)]
            else:
                p =  ap(in_neighbor, S, miia_v_theta, grph, cache)
                cache[hsh(in_neighbor,miia_v_theta)] = p
            base *= (1 - p*pp(in_neighbor, u, grph))
        return 1 - base