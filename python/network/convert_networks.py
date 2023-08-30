"""
    convert_networks.py: converts ensembl/Biogrid files to a json format
"""
__author__ = "Anna Sheaffer"
__email__ = "asheaffe@iwu.edu"
__date__ = "June 24, 2022"

import sys
import json
from python.classes import Orthogroups

def main():
    network_yeast = '../../../PPI-Network-Alignment/networks/s_cerevisiae.network-109-4.4.219.txt'  # species 1
    network_worm = '../../../PPI-Network-Alignment/networks/c_elegans.network-109-4.4.219.txt'      # species 2

    # access ensembl data from PPI-Network-Alignment repo
    ensembl_ncbi_yeast = "../../../PPI-Network-Alignment/ensembl/s_cerevisiae_ensembl_ncbi-109.txt"
    ensembl_others_yeast = "../../../PPI-Network-Alignment/ensembl/s_cerevisiae_ensembl_others-109.txt"
    ensembl_ncbi_worm = "../../../PPI-Network-Alignment/ensembl/c_elegans_ensembl_ncbi-109.txt"
    ensembl_others_worm = "../../../PPI-Network-Alignment/ensembl/c_elegans_ensembl_others-109.txt"

    # assemble ensembl data from each species
    data_yeast = extract_ensembl_data_ncbi(ensembl_ncbi_yeast)
    ensembl_data_yeast = extract_ensembl_data_other_ids(ensembl_others_yeast, data_yeast)

    data_worm = extract_ensembl_data_ncbi(ensembl_ncbi_worm)
    ensembl_data_worm = extract_ensembl_data_other_ids(ensembl_others_worm, data_worm)
    
    # assemble network data from each species
    network_data_yeast = read_network_file(network_yeast)
    network_dict_yeast = list_to_dict(network_data_yeast)

    network_data_worm = read_network_file(network_worm)
    network_dict_worm = list_to_dict(network_data_worm)

    subnetwork = query_subnetwork(network_dict_yeast, 'YOL139C', network_dict_worm, 'WBGene00002061', ensembl_data_yeast, ensembl_data_worm, "S cerevisiae", "C elegans")

    node_dict = nodes_from_json(subnetwork)

    network_dict = create_network_dict(subnetwork)

    # orthology data for worm and yeast
    ortho_network, ortho_dict = compile_ortho_json(subnetwork, "S cerevisiae", "C elegans", network_dict_yeast, network_dict_worm)
    
    # create json for alignment view
    alignment_data = query_alignment_data("S cerevisiae", "C elegans", node_dict)
    align_subnetwork = find_alignment_classes(subnetwork, alignment_data, ortho_dict, network_dict)

    align_network = alignment_to_json(align_subnetwork, ortho_network, ensembl_data_yeast, ensembl_data_worm, network_dict, node_dict)

    final_output = json.dumps(align_network)

    with open("../../json/a_demo.json", 'w') as test_network:
        test_network.write(str(final_output))

    print("JSON file for alignment view compiled")

