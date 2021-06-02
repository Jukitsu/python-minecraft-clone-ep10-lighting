import math

import chunk
import subchunk
import block_type
import texture_manager
import random

from vector import *
from collections import deque

# import custom block models

import models.plant
import models.cactus
import models.cube
import models.torch

import time

light_threads = []

RENDERDISTANCE = 8
WORLDSIZE = 8
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

    def reset(self):
        self.queue = list()

BLOCKLIGHT = 1
SKYLIGHT = 2

class BFSLightNode:
    def __init__(self, x, y, z, _chunk, light, light_type=BLOCKLIGHT):
        self.x = x
        self.y = y
        self.z = z
        self._chunk = _chunk
        self.light = light
        self.light_type = light_type


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
        self.position = localposition

directions = (EAST, WEST, UP, DOWN, NORTH, SOUTH)
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
        #self.block_types.append(block_type.Block_type(self.texture_manager, "torch", {"all": "torch_on"}, models.plant))
        self.block_types.append(block_type.Block_type(self.texture_manager, "torch", {"top": "torch_top", "sides": "torch_side"}, models.torch, 15))
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
                            if j == 15:
                                current_chunk.blocks[i][j][k] = random.choices([0, 9, 10], [20, 2, 1])[0]
                            elif j == 14:
                                current_chunk.blocks[i][j][k] = 2
                            elif 9 < j < 14:
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
                                self.create_skylight((x, y, z), 15)

        for chunk_position in self.chunks.keys():
            self.chunks[chunk_position].update_subchunk_meshes()
            self.chunks[chunk_position].update_mesh()

    # create functions to make things a bit easier

    def get_chunk(self, cpos, create=True):
        if cpos in self.chunks.keys():
            newchunk = self.chunks[cpos]
        else:
            if create:
                newchunk = chunk.Chunk(self, cpos)
                self.chunks[cpos] = newchunk
            else:
                return None
        return newchunk

    def create_skylight(self, pos, light):  # Currently Broken
        if 1: return
        lpos = self.get_local_position(pos)
        cpos = self.get_chunk_position(pos)
        _chunk = self.get_chunk(cpos)
        lightBfsQueue.put(BFSLightNode(*lpos, _chunk, light, SKYLIGHT))
        _chunk.set_sky_light(lpos, light)
        self.propagate_light()

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

    def create_light(self, pos, light):
        x, y, z = pos
        lpos = self.get_local_position(pos)
        cpos = self.get_chunk_position(pos)
        _chunk = self.get_chunk(cpos)
        lightBfsQueue.put(BFSLightNode(*lpos, _chunk, light))
        _chunk.set_block_light(lpos, light)
        self.propagate_light()

    def propagate_light(self):
        starttime = time.time()
        while not lightBfsQueue.empty():
            node = lightBfsQueue.get()
            blockchunk = node._chunk
            nx, ny, nz = node.x, node.y, node.z
            current_light = node.light
            light_type = node.light_type
            for face in range(0, 6):
                fx, fy, fz = self.get_direction_vector(face)
                mpos = (nx + fx, ny + fy, nz + fz)
                cpos = self.interchunk(mpos, blockchunk)
                pos = self.get_local_position(mpos)
                newchunk = self.get_chunk(cpos)
                if not newchunk.is_opaque_block(pos) and newchunk.get_block_light(pos) + 2 <= current_light:
                    self.set_light(blockchunk, mpos, current_light - 1, light_type)
                    self.set_light(newchunk, pos, current_light - 1, light_type)
                    lightBfsQueue.put(BFSLightNode(*pos, newchunk, current_light - 1, light_type))
                    px, py, pz = pos
                    lupos = (math.floor(px / subchunk.SUBCHUNK_WIDTH),
                             math.floor(py / subchunk.SUBCHUNK_HEIGHT),
                             math.floor(pz / subchunk.SUBCHUNK_LENGTH))
                    self.lightupdatequeue.put(LightUpdateNode(newchunk, lupos))
        endtime = time.time()
        if round(endtime - starttime, 2):
            print(f"propagation algorithm took {round(endtime - starttime, 3)}")  # debug


    def set_light(self, lchunk, lpos, light_level, light_type):
        if light_type == BLOCKLIGHT:
            lchunk.set_block_light(lpos, light_level)
        elif light_type == SKYLIGHT:
            lchunk.set_sky_light(lpos, light_level)

    def get_light(self, lchunk, lpos, light_type):
        if light_type == BLOCKLIGHT:
            lchunk.get_block_light(lpos)
        elif light_type == SKYLIGHT:
            lchunk.get_sky_light(lpos)

    def interchunk(self, lpos, _chunk):
        lx, ly, lz = lpos
        cx, cy, cz = _chunk.chunk_position
        fx = math.floor(lx / chunk.CHUNK_WIDTH)
        fy = math.floor(ly / chunk.CHUNK_HEIGHT)
        fz = math.floor(lz / chunk.CHUNK_LENGTH)
        chunkpos = (cx + fx, cy + fy, cz + fz)
        return chunkpos

    def remove_light(self, pos):
        lpos = self.get_local_position(pos)
        cpos = self.get_chunk_position(pos)
        _chunk = self.get_chunk(cpos)
        val = _chunk.get_block_light(lpos)
        removeBfsQueue.put(BFSLightRemovalNode(*lpos, _chunk, val))
        _chunk.set_block_light(lpos, 0)
        self.unpropagate_light()
        self.propagate_light()


    def unpropagate_light(self):
        starttime = time.time()
        while not removeBfsQueue.empty():
            node = removeBfsQueue.get()
            nx, ny, nz = node.x, node.y, node.z
            light = node.val
            blockchunk = node._chunk
            for face in range(0, 6):
                fx, fy, fz = self.get_direction_vector(face)
                mpos = (nx + fx, ny + fy, nz + fz)
                cpos = self.interchunk(mpos, blockchunk)
                newchunk = self.get_chunk(cpos)
                pos = self.get_local_position(mpos)
                neighbor = newchunk.get_block_light(pos)
                if neighbor and neighbor < light:
                    blockchunk.set_block_light(mpos, 0)
                    newchunk.set_block_light(pos, 0)
                    removeBfsQueue.put(BFSLightRemovalNode(*pos, newchunk, neighbor))
                    px, py, pz = pos
                    lupos = (math.floor(px / subchunk.SUBCHUNK_WIDTH),
                             math.floor(py / subchunk.SUBCHUNK_HEIGHT),
                             math.floor(pz / subchunk.SUBCHUNK_LENGTH))
                    self.lightupdatequeue.put(LightUpdateNode(newchunk, lupos))
                elif neighbor >= light:
                    lightBfsQueue.put(BFSLightNode(*pos, newchunk, neighbor, BLOCKLIGHT))
        endtime = time.time()
        if round(endtime - starttime, 2):
            print(f"unpropagation algorithm took {round(endtime - starttime, 3)}")  # debug

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

        if self.get_block_number(position) in self.light_blocks:
            return False

        return not block_type.transparent



    def update_light_meshes(self):
        if self.lightupdatequeue.qsize() > 32767:
            print(f"chunk lighting update queue overflowed, skipped {self.lightupdatequeue.qsize()} chunk updates")
            self.lightupdatequeue.reset()
        size = self.lightupdatequeue.qsize()
        chunk_updates = []
        updated_subchunks = []
        for i in range(size):
            node = self.lightupdatequeue.get()
            _subchunk = node.newchunk.subchunks[node.position]
            if _subchunk not in updated_subchunks:
                _subchunk.update_mesh()
                updated_subchunks.append(_subchunk)
            if node.newchunk not in chunk_updates:
                chunk_updates.append(node.newchunk)
        for newchunk in chunk_updates:
            newchunk.update_mesh()



    def neighbour_check(self, position):
        lights = []
        lnodes = []
        slights = []
        snodes = []
        for f in range(0, 6):
            face = self.get_direction_vector(f)
            _pos = tuple(Vec3D(position) + face)
            if self.is_opaque_block(_pos):
                continue
            _cpos = self.get_chunk_position(_pos)
            _lpos = self.get_local_position(_pos)
            if _cpos not in self.chunks:
                continue
            neighbourl = self.chunks[_cpos].get_block_light(_lpos)
            neighboursl = self.chunks[_cpos].get_sky_light(_lpos)
            lnode = BFSLightNode(*_lpos, self.chunks[_cpos], neighbourl)
            snode = BFSLightNode(*_lpos, self.chunks[_cpos], neighboursl)
            snodes.append(snode)
            lnodes.append(lnode)
            lights.append(neighbourl)
            slights.append(neighboursl)
        if len(lights):
            l = max(lights)
            lnode = lnodes[lights.index(l)]
            lightBfsQueue.put(lnode)
        if len(slights):
            sl = max(slights)
            snode = snodes[slights.index(sl)]
            lightBfsQueue.put(snode)
        self.propagate_light()



    def set_block(self, position, number):  # set number to 0 (air) to remove block
        x, y, z = position
        chunk_position = self.get_chunk_position(position)

        if not chunk_position in self.chunks:  # if no chunks exist at this position, create a new one
            if number == 0:
                return  # no point in creating a whole new chunk if we're not gonna be adding anything

            self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)

        if self.get_block_number(position) == number:  # no point updating mesh if the block is the same
            return

        if self.get_block_number(position) in self.light_blocks:
            self.remove_light(position)

        lx, ly, lz = self.get_local_position(position)
        cx, cy, cz = chunk_position

        self.chunks[chunk_position].blocks[lx][ly][lz] = number

        if self.is_opaque_block(position) and number not in self.light_blocks:
            self.remove_light(position)

        if number in self.light_blocks:
            self.create_light(position, 15)


        if not number:
            self.neighbour_check(position)



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
