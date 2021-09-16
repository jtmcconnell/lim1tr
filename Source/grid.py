########################################################################################
#                                                                                      #
#  Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC (NTESS).  #
#  Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains    #
#  certain rights in this software.                                                    #
#                                                                                      #
#  This software is released under the license detailed in the file, LICENSE.          #
#                                                                                      #
########################################################################################

from __future__ import division
import numpy as np


class grid_manager:
    def set_table(self, tab_dict):
        '''Sets the table from the parser.
        '''
        self.layer_names = tab_dict['Material Name']
        self.layer_dx = tab_dict['dx']
        self.layer_thickness = tab_dict['Thickness']


    def setup_grid(self):
        '''Sets up the grid.
        '''
        self.n_layers = len(self.layer_names)

        # Loop through material layers
        self.n_tot = 0
        mat_nodes = []
        nodes_per_layer = []
        self.mint_list = []
        self.first_node_list = []
        dx_list = []
        for i in range(self.n_layers):
            if self.layer_thickness[i] < self.layer_dx[i]:
                err_str = 'Requested dx on layer {} is greater than the thickness.'.format(i+1)
                raise ValueError(err_str)

            # Save first node index
            self.first_node_list.append(self.n_tot)

            # Calculate number of nodes
            n_m = int(np.round(self.layer_thickness[i]/self.layer_dx[i],0))
            nodes_per_layer.append(n_m)

            # Total up nodes
            self.n_tot += n_m

            # Acutal dx
            dx_m = self.layer_thickness[i]/n_m
            dx_list.append(dx_m)

            # Material type list
            mat_nodes += n_m*[str(self.layer_names[i])]

            # Save node number on the left of each interface (includes right domain bc)
            self.mint_list.append(self.n_tot - 1)

        # Check for single node layers
        single_node_layers = []
        if self.n_layers > 1:
            for i in range(self.n_layers):
                if nodes_per_layer[i] <= 1:
                    single_node_layers.append(i)
        if len(single_node_layers) > 0:
            err_str = 'Only 1 control volume on layer(s) {}!\n'.format(single_node_layers)
            err_str += 'Minimum of 2 control volumes required for conduction problems.'
            raise ValueError(err_str)

        # Recast list of material types as an array
        self.mat_nodes = np.asarray(mat_nodes)

        # Build dx array at each node
        self.dx_arr = np.zeros(self.n_tot)
        m = 0
        for i in range(self.n_tot):
            self.dx_arr[i] = dx_list[m]
            if i == self.mint_list[m]:
                m += 1

        # Build bounds lists
        self.internal_bounds = [[1, self.mint_list[0]]]
        self.k_bounds = [[0, self.mint_list[0]]]
        for m in range(1, self.n_layers):
            self.internal_bounds.append([self.mint_list[m-1]+2, self.mint_list[m]])
            self.k_bounds.append([self.mint_list[m-1]+1, self.mint_list[m]])

        # Build node locations
        self.x_node = np.zeros(self.n_tot)
        for i in range(self.n_tot):
            self.x_node[i] = 0.5*self.dx_arr[i] + np.sum(self.dx_arr[:i])


    def set_PA_r(self, oth_dict):
        '''Calculate the perimeter to cross-sectional area ratio.
        '''
        L_y = oth_dict['Y Dimension']
        L_z = oth_dict['Z Dimension']
        self.PA_r = 2.*(L_y + L_z)/(L_y*L_z)
