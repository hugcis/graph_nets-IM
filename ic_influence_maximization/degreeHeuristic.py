import numpy as np


def degreeHeuristic(graph, num_nodes=5):
    log_transition_proba=list(graph.edges.values())
    c=0
    dict_=[]
    for j in graph.nodes: 
        degree=0
        for i in range(len(list(graph.edges(j)))): 
            degree+=log_transition_proba[c+i]['log_transition_proba']
        dict_.append(degree)
        c+=len(list(graph.edges(j)))-1
    dict_=np.array(dict_)
    S=np.argsort(dict_)[:num_nodes]
    return S