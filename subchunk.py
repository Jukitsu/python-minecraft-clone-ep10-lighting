import models.cube
import models.cactus

SUBCHUNK_WIDTH = 4
SUBCHUNK_HEIGHT = 4
SUBCHUNK_LENGTH = 4


class Subchunk:
    def __init__(self, parent, subchunk_position):
        self.parent = parent
        self.world = self.parent.world

        self.subchunk_position = subchunk_position

        self.local_position = (
            self.subchunk_position[0] * SUBCHUNK_WIDTH,
            self.subchunk_position[1] * SUBCHUNK_HEIGHT,
            self.subchunk_position[2] * SUBCHUNK_LENGTH)

        self.position = (
            self.parent.position[0] + self.local_position[0],
            self.parent.position[1] + self.local_position[1],
            self.parent.position[2] + self.local_position[2])

        # mesh variables

        self.mesh_vertex_positions = []
        self.mesh_tex_coords = []
        self.mesh_shading_values = []

        self.mesh_index_counter = 0
        self.mesh_indices = []

    def update_mesh(self):
        self.mesh_vertex_positions = []
        self.mesh_tex_coords = []
        self.mesh_shading_values = []

        self.mesh_index_counter = 0
        self.mesh_indices = []

        def add_face(self, face=None, light_levels=None):
            vertex_positions = block_type.vertex_positions[face].copy()

            for i in range(4):
                vertex_positions[i * 3 + 0] += x
                vertex_positions[i * 3 + 1] += y
                vertex_positions[i * 3 + 2] += z

            self.mesh_vertex_positions.extend(vertex_positions)

            indices = [0, 1, 2, 0, 2, 3]
            for i in range(6):
                indices[i] += self.mesh_index_counter

            self.mesh_indices.extend(indices)
            self.mesh_index_counter += 4

            self.mesh_tex_coords.extend(block_type.tex_coords[face])
            if block_type.is_cube:
                shading_values = models.cube.get_face_shading_values(light_levels[face], face)
            else:
                shading_values = block_type.shading_values[face]
            self.mesh_shading_values.extend(shading_values)

        for local_x in range(SUBCHUNK_WIDTH):
            for local_y in range(SUBCHUNK_HEIGHT):
                for local_z in range(SUBCHUNK_LENGTH):
                    parent_lx = self.local_position[0] + local_x
                    parent_ly = self.local_position[1] + local_y
                    parent_lz = self.local_position[2] + local_z

                    block_number = self.parent.blocks[parent_lx][parent_ly][parent_lz]

                    if block_number:
                        if block_number in self.world.light_blocks:
                            self.world.create_light(parent_lx, parent_ly, parent_lz, 15)
                        block_type = self.world.block_types[block_number]

                        x, y, z = (
                            self.position[0] + local_x,
                            self.position[1] + local_y,
                            self.position[2] + local_z)

                        light_levels = list([self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 0),
                                                          self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 1),
                                                          self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 2),
                                                          self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 3),
                                                          self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 4),
                                                          self.parent.getfacelight(parent_lx, parent_ly, parent_lz, 5)])

                        # if block is cube, we want it to check neighbouring blocks so that we don't uselessly render faces
                        # if block isn't a cube, we just want to render all faces, regardless of neighbouring blocks
                        # since the vast majority of blocks are probably anyway going to be cubes, this won't impact performance all that much; the amount of useless faces drawn is going to be minimal

                        if block_type.is_cube:
                            if not self.world.is_opaque_block((x + 1, y, z)): add_face(self, 0, light_levels)
                            if not self.world.is_opaque_block((x - 1, y, z)): add_face(self, 1, light_levels)
                            if not self.world.is_opaque_block((x, y + 1, z)): add_face(self, 2, light_levels)
                            if not self.world.is_opaque_block((x, y - 1, z)): add_face(self, 3, light_levels)
                            if not self.world.is_opaque_block((x, y, z + 1)): add_face(self, 4, light_levels)
                            if not self.world.is_opaque_block((x, y, z - 1)): add_face(self, 5, light_levels)

                        else:
                            for i in range(len(block_type.vertex_positions)):
                                add_face(self, i)
