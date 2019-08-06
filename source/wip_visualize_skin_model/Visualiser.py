import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
import numpy as np
from source.wip_visualize_skin_model.Mapper import Mapper
from matplotlib import animation

plt.rcParams['legend.fontsize'] = 16


class Arrow3D(FancyArrowPatch):
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        FancyArrowPatch.draw(self, renderer)


class Visualiser:
    def __init__(self, line_structure, structure=None):
        self.line_structure = line_structure
        if structure is not None:
            self.structure = structure
        self.mapper = Mapper(structure, line_structure)
        self.interpolated_line_structure = self.mapper.interpolated_line_structure
        self.factor = 150.

        self.fig = plt.figure(figsize=(10, 10))
        # self.ax = Axes3D(self.fig)
        self.ax = self.fig.add_subplot(111, projection='3d', aspect='equal', azim=-60, elev=10)
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')
        self.set_coordinate_in_real_size()
        self.visualize_coordinate()

        self.mapper.map_interpolated_line_structure_to_structure_floor()
        self.line_structure.apply_transformation_for_line_structure()
        self.interpolated_line_structure.apply_transformation_for_line_structure()
        self.structure.apply_transformation_for_structure()

        self.animate()

    def visualize_coordinate(self):
        arrow_prop_dict = dict(mutation_scale=20, arrowstyle='->', shrinkA=0, shrinkB=0)
        a = Arrow3D([0, 10], [0, 0], [0, 0], **arrow_prop_dict, color='r')
        self.ax.add_artist(a)
        a = Arrow3D([0, 0], [0, 10], [0, 0], **arrow_prop_dict, color='b')
        self.ax.add_artist(a)
        a = Arrow3D([0, 0], [0, 0], [0, 10], **arrow_prop_dict, color='g')
        self.ax.add_artist(a)

        self.ax.text(0.0, 0.0, -1, r'$o$')
        self.ax.text(11, 0, 0, r'$x$')
        self.ax.text(0, 11, 0, r'$y$')
        self.ax.text(0, 0, 11, r'$z$')

    def set_coordinate_in_real_size(self):
        X, Y, Z = [], [], []
        for frame in self.structure.frames:
            X += frame.x_vec
            Y += frame.y_vec
            Z += frame.z_vec

        mid_x = (max(X) + min(X)) * 0.5
        mid_y = (max(Y) + min(Y)) * 0.5
        mid_z = (max(Z) + min(Z)) * 0.5
        max_range = np.array([max(X) - min(X), max(Y) - min(Y), max(Z) - min(Z)]).max() / 2.0
        self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
        self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
        self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
        self.visualize_coordinate()

    def visualise_line_structure(self):
        x_vec = self.line_structure.x0_vec + np.subtract(self.line_structure.x_vec, self.line_structure.x0_vec) * self.scale
        y_vec = self.line_structure.y0_vec + np.subtract(self.line_structure.y_vec, self.line_structure.y0_vec) * self.scale
        z_vec = self.line_structure.z0_vec + np.subtract(self.line_structure.z_vec, self.line_structure.z0_vec) * self.scale

        z = np.array([z_vec, z_vec])
        self.ax.plot_wireframe(x_vec, y_vec, z, color='b', linewidth=3)
        for node in self.line_structure.nodes:
            x = node.x0 + (node.x - node.x0) * self.scale
            y = node.y0 + (node.y - node.y0) * self.scale
            z = node.z0 + (node.z - node.z0) * self.scale
            self.ax.scatter(x, y, z, marker='o', c='r', s=50)

    def visualise_interpolated_line_structure(self):
        x_vec = self.interpolated_line_structure.x0_vec + np.subtract(self.interpolated_line_structure.x_vec, self.interpolated_line_structure.x0_vec) * self.scale
        y_vec = self.interpolated_line_structure.y0_vec + np.subtract(self.interpolated_line_structure.y_vec, self.interpolated_line_structure.y0_vec) * self.scale
        z_vec = self.interpolated_line_structure.z0_vec + np.subtract(self.interpolated_line_structure.z_vec, self.interpolated_line_structure.z0_vec) * self.scale

        z = np.array([z_vec, z_vec])
        self.ax.plot_wireframe(x_vec, y_vec, z,
                               color='g', linewidth=3, linestyle='--')
        # for node in self.interpolated_line_structure.nodes:
        # self.ax.scatter(node.x, node.y, node.z, marker='o', c='g', s = 50)

    def visualise_structure(self):
        self.visualise_element()
        self.visualize_frame()

    def visualise_element(self):
        for element in self.structure.elements:
            x_vec = element.x0_vec + np.subtract(element.x_vec, element.x0_vec) * self.scale
            y_vec = element.y0_vec + np.subtract(element.y_vec, element.y0_vec) * self.scale
            z_vec = element.z0_vec + np.subtract(element.z_vec, element.z0_vec) * self.scale

            x_vec = np.append(x_vec, x_vec[0])
            y_vec = np.append(y_vec, y_vec[0])
            z_vec = np.append(z_vec, z_vec[0])

            z = np.array([z_vec, z_vec])

            self.ax.plot_wireframe(x_vec, y_vec, z, color='black')

    def visualize_frame(self):
        for frame in self.structure.frames:
            x_vec = frame.x0_vec + np.subtract(frame.x_vec, frame.x0_vec) * self.scale
            y_vec = frame.y0_vec + np.subtract(frame.y_vec, frame.y0_vec) * self.scale
            z_vec = frame.z0_vec + np.subtract(frame.z_vec, frame.z0_vec) * self.scale

            z = np.array([z_vec, z_vec])
            self.ax.plot_wireframe(x_vec, y_vec, z, color='black')

    def animate(self):
        # Set up formatting for the movie files
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
        a = animation.FuncAnimation(self.fig, self.update, 40, repeat=False)
        # a.save("structure_displacement.mp4")
        plt.tight_layout()
        plt.show()

    def update(self, t):
        """
        plotting the deformed structure with respect to the displacement
        """
        wframe = self.fig.gca()
        if wframe is not None:
            self.ax.cla()
        self.scale = self.factor * np.sin(t)
        self.visualise_structure()
        # self.visualise_line_structure()
        # self.visualise_interpolated_line_structure()
        self.set_coordinate_in_real_size()


