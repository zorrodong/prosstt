#!/usr/bin/env python
# coding: utf-8
"""
This module contains utility functions for the Tree class.
"""

import numpy as np
import pandas as pd

def parse_newick(newick_tree, def_time):
    """
    Function that translates a Newick tree to a prosstt Tree object.

    Parameters
    ----------
    newick_tree: Newick tree
        A Newick tree object as returned by the loads function of the newick
        package
    def_time: int
        The default pseudotime length of each tree branch

    Returns
    -------
    topology: list
        A list of connected branch names
    time: dict
        Contains the pseudotime length of each branch
    branches: list
        The name of each branch
    branch_points: int
        The number of branch points in the lineage tree
    root: str
        The name of the root of the lineage tree
    """
    topology = list()
    time = {}
    branches = 0
    branch_points = 0
    root = None
    for node in newick_tree[0].walk():
        branches += 1
        if node.length == 0:
            time.update({node.name: def_time})
        else:
            time.update({node.name: np.int(node.length)})

        if not node.descendants:
            continue
        else:
            branch_points += 1
            for descendant in node.descendants:
                topology.append([node.name, descendant.name])

        if node.ancestor is None:
            root = node.name
    return topology, time, branches, branch_points, root


def save_cell_params(job_id, save_dir, labs, brns, scalings):
    cell_names = ["cell_" + str(i) for i, l in enumerate(labs)]
    cell_params = pd.DataFrame({"pseudotime": labs,
                                "branches": brns,
                                "scalings": scalings},
                               index=cell_names,
                               columns=["pseudotime", "branches", "scalings"])
    cell_params.to_csv(save_dir + "/" + job_id + "_cellparams.txt", sep="\t")


def save_gene_params(job_id, save_dir, gene_scale, alpha, beta):
    gene_names = ["gene_" + str(i) for i, a in enumerate(alpha)]
    gene_params = pd.DataFrame({"alpha": alpha,
                                "beta": beta,
                                "genescale": gene_scale},
                               index=gene_names,
                               columns=["alpha", "beta", "genescale"])
    gene_params.to_csv(save_dir + "/" + job_id + "_geneparams.txt", sep="\t")


def save_matrices(job_id, save_dir, X, uMs, H):
    cell_names = ["cell_" + str(i) for i in range(X.shape[0])]
    gene_names = ["gene_" + str(i) for i in range(X.shape[1])]

    expr_mat = pd.DataFrame(X, columns=gene_names,
                            index=cell_names).astype(int)
    expr_mat.to_csv(save_dir + "/" + job_id + "_simulation.txt", sep="\t")

    np.savetxt(fname=save_dir + "/" + job_id + "_h.txt", X=H)

    for branch in uMs.keys():
        np.savetxt(fname=save_dir + "/" + job_id + "_ums" + str(branch) + ".txt",
                   X=uMs[branch])


def save_params(job_id, save_dir, lineage_tree, rseed):
    paramfile = save_dir + "/" + job_id + "_params.txt"
    with open(paramfile, 'w') as out:
        out.write("Genes: " + str(lineage_tree.G) + "\n")
        out.write("pseudotimes: " + str(list(lineage_tree.time.values)) + "\n")
        out.write("topology: " + str(lineage_tree.topology) + "\n")
        out.write("#modules: " + str(lineage_tree.modules) + "\n")
        out.write("random seed: " + str(rseed))


def sanitize_velocity(velocity, minimum_velocity=0.1):
    global_min = 0
    for key in velocity:
        branch_min = np.min(velocity[key])
        if branch_min < global_min:
            global_min = branch_min

    if global_min >= 0:
        return velocity

    for key in velocity:
        velocity[key] = velocity[key] + np.abs(global_min) + minimum_velocity

    return velocity


def _density_from_velocity(velocity):
    total_velocity = 0
    total_density = 0
    global_min = np.Inf
    global_max = -np.Inf
    density = {}
    for b in velocity:
        total_velocity += np.sum(velocity[b])
        if global_max <= np.max(velocity[b]):
            global_max = np.max(velocity[b])
        if global_min >= np.min(velocity[b]):
            global_min = np.min(velocity[b])
    
    global_min /= total_velocity
    global_max /= total_velocity
    for b in velocity:
        velocity[b] /= total_velocity
        density[b] = - velocity[b] + global_max + global_min
        total_density += np.sum(density[b])
    for b in velocity:
        density[b] /= total_density
    return density