def alignment_to_json(alignment_data, ortho_network, ensembl_data_s1, ensembl_data_s2, network_dict, node_dict):
    """Creates a list of network elements using JSON conventions
    
    :param alignment_data: dict of aligned protein pairs (tuple) as key and their classification as def
    :param ortho_network: subnetworks for orthology view in JSON format
    :param ensembl_data_s1: dict ensembl data for species 1
    :param ensembl_data_s2: dict ensembl data for species 2
    :param network_dict: dict of network elements with each protein as the key and json network ele as def
    :param node_dict: dictionary of each node ensembl id as key with the species (species1/species2) as def
    :return: list of JSON elements"""
    # change the classes of the first two nodes to not be a container
    ortho_network[0]['classes'] = 'alignment s1'
    ortho_network[1]['classes'] = 'alignment s2'
    align_network = [ortho_network[0], ortho_network[1]]

    # combine species1 and species2 ensembl dicts into one
    ensembl_data = ensembl_data_s1
    ensembl_data.update(ensembl_data_s2)
    
    # keeps track of proteins already added to align_network and associated id
    prots_added = set()

    # keeps track of the ids added to align_network and their associated alignment classes
    ids_added = {}

    # dictionary that indicates which nodes are in a group
    node_parents = {}
    parent = "group0"

    for protein in alignment_data:

        # create an ortho/aligned edge between this protein and each protein in its dict
        for match in alignment_data[protein]:
            new_edge = {}
            match_class = alignment_data[protein][match]

            if match in network_dict and protein in network_dict:
                
                # separate the class based on underscore
                match_class_list = match_class.split("_")

                # replace orthology class with alignment class
                node_class_list1 = network_dict[protein]['classes'].split(" ")
                node_class_list2 = network_dict[match]['classes'].split(" ")

                # vars for each protein id for better readability
                id1 = network_dict[protein]['data']['id']
                id2 = network_dict[match]['data']['id']

                # keep align_ortho nodes
                # if match_class != "align_ortho" and id1 in ids_added:
                #     class_update_1 = [match_class if 'ortho' in x else x for x in node_class_list1]
                # elif match_class != "align_ortho" and id2 in ids_added:
                #     class_update_2 = [match_class if 'ortho' in x else x for x in node_class_list2]
                #     print(ids_added[id1])
                # elif id1 not in ids_added and id2 not in ids_added:
                class_update_1 = [match_class if 'ortho' in x else x for x in node_class_list1]
                class_update_2 = [match_class if 'ortho' in x else x for x in node_class_list2]

                # check if the nodes are already in the parent dictionary
                if id1 in node_parents:
                    assign_parent = node_parents[id1]
                elif id2 in node_parents:
                    assign_parent = node_parents[id2]
                else:
                    assign_parent = parent

                    # add a group node
                    group_node = {'data':
                                  {
                                      'id': assign_parent,
                                      'name': ""
                                  },
                                  'classes': 'compound'}
                    
                    align_network.append(group_node)

                    # update last value in the parent group name
                    parent_num_old = int(parent[-1])
                    parent_num_new = parent_num_old + 1
                    parent = parent.replace(str(parent_num_old), str(parent_num_new))

                # give the parent dictionary the id values
                node_parents[id1] = assign_parent
                node_parents[id2] = assign_parent

                # update the node with the alignment classes
                node_update1 = network_dict[protein]
                node_update1['classes'] = " ".join(class_update_1)
                node_update1['data']['parent'] = assign_parent

                node_update2 = network_dict[match]
                node_update2['classes'] = " ".join(class_update_2)
                node_update2['data']['parent'] = assign_parent

                new_edge = {
                    'data': {
                        'source': id1,
                        'target': id2,
                        'weight': 5
                    }
                }

                if "ortho" in match_class_list and "nonalign" in match_class_list:
                    new_edge['classes'] = 'ortho_edge'

                elif "align" in match_class_list and "nonortho" in match_class_list:
                    new_edge['classes'] = 'align_edge'
                
                elif "align" in match_class_list and "ortho" in match_class_list:
                    new_edge['classes'] = 'alignortho_edge'

                if new_edge:
                    # add the protein to the alignment network if it isn't already in it
                    if protein not in prots_added:
                        align_network.append(node_update1)

                    if match not in prots_added:
                        align_network.append(node_update2)

                    # keep track of proteins and ids added
                    prots_added.add(match)
                    prots_added.add(protein)
                    ids_added[id1] = match_class
                    ids_added[id2] = match_class

                    # add the edge to the network
                    align_network.append(new_edge)

    # loop thru network data to add interaction edges for proteins in alignment view
    for data in ortho_network:
        if 'source' in data['data']:
            temp_id1 = data['data']['source']
            temp_id2 = data['data']['target']

            if temp_id1 in ids_added and temp_id2 in ids_added:
                # change the class to equal to the alignment class if aligned
                if ids_added[temp_id1] == ids_added[temp_id2] and 'nonalign' not in ids_added[temp_id1]:
                    data['classes'] = ids_added[temp_id1]
                else:
                    # replace 'edge' with 'plain_interaction'
                    temp_classes = data['classes'].replace('edge', 'plain_interaction')
                    data['classes'] = temp_classes

                    data['data']['weight'] = 1

                align_network.append(data)

    # sort network elements based on classes                
    #align_network = sorted(align_network, key=lambda node: node['classes'])

    # for ele in align_network:
    #     print(ele)
    return align_network

