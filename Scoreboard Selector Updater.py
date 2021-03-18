# coding unicode-escape
""" Scoreboard Selector Updator
Original by SethBling (http://youtube.com/SethBling)
Heavily modified by Paulson McIntyre <paul@gpmidi.net> (https://gpmidi.net)

GitHub Home: https://github.com/gpmidi/MCEdit-Filters

(Viewing in github.com as raw and need to download? Hit ctrl-s or super-s! )
"""
from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_String
import re
from collections import namedtuple

displayName = "Scoreboard Selector Updater"

# @a[score_temp_min=1,score_temp=1]
ReTakeApart = re.compile(r'(?P<all>\@(?P<target>[a-z])\[(?P<args>[^\[\]]+)\])')
ScoreF = namedtuple('ScoreF', ['key', 'value', 'isMin', 'name'])
ReEffectClear = re.compile(r'(?P<all>effect\s(?P<target>[^ ]+)\sclear)')
ReMatchEffectGive = re.compile(r'(?P<all>(?:effect(?! give)(?! clear))|(?:effect$))')


def perform(level, box, options):
    for (chunk, slices, point) in level.getChunkSlices(box):
        for t in chunk.TileEntities:
            x = t["x"].value
            y = t["y"].value
            z = t["z"].value

            if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
                if t["id"].value == "minecraft:command_block":
                    cmd = t["Command"].value
                    newcmd = things(cmd, x, box.minx, box.maxx, y, box.miny, box.maxy, z, box.minz, box.maxz)
                    if newcmd != cmd:
                        t["Command"] = TAG_String(newcmd)
                        chunk.dirty = True


def things(line, x, minx, maxx, y, miny, maxy, z, minz, maxz):
    # Effect clear
    ec = ReEffectClear.finditer(line)
    if ec:
        for m in ec:
            line = line.replace(m.group("all"), "effect clear %s" % m.group("target"))

    # Effect give - Must be after clear
    eg = ReMatchEffectGive.finditer(line)
    if eg:
        for m in ec:
            line = line.replace(m.group('all'), "effect give")

    # Target take apart
    fa = ReTakeApart.finditer(line)
    if fa:
        for m in fa:
            args = m.group("args")

            kvs = {}
            founds = {}
            for argKV in args.split(","):
                if len(argKV.split("=")) != 2:
                    continue
                key, value = argKV.split("=")
                if key.startswith("score_"):
                    name = key.replace("score_", "").replace("_min", "")
                    if not founds.get(name, None):
                        founds[name] = []
                    founds[name].append(ScoreF(key, value, key.endswith("_min"), name))
                else:
                    kvs[key] = value

            nvs = []
            for name, parts in founds.items():
                fMin = None
                fMax = None
                for p in parts:
                    if p.isMin:
                        fMin = p
                    else:
                        fMax = p
                if not fMin and not fMax:
                    continue
                elif fMin and fMax:
                    if fMin.value == fMax.value:
                        nvs.append("%s=%s" % (fMin.name, fMin.value))
                    else:
                        nvs.append("%s=%s..%s" % (fMin.name, fMin.value, fMax.value))
                elif fMin and not fMax:
                    nvs.append("%s=%s.." % (fMin.name, fMin.value))
                elif fMax and not fMin:
                    nvs.append("%s=..%s" % (fMax.name, fMax.value))

            if len(nvs) > 0:
                kvs["scores"] = "{" + ",".join(nvs) + "}"
                newNew = "@%s[%s]" % (m.group("target"), ','.join(["%s=%s" % (k, v) for k, v in kvs.items()]))
                line = line.replace(m.group("all"), newNew)

    return line
