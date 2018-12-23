""" All the acronyms refer to quantities defined in [1].
This is an implementation of the PMIA algorithm [1] inspired by Github user
nd7141's implementation.

[1] -- Scalable Influence Maximization for Prevalent Viral Marketing in
Large-Scale Social Networks.
"""
import networkx as nx
import numpy as np
from tqdm import tqdm as base_tqdm

ALPHA_ASSERT = "node u=%s must have exactly one neighbor, got %s instead"

def update_ap(ap, S, pmiia, pmiia_mip):
    ''' Assumption: PMIIAv is a directed tree, which is a subgraph of general G.
    PMIIA_MIPv -- dictionary of MIP from nodes in PMIIA
    PMIIAv is rooted at v.
    '''
    # going from leaves to root
    sorted_mips = sorted(pmiia_mip.items(), 
                         key = lambda x: len(x[1]), 
                         reverse = True)
    for u, _ in sorted_mips:
        if u in S:
            ap[(u, pmiia)] = 1
        elif not pmiia.in_edges([u]):
            ap[(u, pmiia)] = 0
        else:
            in_edges = pmiia.in_edges([u])
            prod = 1
            for w, _ in in_edges:
                p = pmiia.edges[(w,u)]['transition_proba']
                prod *= 1 - ap[(w, pmiia)]*p
            ap[(u, pmiia)] = 1 - prod

def update_alpha(alpha, node, S, pmiia, pmiia_mip, ap):
    # going from root to leaves
    sorted_mips = sorted(pmiia_mip.items(), key=lambda x: len(x[1]))
    for u, _ in sorted_mips:
        if u == node:
            alpha[(pmiia, u)] = 1
        else:
            out_edges = list(pmiia.out_edges([u]))
            assert len(out_edges) == 1, ALPHA_ASSERT % (u, len(out_edges))
            w = out_edges[0][1]
            if w in S:
                alpha[(pmiia, u)] = 0
            else:
                in_edges = pmiia.in_edges([w])
                prod = 1
                for up, _ in in_edges:
                    if up != u:
                        pp_up = pmiia.edges[up, w]['transition_proba']
                        prod *= (1 - ap[(up, pmiia)] * pp_up)
                pp = pmiia.edges[u, w]['transition_proba']
                alpha[(pmiia, u)] = alpha[(pmiia, w)] * pp * prod


def compute_pmiia(graph, inactive_seeds, node, theta, S):

    # initialize PMIIA
    pmiia = nx.DiGraph()
    pmiia.add_node(node)
    pmiia_mip = {node: [node]} # MIP(u,v) for u in PMIIA

    crossing_edges = set([in_edge for in_edge in graph.in_edges([node]) 
                          if in_edge[0] not in inactive_seeds + [node]])
    edge_weights = dict()
    dist = {node: 0} # shortest paths from the root u

    # grow PMIIA
    while crossing_edges:
        # Dijkstra's greedy criteria
        min_dist = np.Inf
        sorted_crossing_edges = sorted(crossing_edges) # to break ties consistently
        for edge in sorted_crossing_edges:
            if edge not in edge_weights:
                edge_weights[edge] = graph.edges[edge]['log_transition_proba']
        
            edge_weight = edge_weights[edge]
            if dist[edge[1]] + edge_weight < min_dist:
                min_dist = dist[edge[1]] + edge_weight
                min_edge = edge
        # check stopping criteria
        if min_dist < -np.log(theta):
            dist[min_edge[0]] = min_dist
            pmiia.add_edge(
                min_edge[0], 
                min_edge[1],
                log_transition_proba=min_dist,
                transition_proba=np.exp(-min_dist))

            pmiia_mip[min_edge[0]] = pmiia_mip[min_edge[1]] + [min_edge[0]]
            # update crossing edges
            crossing_edges.difference_update(graph.out_edges(min_edge[0]))
            if min_edge[0] not in S:
                crossing_edges.update([in_edge for in_edge in graph.in_edges(min_edge[0])
                                       if (in_edge[0] not in pmiia) and 
                                       (in_edge[0] not in inactive_seeds)])
        else:
            break
    return pmiia, pmiia_mip


