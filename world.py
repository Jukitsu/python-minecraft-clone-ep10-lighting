import math

import chunk
import subchunk
import block_type
import texture_manager
import random

from vector import Vec3D
from collections import deque

# import custom block models

import models.plant
import models.cactus
import models.cube

light_threads = []

RENDERDISTANCE = 2
WORLDSIZE = 2
max_light_level = models.cube.max_light_level

default_sky_light = 15

class Queue:
    def __init__(self):
        self.queue = list()

    def put(self, item):
        self.queue.append(item)

    def get(self):
        if not self.empty():
            return self.queue.pop(0)

    def qsize(self):
        return len(self.queue)

    def empty(self):
        return not self.qsize()

class BFSLightNode:
    def __init__(self, x, y, z, _chunk, light):
        self.x = x
        self.y = y
        self.z = z
        self._chunk = _chunk
        self.light = light


class BFSLightRemovalNode:
    def __init__(self, x, y, z, _chunk, val):
        self.x = x
        self.y = y
        self.z = z
        self._chunk = _chunk
        self.val = val


class LightUpdateNode:
    def __init__(self, newchunk, localposition):
        self.newchunk = newchunk
        clx, cly, clz = localposition
        self.position = (math.floor(clx / subchunk.SUBCHUNK_WIDTH),
                         math.floor(cly / subchunk.SUBCHUNK_HEIGHT),
                         math.floor(clz / subchunk.SUBCHUNK_LENGTH))


lightBfsQueue = Queue()
removeBfsQueue = Queue()
skylightBfsQueue = Queue()