def compile_ortho_json(query_subnetwork, species1, species2, network_dict_s1, network_dict_s2):
    """Compiles the JSON file for orthology view
    
    :param query_subnetwork: subnetwork compiled from query_subnetwork()
    :param species1: shortened scientific name for species 1
    :param species2: shortened scientific name for species 2
    :param network_dict_s1: network dict species 1
    :param network_dict_s2: network dict species 2
    :return: dictionary of orthologous proteins"""

    orthology_data = query_orthology_data(species1, species2)

    node_dict = nodes_from_json(query_subnetwork)

    matched_groups = combine_network_ortho(node_dict, orthology_data)

    ortho_nonexist, ortho_exists_in, ortho_exists_out, ortho_dict = find_ortho_classes(query_subnetwork, node_dict, matched_groups, network_dict_s1, network_dict_s2)

    ortho_subnetwork = add_ortho_to_json(ortho_nonexist, ortho_exists_in, ortho_exists_out, query_subnetwork)

    final_output = json.dumps(ortho_subnetwork)

    with open("../../json/o_demo.json", 'w') as test_network:
        test_network.write(str(final_output))

    print("JSON file for orthology view compiled")

    return ortho_subnetwork, ortho_dict

def create_network_dict(network_list):
    """Makes a dictionary for network data for easier iteration through the network
    
    :param network_list: list of network data with ortho classes in JSON format (output of add_ortho_to_json())
    :return: dict with protein name as key and corresponding entry as def"""
    prot_dict = {}
    for ele in network_list:
        if 'e_id' in ele['data']:
            prot_dict[ele['data']['e_id']] = ele

    return prot_dict

def find_alignment_classes(network_list, alignment_data, ortho_dict, network_dict):
    """Takes set of alignment data and the list of network data in JSON format with orthology
    classifications and determines the alignment classifications
    
    :param network_list: list of network data with ortho classes in JSON format (output of add_ortho_to_json())
    :param alignment_data: set of tuples with aligned proteins (from query_alignment_data())
    :param ortho_dict: dictionary that indicates which nodes are orthologous to it
    :param network_dict: dictionary of network elements for easier lookup
    :return: dictionary of each node as key and alignment class as def"""
    align_dict = {}

    for alignment in alignment_data:
        for protein in alignment:
            
            # keep track of the index of current element
            index = alignment.index(protein)

            if protein in network_dict and alignment[index-1] in network_dict:

                # set default to aligned nonorthologous if the protein is in the network
                align_dict[protein] = {alignment[index-1]: "align_nonortho"} 
                align_dict[alignment[index-1]] = {protein: "align_nonortho"}

                # overwrite align_nonortho to align_ortho if the node is also orthologous
                if 'ortho_exists_in' in network_dict[protein]['classes']:
                    align_dict[protein] = {alignment[index-1]: "align_ortho"} 
                    align_dict[alignment[index-1]] = {protein: "align_ortho"}

    # get the difference between proteins added to align_dict and proteins added to network_dict
    network_diff = set(network_dict.keys()) - (set(align_dict.keys()))

    # assign each element in the network diff set after the for loop to nonalign_ortho
    for leftover in network_diff:
        
        # if the leftover protein is not in the ortho_dict, then it is not orthologous so exclude it
        if leftover in ortho_dict and ortho_dict[leftover] in network_dict:
            ortho = ortho_dict[leftover]

            left_species = network_dict[leftover]
            left_species = left_species['data']['id'][0]

            ortho_species = network_dict[ortho]
            ortho_species = ortho_species['data']['id'][0]

            # make sure the two proteins are from different species
            if left_species != ortho_species:
                align_dict[leftover] = {ortho_dict[leftover]: "nonalign_ortho"}
                align_dict[ortho_dict[leftover]] = {leftover: "nonalign_ortho"}
        
    # iterate through all network data
    # for i in range(len(network_list)):
    #     if 'e_id' in network_list[i]['data']:
    #         if 'ortho_exists_in' in network_list[i]["classes"]:
    #             current_id = network_list[i]['data']['e_id']

    #             for alignment in alignment_data:

    #                 if network_list[i]['data']['e_id'] in alignment:
                        
    #                     index = alignment.index(current_id)

    #                     if alignment[index-1] in ortho_dict[alignment[index]]:
    #                         align_dict[alignment] = "align_ortho"

    #             # keep first element species 1 and second element species 2
    #             # ortho_pair = tuple([current_id, ortho_dict[current_id]])
    #             # ortho_pair_inverse = tuple([ortho_dict[current_id], current_id])

    #             if current_id in ortho_dict and ortho_pair not in align_dict:
    #                 align_dict[ortho_pair] = "nonalign_ortho"
    
    return align_dict