def compute_pmioa(graph, node, theta, S):
    """
     Compute PMIOA -- subgraph of G that's rooted at u.
     Uses Dijkstra's algorithm until length of path doesn't exceed -log(theta)
     or no more nodes can be reached.
    """
    # initialize PMIOA
    pmioa = nx.DiGraph()
    pmioa.add_node(node)
    pmioa_mip = {node: [node]} # MIP(u,v) for v in PMIOA

    crossing_edges = set([out_edge for out_edge in graph.out_edges([node]) 
                          if out_edge[1] not in S + [node]])
    edge_weights = dict()
    dist = {node: 0} # shortest paths from the root u

    # grow PMIOA
    while crossing_edges:
        # Dijkstra's greedy criteria
        min_dist = np.inf
        # break ties consistently with the sort
        sorted_crossing_edges = sorted(crossing_edges) 
        for edge in sorted_crossing_edges:
            if edge not in edge_weights:
                edge_weights[edge] = graph.edges[edge]['log_transition_proba']
            edge_weight = edge_weights[edge]
            if dist[edge[0]] + edge_weight < min_dist:
                min_dist = dist[edge[0]] + edge_weight
                min_edge = edge
        # check stopping criteria
        if min_dist < -np.log(theta):
            dist[min_edge[1]] = min_dist
            pmioa.add_edge(
                min_edge[0], 
                min_edge[1],
                log_transition_proba=min_dist,
                transition_proba=np.exp(-min_dist))

            pmioa_mip[min_edge[1]] = pmioa_mip[min_edge[0]] + [min_edge[1]]
            # update crossing edges
            crossing_edges.difference_update(graph.in_edges(min_edge[1]))
            crossing_edges.update([
                out_edge for out_edge in graph.out_edges(min_edge[1])
                if (out_edge[1] not in pmioa) 
                and (out_edge[1] not in S)])
        else:
            break
    return pmioa, pmioa_mip

def update_inactive_seeds(inactive_seeds, S, node, pmioa, pmiia):
    for v in pmioa[node]:
        for si in S:
            # if seed node is effective and it's blocked by u
            # then it becomes ineffective
            if ((si in pmiia[v]) and 
                (si not in inactive_seeds[v]) and 
                (node in pmiia[v][si])):
                    inactive_seeds[v].append(si)


def pmia(graph, k, theta,  tqdm_function=base_tqdm):
    # initialization
    S = []
    inc_inf = dict(zip(graph.nodes, [0] * len(graph)))
    pmiia = dict() # node to tree
    pmioa = dict()
    pmiia_mip = dict() # node to MIPs (dict)
    pmioa_mip = dict()
    ap = dict()
    alpha = dict()
    inactive_seeds = dict()
    
    # Initialization
    #for node in tqdm_function(graph, desc="Initialization"):
    for node in graph:
        inactive_seeds[node] = []
        pmiia[node], pmiia_mip[node] = compute_pmiia(
            graph, 
            inactive_seeds[node], 
            node, 
            theta, 
            S)
        
        for u in pmiia[node]:
            ap[(u, pmiia[node])] = 0 # ap of u node in PMIIA[v]
        update_alpha(alpha, node, S, pmiia[node], pmiia_mip[node], ap)
        for u in pmiia[node]:
            inc_inf[u] += alpha[(pmiia[node], u)]*(1 - ap[(u, pmiia[node])])
    
    # Main Loop
    #for _ in tqdm_function(range(k), desc="Nodes added to set"):
    for _ in range(k):
        node, _ = max(inc_inf.items(), key = lambda x: x[1])
        inc_inf.pop(node) # exclude node u for next iterations

        pmioa[node], pmioa_mip[node] = compute_pmioa(graph, node, theta, S)
        for v in pmioa[node]:
            for w in pmiia[v]:
                if w not in S + [node]:
                    inc_inf[w] -= alpha[(pmiia[v],w)] * (1 - ap[(w, pmiia[v])])

        update_inactive_seeds(inactive_seeds, S, node, pmioa_mip, pmiia_mip)
        S.append(node)

        #for v in tqdm_function(pmioa[node], leave=False):
        for v in pmioa[node]:
            if v != u:
                pmiia[v], pmiia_mip[v] = compute_pmiia(
                    graph, inactive_seeds[v], v, theta, S)
                update_ap(ap, S, pmiia[v], pmiia_mip[v])
                update_alpha(alpha, v, S, pmiia[v], pmiia_mip[v], ap)
                # add new incremental influence
                for w in pmiia[v]:
                    if w not in S:
                        inc_inf[w] += alpha[(pmiia[v], w)]*(1 - ap[(w, pmiia[v])])

    return S