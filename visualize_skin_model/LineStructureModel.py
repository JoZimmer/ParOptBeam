import json
import numpy as np
from NodeModel import Node

class LineStructure:
    def __init__(self, structure_file):
        """
        intializing line structure with eigenform
        """
        self.nodes = []
        self.x_vec, self.y_vec, self.z_vec = [],[],[] 
        with open(structure_file) as json_file:
            data = json.load(json_file)
            self.num_of_dofs_per_node = data["num_of_dofs_per_node"]
            self.node_positions = data["node_positions"]
            self.dofs = data["dofs"]
            self.num_of_nodes = int(len(self.dofs)/self.num_of_dofs_per_node)
            self.structure_height = data["height"]
        self.print_line_structure_info()
        self.init_nodes()
        self.init_dofs()

    def init_nodes(self):
        for i in range(self.num_of_nodes):
            x = self.node_positions[int(i*3  )]
            y = self.node_positions[int(i*3+1)]
            z = self.node_positions[int(i*3+2)]
            node = Node(x, y, z)
            self.nodes.append(node)
            self.x_vec.append(node.x0)
            self.y_vec.append(node.y0)
            self.z_vec.append(node.z0)

    def init_dofs(self):
        for i in range(self.num_of_nodes):
            dx = self.dofs[int(i*self.num_of_dofs_per_node  )]
            dy = self.dofs[int(i*self.num_of_dofs_per_node+1)]
            dz = self.dofs[int(i*self.num_of_dofs_per_node+2)]
            theta_x = self.dofs[int(i*self.num_of_dofs_per_node  )]
            theta_y = self.dofs[int(i*self.num_of_dofs_per_node+1)]
            theta_z = self.dofs[int(i*self.num_of_dofs_per_node+2)]
            self.nodes[i].add_dofs(dx, dy, dz, theta_x, theta_y, theta_z)  
            #self.nodes[i].print_info()   

    def print_line_structure_info(self):    
        msg = "=============================================\n"
        msg += "LINE STRUCTURE MODEL INFO \n"
        msg += "NUMBER OF NODES:\t" + str(self.num_of_nodes) + "\n"
        msg += "============================================="
        print(msg)

    def print_nodal_infos(self):
        for node in self.nodes:
            node.print_info()

    def apply_rotation_for_line_structure(self):
        # rotation matrix around axis x
        Rx = np.matrix([[1,     0,                  0              ],
                        [0,     cos(self.theta_x), -sin(self.theta_x)],
                        [0,     sin(self.theta_x),  cos(self.theta_x) ]])

        # rotation matrix around axis y
        Ry = np.matrix([[cos(self.theta_y),   0,    sin(self.theta_y)],
                        [0,                 1,    0              ],
                        [-sin(self.theta_y),  0,    cos(self.theta_y)]])

        # rotation matrix around axis z
        Rz = np.matrix([[cos(self.theta_z), -sin(self.theta_z),  0],
                        [sin(self.theta_z), cos(self.theta_z),   0],
                        [0,                 0,                   1]])

        previous_coordinate = np.matrix([[x0],[y0],[z0]])
        new_coordinate = (Ry*Rx)*previous_coordinate
        self.x = float(new_coordinate[0][0])
        self.y = float(new_coordinate[1][0])
        self.z = float(new_coordinate[2][0])