def query_alignment_data(species1, species2, node_dict):
    """Takes alignment data and queried network data and returns a set of tuples with aligned
    nodes
    
    :param species1: shortened scientific name of species 1 as str
    :param species2: shortened scientific name of species 2 as str
    :param node_dict: list of all nodes and their species within the query subnetwork
    :return: set of tuples containing aligned nodes from separate species"""
    # TODO: open file that correlates with the input species1/species2
    filepath = "../../../PPI-Network-Alignment/alignments/basic/worm_yeast.align"

    temp_dict = node_dict

    # a set of tuples for pairs of nodes that are from the query and aligned
    # if only one node is in an alignment in the query, exclude it from the set
    alignments = set()
    # open the alignment file and iterate through each entry
    with open(filepath, 'r') as file:

        # while there are still proteins in the node_list
        for line in file:

            # only continue iterating through file while there are elements left in temp_list
            if temp_dict:
                line = line.strip().split("\t")

                prot_pair = False
                # check each element in line
                for prot in line:
                    if prot in node_dict:
                        prot_pair = True
                        del temp_dict[prot]
                    else:
                        prot_pair = False
                
                # only add elements that are both in the queried subnetworks
                if prot_pair:
                    alignments.add(tuple(line))
            else:
                break
    
    return alignments


def find_ortho_classes(network_list, node_dict, matched_dict, network_dict_s1, network_dict_s2):
    """Takes the JSON network_list and adds the orthology data based on matched_dict
    
    :param network_list: list of network elements in JSON format
    :param node_dict: dict of gene ids as key, species for specified id as def from the network list
    :param matched_dict: dictionary of network data matched with orthology data
    :param network_dict_s1: all of the proteins in the species1 network
    :param network_dict_s2: all of the proteins in the species2 network
    :return: updated network data list"""
    ortho_exists_out = set()
    ortho_exists_in = set()
    ortho_nonexist = set()
    ortho_dict = {}     # used to indicate which proteins each node in the network is orthologous to

    # check every line in the network_list
    for node in network_list:
        # get only the proteins from the data
        if 'e_id' in node['data']:
            # current id is the ensembl id of the current element with its species
            current_id = node['data']['e_id']
            current_species = node_dict[current_id]

            temp = False

            if current_species == "species1":
                temp = current_id in network_dict_s1
            else:
                temp = current_id in network_dict_s2
            
            # if the current id has a species
            if temp:
                # if the current id is in one of the subnetworks
                if current_id in matched_dict:
                    
                    # add elements to ortho_dict from matched_dict data
                    ortho_dict.update({prot:current_id for prot in matched_dict[current_id]})
                    ortho_dict.update({current_id:prot for prot in  matched_dict[current_id]})

                    for ortho in matched_dict[current_id]:
                        
                        try:
                            # checks if the current protein is already in the network

                            # ortho_species holds the species number for the orthologous protein if it is in either subnetwork
                            ortho_species = node_dict[ortho]
                        except KeyError as ke:
                            # if it's not set to None
                            ortho_species = None
                        finally:
                            # filters for the same protein (?)
                            # if the species of the current node is not equal to the species of the orthologous node
                            if current_species != ortho_species:
                                # if the orthologous node is in one of the subnetworks
                                if ortho in node_dict:
                                    ortho_exists_in.add(current_id)

                                # if the orthologous node is not in one of the subnetworks
                                else:
                                    ortho_exists_out.add(current_id)

            # otherwise, check if the protein is in the subnetworks queried for each species
            # loop over all proteins in the orthogroup for the given protein in the network
            else:
                ortho_nonexist.add(current_id)
    
    return ortho_nonexist, ortho_exists_in, ortho_exists_out, ortho_dict

