import torch as th
import dgl

from utils import igmc_subgraph_extraction_labeling, one_hot

class MovieLensDataset(th.utils.data.Dataset):
    def __init__(self, links, g_labels, graph, 
                hop=1, sample_ratio=1.0, max_nodes_per_hop=200):
        self.links = links
        self.g_labels = g_labels
        self.graph = graph 

        self.hop = hop
        self.sample_ratio = sample_ratio
        self.max_nodes_per_hop = max_nodes_per_hop

    def __len__(self):
        return len(self.links[0])

    def __getitem__(self, idx):
        u, v = self.links[0][idx], self.links[1][idx]
        g_label = self.g_labels[idx]

        subgraph = igmc_subgraph_extraction_labeling(
            self.graph, (u, v), h=self.hop, 
            sample_ratio=self.sample_ratio, max_nodes_per_hop=self.max_nodes_per_hop)
        
        subgraph.ndata['nlabel'] = one_hot(subgraph.ndata['nlabel'], (self.hop+1)*2)
        
        # set edge mask to zero as to remove edges between target nodes in training process
        subgraph.edata['edge_mask'] = th.ones(subgraph.number_of_edges())
        su = subgraph.nodes()[subgraph.ndata[dgl.NID]==u]
        sv = subgraph.nodes()[subgraph.ndata[dgl.NID]==v]
        _, _, target_edges = subgraph.edge_ids([su, sv], [sv, su], return_uv=True)
        subgraph.edata['edge_mask'][target_edges] = 0
        
        return subgraph, g_label

def collate_movielens(data):
    g_list, label_list = map(list, zip(*data))
    g = dgl.batch(g_list)
    g_label = th.stack(label_list)
    return g, g_label