class World:
    def __init__(self):
        self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
        self.block_types = [None]

        self.block_types.append(block_type.Block_type(self.texture_manager, "cobblestone", {"all": "cobblestone"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "grass",
                                                      {"top": "grass", "bottom": "dirt", "sides": "grass_side"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "grass_block", {"all": "grass"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "dirt", {"all": "dirt"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "stone", {"all": "stone"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "sand", {"all": "sand"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "planks", {"all": "planks"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "log",
                                                      {"top": "log_top", "bottom": "log_top", "sides": "log_side"}))
        self.block_types.append(block_type.Block_type(self.texture_manager, "daisy", {"all": "daisy"}, models.plant))
        self.block_types.append(block_type.Block_type(self.texture_manager, "rose", {"all": "rose"}, models.plant))
        self.block_types.append(block_type.Block_type(self.texture_manager, "cactus",
                                                      {"top": "cactus_top", "bottom": "cactus_bottom",
                                                       "sides": "cactus_side"}, models.cactus))
        self.block_types.append(
            block_type.Block_type(self.texture_manager, "dead_bush", {"all": "dead_bush"}, models.plant))
        self.block_types.append(block_type.Block_type(self.texture_manager, "torch", {"all": "torch_on"}, models.plant))
        self.block_types.append(block_type.Block_type(self.texture_manager, "glowstone", {"all": "glowstone"}))

        self.texture_manager.generate_mipmaps()

        self.chunks = {}
        self.lightupdatequeue = Queue()

        self.light_blocks = [13, 14]
        self.placed_light_blocks = {}
        # print("Initializing Light Map")

        for x in range(RENDERDISTANCE):
            for z in range(RENDERDISTANCE):
                chunk_position = (x - 1, -1, z - 1)
                current_chunk = chunk.Chunk(self, chunk_position)

                for i in range(chunk.CHUNK_WIDTH):
                    for j in range(chunk.CHUNK_HEIGHT):
                        for k in range(chunk.CHUNK_LENGTH):
                            if j == 13:
                                current_chunk.blocks[i][j][k] = random.choices([0, 9, 10], [20, 2, 1])[0]
                            elif j == 12:
                                current_chunk.blocks[i][j][k] = 2
                            elif 9 < j < 12:
                                current_chunk.blocks[i][j][k] = 4
                            elif j < 10:
                                current_chunk.blocks[i][j][k] = 5
                self.chunks[chunk_position] = current_chunk

        for rx in range(RENDERDISTANCE):
            for rz in range(RENDERDISTANCE):
                for i in range(chunk.CHUNK_WIDTH):
                    for j in range(chunk.CHUNK_HEIGHT):
                        for k in range(chunk.CHUNK_LENGTH):
                            cx, cy, cz = (rx - 1, -1, rz - 1)
                            x, y, z = cx + i, cy + j, cz + k
                            if j > 13:
                                self.create_skylight(x, y, z, 15)

        for chunk_position in self.chunks.keys():
            self.chunks[chunk_position].update_subchunk_meshes()
            self.chunks[chunk_position].update_mesh()

    # create functions to make things a bit easier

    def create_skylight(self, x, y, z, light):  # Currently Broken
        if 1: return
        lpos = self.get_local_position((x, y, z))
        _chunk = self.chunks.get(self.get_chunk_position((x, y, z)), None)
        if _chunk is None:
            _chunk = chunk.Chunk(self, self.get_chunk_position((x, y, z)))
            self.chunks[self.get_chunk_position((x, y, z))] = _chunk
        skylightBfsQueue.put(BFSLightNode(*lpos, _chunk, light))
        _chunk.set_block_light(*lpos, light)
        while not skylightBfsQueue.empty():
            node = skylightBfsQueue.get()
            blockchunk = node._chunk
            nx, ny, nz = node.x, node.y, node.z
            current_skylight = node.light
            for face in range(0, 6):
                if face == 2:
                    continue
                fx, fy, fz = self.get_direction_vector(face)
                mpos = (nx + fx, ny + fy, nz + fz)
                cpos = self.interchunk(*mpos, blockchunk)
                if cpos not in self.chunks.keys():
                    newchunk = chunk.Chunk(self, cpos)
                    self.chunks[cpos] = newchunk
                else:
                    newchunk = self.chunks[cpos]
                pos = self.get_local_position(mpos)
                if not newchunk.is_opaque_block(pos) and newchunk.get_sky_light(*pos) + 2 <= current_skylight:
                    newchunk.set_sky_light(*pos, current_skylight - 1)
                    skylightBfsQueue.put(BFSLightNode(*pos, newchunk, current_skylight - 1))

    def remove_skylight(self, x, y, z, ignore=[]):
        if 1: return
        if self.is_opaque_block((x, y, z)):
            self.set_sky_light(x, y, z, 0)
            return
        self.set_sky_light(x, y, z, 0)
        if (x, y, z) in ignore:
            return
        for face in range(0, 6):
            vector = self.get_direction_vector(face)
            pos = (x + vector[0], y + vector[1], z + vector[2])
            l = 0
            if self.is_opaque_block(pos) or pos in ignore or self.get_sky_light(*pos) >= l:
                continue
            ignore += [(x, y, z)]
            self.remove_skylight(*pos, l - 1, ignore)

    def create_light(self, x, y, z, light, newchunks=True):
        lpos = self.get_local_position((x, y, z))
        _chunk = self.chunks.get(self.get_chunk_position((x, y, z)), None)
        if _chunk is None:
            if not newchunks:
                return
            _chunk = chunk.Chunk(self, self.get_chunk_position((x, y, z)))
            self.chunks[self.get_chunk_position((x, y, z))] = _chunk
        lightBfsQueue.put(BFSLightNode(*lpos, _chunk, light))
        _chunk.set_block_light(*lpos, light)
        while not lightBfsQueue.empty():
            node = lightBfsQueue.get()
            blockchunk = node._chunk
            nx, ny, nz = node.x, node.y, node.z
            nvec = Vec3D(nx, ny, nz)
            current_light = node.light
            for face in range(0, 6):
                fvec = self.get_direction_vector(face)
                mpos = fvec + nvec
                cpos = self.interchunk(*mpos, blockchunk)
                pos = self.get_local_position(mpos)
                if cpos in self.chunks.keys():
                    newchunk = self.chunks[cpos]
                else:
                    if not newchunks:
                        continue
                    newchunk = chunk.Chunk(self, cpos)
                    self.chunks[cpos] = newchunk
                if (LightUpdateNode(newchunk, pos) not in self.lightupdatequeue.queue) and newchunk != blockchunk:
                    self.lightupdatequeue.put(LightUpdateNode(newchunk, pos))
                if not newchunk.is_opaque_block(pos) and newchunk.get_block_light(*pos) + 2 <= current_light:
                    newchunk.set_block_light(*pos, current_light - 1)
                    lightBfsQueue.put(BFSLightNode(*pos, newchunk, current_light - 1))

    def update_light(self, x, y, z, light):
        lpos = self.get_local_position((x, y, z))
        _chunk = self.chunks.get(self.get_chunk_position((x, y, z)), None)
        if _chunk is None:
            _chunk = chunk.Chunk(self, self.get_chunk_position((x, y, z)))
            self.chunks[self.get_chunk_position((x, y, z))] = _chunk
        lightBfsQueue.put(BFSLightNode(*lpos, _chunk, light))
        _chunk.set_block_light(*lpos, light)
        while not lightBfsQueue.empty():
            node = lightBfsQueue.get()
            blockchunk = node._chunk
            nx, ny, nz = node.x, node.y, node.z
            nvec = Vec3D(nx, ny, nz)
            current_light = node.light
            for face in range(0, 6):
                fvec = self.get_direction_vector(face)
                mpos = fvec + nvec
                cpos = self.interchunk(*mpos, blockchunk)
                pos = self.get_local_position(mpos)
                if cpos in self.chunks.keys():
                    newchunk = self.chunks[cpos]
                else:
                    newchunk = chunk.Chunk(self, cpos)
                    self.chunks[cpos] = newchunk
                if not newchunk.is_opaque_block(pos) and newchunk.get_block_light(*pos) + 2 <= current_light:
                    newchunk.set_block_light(*pos, current_light - 1)
                    lightBfsQueue.put(BFSLightNode(*pos, newchunk, current_light - 1))

    def interchunk(self, lx, ly, lz, _chunk):
        cx, cy, cz = _chunk.chunk_position
        fx = math.floor(lx / chunk.CHUNK_WIDTH)
        fy = math.floor(ly / chunk.CHUNK_HEIGHT)
        fz = math.floor(lz / chunk.CHUNK_LENGTH)
        chunkpos = (cx + fx, cy + fy, cz + fz)
        return chunkpos

    def remove_light(self, x, y, z):
        lpos = self.get_local_position((x, y, z))
        _chunk = self.chunks.get(self.get_chunk_position((x, y, z)), None)
        if _chunk is None:
            _chunk = chunk.Chunk(self, self.get_chunk_position((x, y, z)))
            self.chunks[self.get_chunk_position((x, y, z))] = _chunk
        val = _chunk.get_block_light(*lpos)
        removeBfsQueue.put(BFSLightRemovalNode(*lpos, _chunk, val))
        _chunk.set_block_light(*lpos, 0)
        while not removeBfsQueue.empty():
            node = removeBfsQueue.get()
            nx, ny, nz = node.x, node.y, node.z
            light = node.val
            blockchunk = node._chunk
            for face in range(0, 6):
                fx, fy, fz = self.get_direction_vector(face)
                mpos = (nx + fx, ny + fy, nz + fz)
                cpos = self.interchunk(*mpos, blockchunk)
                if cpos not in self.chunks.keys():
                    newchunk = chunk.Chunk(self, cpos)
                    self.chunks[cpos] = newchunk
                else:
                    newchunk = self.chunks[cpos]
                pos = self.get_local_position(mpos)
                neighbor = newchunk.get_block_light(*pos)
                if neighbor and neighbor < light:
                    newchunk.set_block_light(*pos, 0)
                    removeBfsQueue.put(BFSLightRemovalNode(*pos, newchunk, val))
                elif neighbor >= light:
                    lightBfsQueue.put(BFSLightNode(*pos, newchunk, neighbor))
                if (LightUpdateNode(newchunk, pos) not in self.lightupdatequeue.queue) and newchunk != blockchunk:
                    self.lightupdatequeue.put(LightUpdateNode(newchunk, pos))

    def get_direction_vector(self, face_number):
        face = ()
        if face_number == 0:  # EAST
            face = Vec3D(1, 0, 0)
        if face_number == 1:  # WEST
            face = Vec3D(-1, 0, 0)
        if face_number == 2:
            face = Vec3D(0, 1, 0)  # UP
        if face_number == 3:
            face = Vec3D(0, -1, 0)  # DOWN
        if face_number == 4:
            face = Vec3D(0, 0, 1)  # SOUTH
        if face_number == 5:
            face = Vec3D(0, 0, -1)  # NORTH
        return face

    def get_chunk_position(self, position):
        x, y, z = position

        return (
            math.floor(x / chunk.CHUNK_WIDTH),
            math.floor(y / chunk.CHUNK_HEIGHT),
            math.floor(z / chunk.CHUNK_LENGTH))

    def get_local_position(self, position):
        x, y, z = position

        return (
            int(x % chunk.CHUNK_WIDTH),
            int(y % chunk.CHUNK_HEIGHT),
            int(z % chunk.CHUNK_LENGTH))

    def get_block_number(self, position):
        x, y, z = position
        chunk_position = self.get_chunk_position(position)

        if not chunk_position in self.chunks:
            return 0

        lx, ly, lz = self.get_local_position(position)

        block_number = self.chunks[chunk_position].blocks[lx][ly][lz]
        return block_number

    def is_opaque_block(self, position):
        # get block type and check if it's opaque or not
        # air counts as a transparent block, so test for that too

        block_type = self.block_types[self.get_block_number(position)]

        if not block_type:
            return False

        return not block_type.transparent

    def update_lights(self):
        for chunkpos in self.chunks:
            self.chunks[chunkpos].lightMap = {}
        for light_blockpos in self.placed_light_blocks.keys():
            self.update_light(*light_blockpos, 15)

    def update_light_meshes(self):
        if self.lightupdatequeue.qsize():
            node = self.lightupdatequeue.get()
            node.newchunk.subchunks[node.position].update_mesh()
            node.newchunk.update_mesh()

    def set_block(self, position, number):  # set number to 0 (air) to remove block
        x, y, z = position
        chunk_position = self.get_chunk_position(position)

        if not chunk_position in self.chunks:  # if no chunks exist at this position, create a new one
            if number == 0:
                return  # no point in creating a whole new chunk if we're not gonna be adding anything

            self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)

        if self.get_block_number(position) == number:  # no point updating mesh if the block is the same
            return

        if not number and (self.get_block_number(position) in self.light_blocks):
            del self.placed_light_blocks[(x, y, z)]
            self.remove_light(x, y, z)

        lx, ly, lz = self.get_local_position(position)
        cx, cy, cz = chunk_position

        self.chunks[chunk_position].blocks[lx][ly][lz] = number
        if self.is_opaque_block(position) and number not in self.light_blocks:
            self.chunks[chunk_position].set_block_light(lx, ly, lz, 0)

        if number in self.light_blocks:
            self.chunks[chunk_position].set_block_light(lx, ly, lz, 15)
            self.create_light(x, y, z, 15)
            self.placed_light_blocks[(x, y, z)] = number

        self.update_lights()

        self.chunks[chunk_position].update_at_position((x, y, z))
        self.update_light_meshes()
        self.chunks[chunk_position].update_mesh(True)

        def try_update_chunk_at_position(chunk_position, position):
            if chunk_position in self.chunks:
                self.chunks[chunk_position].update_at_position(position)
                self.chunks[chunk_position].update_mesh()

        if lx == chunk.CHUNK_WIDTH - 1: try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
        if lx == 0: try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

        if ly == chunk.CHUNK_HEIGHT - 1: try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
        if ly == 0: try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

        if lz == chunk.CHUNK_LENGTH - 1: try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
        if lz == 0: try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))

    def draw(self):
        for chunk_position in self.chunks:
            self.chunks[chunk_position].draw()