def add_ortho_to_json(ortho_nonexist, ortho_in, ortho_out, network_list):
    """Takes sets with different orthology classifications, adds classification to the class of each node
    
    :param ortho_nonexist: set of orthologous proteins that don't exist in the network
    :param ortho_in: set of orthologous proteins that exist in the opposite species' subnetwork
    :param ortho_out: set of orthologous proteins that exist in the network but not in the opposite species' subnetwork
    :param network_list: list of nodes and edges in JSON format
    :return: updated list of JSON elements with orthology data"""
    temp = network_list

    # loop through every index of network_list
    for i in range(len(network_list)):

        # check only proteins
        if 'e_id' in network_list[i]['data']:
            current_id = network_list[i]['data']['e_id']

            if current_id in ortho_nonexist:
                temp[i]['classes'] += " ortho_nonexist"
            
            elif current_id in ortho_in:
                temp[i]['classes'] += " ortho_exists_in"

            elif current_id in ortho_out:
                temp[i]['classes'] += " ortho_exists_out"
            
            # if the current protein is not in any of these sets, it is not orthologous
            else:
                temp[i]['classes'] += " nonortho"

    # sort based on class values so that nodes display based orthology status
    sorted_dict = sorted(temp, key=lambda node: node['classes'])

    return sorted_dict

def nodes_from_json(network_list):
    """Creates a list of all node gene ids
    
    :param network_list: list of network elements in json format
    :return: list of gene ids that are nodes in the network"""
    id_dict = {}
    for ele in network_list:
        if 'protein' in ele['classes']:
            gene_id = ele['data']['e_id']
            species = "species" + ele['data']['id'][0]
            id_dict[gene_id] = species
    
    return id_dict

def combine_network_ortho(node_dict, ortho_data):
    """Pulls the orthology data from the proteins in the network list and combines ortho data with network data
    
    :param node_list: list of gene ids from nodes in the JSON network
    :param ortho_data: list of Orthogroups objects"""
    # dictionary will hold the potential matches for uniprot ids based on node ids
    matched_groups = {}

    ortho_lookup = {y:x for x in ortho_data for y in x.group}

    for gene in node_dict:
        if gene in ortho_lookup is not None:
            # add set with gene removed to the matched_groups dict
            matched_groups[gene] = ortho_lookup[gene].find_protein(gene)

    return matched_groups

def query_orthology_data(species1, species2):
    """Compiles a list of Orthogroups objects for eventually receiving all of the orthology data within the network.
    
    :param species1: name of species 1 as str
    :param species2: name of species 2 as str
    :return: list of Orthogroups objects"""
    # TODO: Change this so that file that opens reflects species passed by parameter
    filepath = "../../../PPI-Network-Alignment/orthology-data/orthogroups/c_elegans-s_cerevisiae_orthogroups.txt"

    # list of orthogroup objects
    orthogroups = []
    with open(filepath, 'r') as file:
        for line in file:
            if line[0] == '!':
                file.readline()
            else: 
                group = line.strip().split("\t")
                orthogroups.append(Orthogroups.Orthogroups(group))

    return orthogroups

def query_subnetwork(p_dict_s1, prot_s1, p_dict_s2, prot_s2, protList_s1, protList_s2, s1, s2):
    """
    Takes in a query protein and query species and returns a subnetwork in JSON format

    :param p_dict_s1: dictionary of proteins and their connections as def list for species 1
    :param prot_s1: desired protein as str for species 1
    :param p_dict_s2: dictionary of proteins and their connections as def list for species 2
    :param prot_s2: desired protein as str for species 2
    :param protList_s1: list of proteins as dict (from extract_ensembl functions)
    :param protList_s2: list of proteins as dict (from extract_ensembl functions)
    :param s1: str species 1 name
    :param s2: str species 2 name
    :return: list of dict values that corresponds with the desired subnetwork
    """
    try:
        prot_def1 = p_dict_s1[prot_s1]

    except Exception as exc:
        raise ValueError("Protein 1 does not exist in the network--input a different protein!") from exc
    
    try:
        prot_def2 = p_dict_s2[prot_s2]
    except Exception as exc:
        raise ValueError("Protein 2 does not exist in the network--input a different protein!")
    
    else:

        # add the query protein to the list of its interacting proteins
        temp1 = prot_def1
        temp1.append(prot_s1)

        temp2 = prot_def2
        temp2.append(prot_s2)

        retList1 = list_to_nodes(temp1, protList_s1, 1)
        nodes1 = retList1[0]  # protein nodes to become JSON
        edge_dict1 = retList1[1]  # dict of protein name as key and corresponding id as def

        retList2 = list_to_nodes(temp2, protList_s2, 2)
        nodes2 = retList2[0]  # protein nodes to become JSON
        edge_dict2 = retList2[1]  # dict of protein name as key and corresponding id as def

        edges1 = list_to_edges(prot_s1, prot_def1, edge_dict1)
        edges2 = list_to_edges(prot_s2, prot_def2, edge_dict2)

        json_header = [
                    {"data":
                        {"id": "species1", "name": s1},
                            "_comment": "Test output for a JSON file -- contains a subnetwork of C. elegans and a subnetwork of M. musculus",
                            "classes": "container s1"},
                    {"data": {"id": "species2", "name": s2}, "classes": "container s2"}]

        # add all lists of dict objects together to form the whole JSON file
        json_header.extend(nodes1)
        json_header.extend(edges1)
        json_header.extend(nodes2)
        json_header.extend(edges2)
        json_str = json.dumps(json_header)

        file = open("test_json.json", "w")
        file.write(json_str)

        return json.loads(json_str)

def list_to_nodes(p_inters, ensembl_data, species_num):
    """
    Converts python dictionary to JSON format with established conventions.
    Writes to a JSON file, returns nothing.

    :param p_inters: dictionary of proteins and their connections as def list
    :param ensembl_data: dict of alternate ids from ensembl file
    :param species_num: species 1 or 2?
    :return: final list of JSON elements without edges, dict of edge ids and e_ids
    """
    # take a dictionary with the entrezgene as the key
    #d = {x.get_p_sid(): x for x in ensembl_data}

    # the list that will be ultimately converted to JSON
    # start with comment and protein category boxes
    final_list = []

    # dictionary that will hold node ids and edges
    edge_dict = {}

    count = 0
    for key in p_inters:
        json_dict = {"data": {}}
        json_dict["data"]["id"] = str(species_num) + "." + str(count)
        for i in range(6):
            if not ensembl_data[key][i] or '' in ensembl_data[key][i]:
                ensembl_data[key][i] = {}

        json_dict["data"]["e_id"] = key
        json_dict["data"]["t_id"] = ensembl_data[key][0]
        json_dict["data"]["p_id"] = ensembl_data[key][1]
        json_dict["data"]["name"] = ensembl_data[key][2]
        json_dict["data"]["ncbi"] = ensembl_data[key][3]
        json_dict["data"]["swissprot"] = ensembl_data[key][4]
        json_dict["data"]["trembl"] = ensembl_data[key][5]
        json_dict["data"]["refseq"] = ensembl_data[key][6]
        json_dict["data"]["parent"] = "species" + str(species_num)

        json_dict["classes"] = "species" + str(species_num) + " protein"

        # if there is not a name, make the name the ensembl id
        if len(json_dict['data']['name']) == 0:
            json_dict['data']['name'] = json_dict['data']['e_id']

        # add data to edge dictionary
        edge_dict[key] = json_dict["data"]["id"]

        final_list.append(json_dict)

        count += 1

    # the last entry in the dict will be the query
    json_dict["classes"] = json_dict["classes"] + " query"

    return [final_list, edge_dict]

def list_to_edges(prot, e_list, e_dict):
    """
    Takes the converted nodes and writes edges to JSON based on established conventions
    and data in the established python dictionary

    :param prot: dictionary of each protein in the network and their connections
    :param e_list: list of edges within the network?
    :param edge_dict: dictionary of id and its corresponding ensembl id
    :return: list of JSON edges
    """

    # final list of JSON edges to be returned
    final_list = []

    temp = {}

    # remove the query protein if in list
    e_list.remove(prot)

    # loop through p_dict
    for ele in e_list:
        temp = {"data": {}}

        # set the source to the current protein
        temp["data"]["source"] = e_dict[prot]

        # set the target to the interacting protein
        temp["data"]["target"] = e_dict[ele]

        temp["classes"] = "species" + str(e_dict[prot][0]) + " edge"

        #print(temp)

        # add to the final list
        final_list.append(temp)

    return final_list

def list_to_dict(map_list):
    """
    Constructs a dictionary with a list of each protein it interacts with
    as def

    :param map_list: list of mapped protein ids
    :return: dict of each protein id and it's interactors
    """

    prot_hash = {}
    for interaction in map_list:
        current = 0
        for prot in interaction:
            # check if the protein already exists in the dictionary
            if prot not in prot_hash:
                prot_hash[prot] = []    # create a new list if not in dict

            prot2 = interaction[current - 1]    # receive interacting protein (either 0 or -1)

            # check if the interacting protein is already in the current def list
            # and also not in the dict already so that there aren't duplicate interactions
            if prot2 not in prot_hash[prot]:
                # add the interacting protein to the list of interactors for the current
                prot_hash[prot].append(interaction[current - 1])

            current += 1

    return prot_hash

def read_network_file(filename):
    """
    Takes in a filepath for a network file from PPI-Network-Alignment and stores data as a dict
    :param filename: filepath as str
    :return: list of tuple interaction pairs
    """
    network_data = []
    with open(filename, "r") as f:
        for line in f:
            if line[0] != "!" and line[0] != "\n":
                interaction = line.strip().split('\t')
                network_data.append(tuple(interaction))

    return network_data

def read_data(file_name):
    """
        read_data(): takes in a file name as param and reads the ensembl file

        :param file_name: filename as str
        :return: contents of the file as list
    """
    contents = []
    with open(file_name) as f:
        f.readline()
        for line in f:
            contents.append(line.strip().split('\t'))

    return contents

def read_json(file_path):
    """
    Takes in a file path as param and reads a current json file
    :param file_path: str file path
    :return: json file contents as dict
    """
    with open(file_path) as file:
        data = json.load(file)

    for i in range(len(data)):
        # do not consider container nodes
        if data[i]['classes'] == 'container':
            break

        if 'id' in data[i]['data']:
            current = data[i]['data']['name']
            current = current.split(",")

            for j in range(len(current)):
                current[j] = current[j].strip()

            data[i]['data']['name'] = current

        #print(data)
        #print(data[1])
        #print(data[1]['data'])
        #print(data[1]['data']['name'])
        #print(data[4]['data']['name'].split(','))

    return data

def extract_ensembl_data_ncbi(filename):
    """
    Takes the data from the ensembl file with the ncbi id and initializes the dictionary with ids
    with the gene stable id as the key
    :param content: ensembl data as list
    :return: dict ensembl data
    """
    with open(filename, 'r') as content:
        content.readline()
        gene_dict = {}

        # loop through the content
        for line in content:
          line = line.strip().split('\t')

          current_gene_id = line[0]
          line.pop(0)

          while len(line) < 7:
              line.append("")

          if current_gene_id in gene_dict:
              for i in range(len(line)):
                  current_id = line[i]
                  
                  current_list = gene_dict[current_gene_id][i]  # list associated with each id type
                  if current_id not in current_list and current_id != "":    # checks for duplicates
                    gene_dict[current_gene_id][i].append(current_id)
                
          else:
              # key is the gene stable id because every line in the file will have one ('primary key')
              gene_dict[current_gene_id] = []

              for ele in line:
                if ele != "":
                    gene_dict[current_gene_id].append([ele])
                else:
                    gene_dict[current_gene_id].append([])

    return gene_dict

def extract_ensembl_data_other_ids(filename, ensembl_dict):
    """
    Takes the data from the ensembl file with the other ids (swissprot, trembl, refseq)
    and appends to the list of other ids if it already exists in the dict, otherwise adds a new
    key/def for any new id entries
    :param filename: filepath for the other id file
    :param ensembl_dict: dict with ensembl data that has already been created
    :return: updated dict with ensembl data
    """
    with open(filename, 'r') as content:
      content.readline()
      for line in content:
        line = line.strip().split('\t')
        
        # assigning variables for better readability
        current_gene_id = line[0]

        line.pop(0)     # remove the current gene id from the line for better transition
        line.insert(3, "")   # insert an empty space for ncbi id

        while len(line) < 7:
            line.append("")

        if current_gene_id in ensembl_dict:
            for i in range(len(line)):
                current_id = line[i]
                current_list = ensembl_dict[current_gene_id][i]  # list associated with each id type

                if current_id not in current_list and current_id != "":    # checks for duplicates
                    ensembl_dict[current_gene_id][i].append(current_id)

        else:
            # key is the gene stable id because every line in the file will have one ('primary key')
            gene_dict[current_gene_id] = []

            for ele in line:
                if ele != "":
                    gene_dict[current_gene_id].append([ele])
                else:
                    gene_dict[current_gene_id].append([])

    return ensembl_dict

def match_name(name, dict):
    """
    Matches the name from a json file with the corresponding id info from the ensembl file
    Returns the list of ids associated with the protein name
    :param name: Key from json dict
    :param dict: ensembl dictionary
    :return: list of ids associated with the given protein name
    """
    # list of names to be returned
    id_list = []

    if name.lower() in dict:
        id_list = dict[name.lower()]
    elif name.upper() in dict:
        id_list = dict[name.upper()]
    else:
        id_list = None

    return id_list

'''
AAA-1, 848483, Q93783, ENSG3883839393
www.ncbi.nih.gov/gene/848483
www.uniprot.com/Q37383
www.ensemble.org/?q=ENSG108839393939

'''

def update_json(json, dict, filename):
    """
    Take in the json file info and dict with protein data and write data to a given file
    Loop through json file and add the dict data when necessary
    :param json: json dict
    :param dict: ensembl dict
    :param filename: name of file to be written to
    :return: None
    """
    temp = []

    original_stdout = sys.stdout
    with open(filename, 'w') as f:
        sys.stdout = f

        print("[")

        # loop through the json file
        for i in range(len(json)):
            # check if the data has element "name"
            if 'name' in json[i]['data']:
                name_list = json[i]['data']['name']
            else:
                print(str(json[i]).replace("'", '"'), ",", sep="")
                continue # might want a diff approach????

                # name_list remains the same after the name does not change
                # i.e. the line is an edge and therefore does not have a name
                # will continue to print the info for the last node along with the
                # edge print statement

            # pull the name from the line
            for name in name_list:
                is_matched = match_name(name, dict)
                if is_matched is not None:
                    temp = temp + match_name(name, dict)

            # boolean value that keeps track of whether there are
            # multiple proteins to a node
            mult = False
            if temp != []:
                if len(name_list) > 1:
                    mult = True

                print('{ "data":', end='')
                if 'id' in json[i]['data']:
                    print(' { "id": "' + json[i]['data']['id'] + '",', end='')

                print(' "e_id": "' + temp[0] + '",', end='')
                if mult:
                    print(' "e_id2": "' + temp[4] + '",', end='')
                print(' "name": "' + ", ".join(name_list) + '",', end='')

                # not all elements will have a parent
                if 'parent' in json[i]['data']:
                    print(' "parent": "' + json[i]['data']['parent'] + '",', end='')

                print(' "ncbi": "' + temp[1] + '",', end='')
                if mult:
                    print(' "ncbi2": "' + temp[5] + '",', end='')

                if temp[2] != "":
                    print(' "uniprot": "' + temp[2] + '"', end='')
                elif temp[3] != "":
                    print(' "uniprot": "' + temp[3] + '"', end='')

                if mult:
                    if temp[6] != "":
                        print(', "uniprot2": "' + temp[6] + '"', end='')
                    elif temp[7] != "":
                        print(', "uniprot2": "' + temp[7] + '"', end='')
                print("}", end='')

                if "classes" in json[i]:
                    print(', "classes": "' + json[i]['classes'] + '"}', end='')

            else:
                print(str(json[i]).replace("'", '"'), end='')

            # only have a comma if the current line is not the last one
            if i != len(json)-1:
                print(",")

            temp = []

        print("]")

        sys.stdout = original_stdout

main()