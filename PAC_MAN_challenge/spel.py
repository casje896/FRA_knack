import curses
import time
import sys
import os
import random
import re
import datetime
import struct
import zlib
import gzip
import string
import crypt
import codecs
#from Crypto.Cipher import ARC4


CRED_FILE = 'creds.txt'
COLOR_FILE = 'colors.txt'

COLOR_NORMAL = 1
global color_idx
color_idx = 2
def new_color(fg, bg, save=True):
    global color_idx
    curses.init_pair(color_idx, fg, bg)
    if save:
        with open(COLOR_FILE, 'a') as f:
            f.write('{},{},{}\n'.format(color_idx, fg, bg))
    color_idx += 1
    return color_idx - 1

def new_rgb(r, g, b):
    global color_idx
    curses.init_color(color_idx, fg, bg)
    color_idx += 1
    return color_idx - 1

class Coin(object):
    def __init__(self, value, world, coin_list):
        self.x = random.randint(1, world.x_size-1)
        self.y = random.randint(1, world.y_size-1)
        while not world.is_ok(self.x, self.y) and not self.in_list(self.x, self.y, coin_list):
            self.x = random.randint(1, world.x_size-1)
            self.y = random.randint(1, world.y_size-1)
        self.color = new_color(curses.COLOR_YELLOW, 0)
        self.marker = 'o'
        self.value = value


    def in_list(self, x, y, coin_list):
        for coin in coin_list:
            if x == coin.x and y == coin.y:
                return True
        return False


    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def on_coin(self, x, y):
        if self.x == x and self.y == y:
            return self.value
        return 0


class World(object):
    def __init__(self, map_file, xmax, ymax):
        self.load_map(map_file)
        self.x_size = len(self.world[0])
        self.y_size = len(self.world)
        

    def load_map(self, map_file):
        with open(map_file, 'r') as f:
            lines = f.readlines()

        # first 8 lines are color attributes
        m = re.search(r"('.+')", lines[0])
        self.marker_obj = eval(m.group())
        fg_obj = eval(lines[1].strip())
        bg_obj = eval(lines[2].strip())
        self.color_obj = new_color(fg_obj, bg_obj)
        self.att_obj = eval(lines[3].strip())
        
        m = re.search(r"('.+')", lines[4])
        self.marker_grd = eval(m.group())
        fg_grd = eval(lines[5].strip())
        bg_grd = eval(lines[6].strip())
        self.att_grd = eval(lines[7].strip())
        self.color_grd = new_color(fg_grd, bg_grd)

        buff = []
        for line in lines[8:]:  # 6 first lines are attr
            b = []
            for c in line.strip():
                if c != ' ':
                    b.append(1)
                else:
                    b.append(0)
            buff.append(b)
        self.world = buff

    def get_obj_tuple(self):
        return [self.marker_obj, self.color_obj, self.att_obj]
    
    def get_grd_tuple(self):
        return [self.marker_grd, self.color_grd, self.att_grd]

    def get_world(self):
        world = []
        oo = self.get_obj_tuple()
        gg = self.get_grd_tuple()
        for line in self.world:
            world.append(list([oo if x else gg for x in line]))
        return world

    def is_ok(self, x, y):
        if self.world[y][x]:
            return False
        return True


class ScoreBoard(object):
    def __init__(self, x, y, draw_func):
        self.draw = draw_func
        self.x = x  # upper left corner
        self.y = y  # spans downwards
        self.load_scoreboard()

        self.score = 0
        self.level = 1
        self.points_next = 30
        self.level_factor = 1.0

    def update_score(self, points):
        self.score += points
        score = str(self.score).zfill(7)
        score = '*   ' + score + '   *'
        for i, x in enumerate(score):
            self.draw(self.pos_score + self.y, self.x + i, x)


    def update_level(self, force_level=None):
        if force_level:
            self.level = force_level
        else:
            self.level += 1
        self.points_next += 30
        self.level_factor += 0.5

        lvl = str(self.level)
        lvl = '*      ' + lvl + '      *'
        for i, x in enumerate(lvl):
            self.draw(self.pos_level + self.y, self.x + i, x)

    def load_scoreboard(self):
        scoreboard_file = 'scoreboard.txt'
        with open(scoreboard_file, 'r') as f:
            lines = f.readlines()

        self.scoreboard = []
        self.pos_score = -1
        self.pos_level = -1
        for y, line in enumerate(lines):
            self.scoreboard.append(line.strip())
            if 'SCORE' in line:
                self.pos_score = y + 1
            if 'LEVEL' in line:
                self.pos_level = y + 1
        
    def draw_scoreboard(self):
        for y in range(len(self.scoreboard)):
            line = ''.join(self.scoreboard[y])
            for i, x in enumerate(line):
                self.draw(self.y + y, self.x + i, x)
            
    def advance(self):
        if self.score > self.points_next:
            self.update_level()
            return True
        return False


def bin_packer(keys, date, level, y, x, s, color_id, attr):
    payload = b""

    # Append timestamp
    ts = date.timestamp()
    ts_s = int(ts)
    ts_us = date.microsecond
    payload += struct.pack('>ccc', b't', b'i', b'm')
    # payload += struct.pack('>ii', ts_s, ts_us)
    payload += struct.pack('>d', ts)


    # Append coordinate
    payload += struct.pack('>ccc', b'p', b'o', b's')
    payload += struct.pack('>hh', y, x)        

    # Append marker
    payload += struct.pack('>ccc', b'm', b'k', b'r')
    payload += struct.pack('>c', s.encode())
    
    payload += struct.pack('>ccc', b'c', b'o', b'l')
    if color_id is None:  # Add 0 if None, else 1 + value
        payload += struct.pack('>b', 0)
    else:        
        payload += struct.pack('>b', 1)
        payload += struct.pack('>i', color_id)

    payload += struct.pack('>ccc', b'a', b't', b't')
    if attr is None:  # Add 0 if None, else 1 + value
        payload += struct.pack('>b', 0)
    else:        
        payload += struct.pack('>b', 1)
        payload += struct.pack('>i', attr)

    # Calculate checksum on raw data
    crc = zlib.crc32(payload)
    crc_bin = struct.pack('>I', crc)

    # Higher levels are encrypted to avoid sharing saved files with friends...
    if level == 1:  # Dont do anything for level = 1
        pass
    elif level == 2:
        ciph = gzip.compress(payload)
        payload = ciph
    elif level == 3:  # rot_13
        payload = codecs.encode(payload.hex(), 'rot_13').encode()

    elif level == 4:  # rc4
        k = keys['rc4']
        rc4 = ARC4.new(k)
        ciph = rc4.encrypt(payload)
        payload = ciph
    elif level == 5:
        k = keys['very_strong']
        rc4 = ARC4.new(k)
        ciph = rc4.encrypt(payload)
        payload = ciph
    else:
        pass

    # Pack level-info
    level_bin = struct.pack('>b', level)

    out_bin = b''
    out_bin += struct.pack('>ccc', b'c', b'r', b'c')
    out_bin += crc_bin
    out_bin += struct.pack('>ccc', b'l', b'v', b'l')
    out_bin += level_bin
    out_bin += struct.pack('>ccc', b'd', b'a', b't')
    out_bin += payload

    # Calculate total length
    ll = len(out_bin)
    out_bin = struct.pack('>h', ll) + out_bin

    # Packet structure: length + crc + level + payload
    return out_bin
########################################################################################################
def bin_unpacker(file_name):
    cs = struct.calcsize
    with open(file_name, 'rb') as f:
        data = f.read()

    keys = load_keys()

    packets = []
    pos = 0

    i = 0
    while pos < len(data):
        ll = struct.unpack('>h', data[pos:pos+cs('>h')])[0]
        pos += cs('>h')
        d = data[pos:pos+ll]
        packets.append(d)
        pos += ll

        
    unpacked_data = []
    for p in packets:
        pos = 0
        
        # TODO: Unpack every packets and extract the data needed below

        unpacked_data.append([ts, level, y, x, marker, color, attr])
        
    return unpacked_data


class Scene(object):

    def __init__(self, scr, map_files, save_file_name=None):
        
        self.save_file_name = None
        if save_file_name:
            self.save_file = open(save_file_name, 'w')
            save_file_name_bin = save_file_name.split('.')[0] + '_v2.bin'
            self.save_file_bin = open(save_file_name_bin, 'wb')

        self.load_keys()

        self.scr = scr
        ymax, xmax = scr.getmaxyx()
        self.xmax = xmax - 1
        self.ymax = ymax - 1
        self.finished = False
        self.finished_shown = False

        # Initialise world
        self.map_files = map_files
        self.map_counter = 1
        self.load_world(map_files[self.map_counter - 1])
        
        # Initialise scoreboard
        self.scoreboard = ScoreBoard(51, 0, self.draw)
        self.scoreboard.draw_scoreboard()
        
        # Initialise player
        self.player = None

        # Initialise coins
        nr_coins = 5
        self.coin_list = []
        for i in range(nr_coins):
            val = random.randint(1, 11)
            c = Coin(val, self.world, self.coin_list)
            self.coin_list.append(c)
        self.draw_coins()

    def load_keys(self):
        self.keys = {}
        with open(CRED_FILE, 'r') as f:
            lines = [x.strip() for x in f.readlines()]
        for line in lines:
            k, v = line.split(':')
            self.keys[k] = v


    def load_world(self, map_file):
        self.world = World(map_file, self.xmax, self.ymax)
        if not self.world:
            return None
        self.draw_world()

    def init_player(self):
        x = 2
        y = 2
        self.player = Player('@', x, y, self.xmax, self.ymax)
        self.player.marker_prev = ' '
        self.draw(y, x, self.player.body)
        
    def show_finish_screen(self):
        fn = 'finish_screen.txt'
        with open(fn, 'r') as f:
            lines = f.readlines()
        m = re.search(r"('.+')", lines[0])
        marker_obj = eval(m.group())
        fg_obj = eval(lines[1].strip())
        bg_obj = eval(lines[2].strip())
        color_obj = new_color(fg_obj, bg_obj)
        att_obj = eval(lines[3].strip())
        
        m = re.search(r"('.+')", lines[4])
        marker_grd = eval(m.group())
        fg_grd = eval(lines[5].strip())
        bg_grd = eval(lines[6].strip())
        att_grd = eval(lines[7].strip())
        color_grd = new_color(fg_grd, bg_grd)

        for ypos, line in enumerate(lines[8:]):
            for xpos, c in enumerate(line):
                if c == ' ':
                    self.draw(ypos, xpos, c, color_grd, att_grd)
                else:
                    self.draw(ypos, xpos, c, color_obj, att_obj)

    def move_player(self, key):
        if self.finished_shown:
            if key!='KEY_UP' and key!='KEY_DOWN' and key!='KEY_RIGHT' and key!='KEY_LEFT':
                sys.exit()
        if self.finished:
            self.show_finish_screen()
            self.scoreboard.draw_scoreboard()
            self.scoreboard.update_score(0)
            self.scoreboard.update_level(self.map_counter)
            self.finished_shown = True
            time.sleep(3)
            sys.exit()
            return

        # Check if move is valid 
        x, y = self.player.new_position(key)
        if self.world.is_ok(x, y):
            x_prev = self.player.x
            y_prev = self.player.y
            self.player.move(x, y)
            self.draw(y, x, self.player.body)
            marker, color, attr = self.world.get_grd_tuple()
            self.draw(y_prev, x_prev, marker, color, attr)
            
            # Did we step on a coin?
            for coin in self.coin_list:
                if coin.on_coin(x, y):
                    self.scoreboard.update_score(coin.value)
                    self.coin_list.remove(coin)
                    break

        # Spawn new coin
        val = random.randint(1, 1000)
        if (val > 900 or len(self.coin_list) < 3) and not len(self.coin_list) > 10:
            val = int(val / 100. * self.scoreboard.level_factor)
            coin = self.spawn_new_coin(val)
            self.draw_coin(coin)

        # Advance to next level? Change map!
        if self.scoreboard.advance():
            for coin in self.coin_list:
                self.coin_list.remove(coin)
            if self.map_counter == len(self.map_files):
                self.finished = True
                return
            self.load_world(self.map_files[self.map_counter])
            self.map_counter += 1
            self.draw_world()
            for i in range(5):
                self.spawn_new_coin(random.randint(1, 10))
            self.draw_coins()
            self.secure_player()

    def secure_player(self):
        x = 2
        y = 2
        self.player.move(x, y)
        self.draw(y, x, self.player.body)
        
    def spawn_new_coin(self, value):
        coin = Coin(value, self.world, self.coin_list)
        self.coin_list.append(coin)
        return coin

    def draw_world(self):
        world = self.world.get_world()
        for ypos, line in enumerate(world):
            for xpos, cc in enumerate(line):
                marker, color, attr = cc
                self.draw(ypos, xpos, marker, color, attr)
        
    def draw_coins(self):
        for coin in self.coin_list:
            self.draw_coin(coin)

    def draw_coin(self, coin):
        self.draw(coin.y, coin.x, coin.marker, coin.color, curses.A_BOLD)

    def draw(self, y, x, s, color_id=None, attr=None):
        color = 0
        if color_id:
            color = curses.color_pair(color_id)
        if attr:
            color = color | attr
        self.scr.addstr(y, x, s, color)
        self.scr.refresh()
        self.draw_saver(y, x, s, color_id, attr)

    def draw_saver(self, y, x, s, color_id, attr):
        if self.save_file:
            date = datetime.datetime.now()
            if date.microsecond == 0:
                date = date + datetime.timedelta(microseconds=1)
            try:
                level = self.scoreboard.level
            except AttributeError:
                level = 1
            if color_id:
                color = color_id
            else:
                color = 0
            if s == '\n':
                return
            
            out = ','.join([str(date), str(level), str(y), str(x), str(s), str(color), str(attr)])
            self.save_file.write(out + '\n')

            # Prepare data for binary save
            out_bin = bin_packer(self.keys, date, level, y, x, s, color_id, attr)
            self.save_file_bin.write(out_bin)
            

class Player(object):
    def __init__(self, body, x, y, xmax, ymax):
        self.x = int(x)
        self.y = int(y)

        self.x_prev = x
        self.y_prev = y
        self.marker_prev = None

        self.body = body

    def new_position(self, key, motion=1):
        x_new = self.x
        y_new = self.y
        if key=='KEY_UP':
            y_new -= motion
        if key=='KEY_DOWN':
            y_new += motion
        if key=='KEY_LEFT':
            x_new -= motion
        if key=='KEY_RIGHT':
            x_new += motion
        return x_new, y_new

    def move(self, new_x, new_y):
        self.x = new_x
        self.y = new_y


def play_live(stdscr):
    with open(COLOR_FILE, 'w') as f:
        f.write('')
    stdscr.clear()
    curses.curs_set(0)
    curses.init_pair(COLOR_NORMAL, 0, curses.COLOR_WHITE)

    map_files = [m for m in os.listdir('.') if "map" in m]
    save_timetrace = 'savefile.txt'
    save_keytrace = 'keyfile.txt'
    with open(save_keytrace, 'w') as f_key:

        scene = Scene(stdscr, map_files, save_timetrace)
        scene.init_player()

        running = True
        while running:

            k = stdscr.getkey()
            d = datetime.datetime.now()
            if d.microsecond == 0:
                d = d + datetime.timedelta(microseconds=1)
            f_key.write(str(d) + ',' + str(k.encode()) + '\n')

            if k.encode() == b'\x1b':
                sys.exit()

            scene.move_player(k)

def date_parser(s):
    f = '%Y-%m-%d %H:%M:%S.%f'
    return datetime.datetime.strptime(s, f)


def replay_v1(stdscr, file_name):
    stdscr.clear()
    curses.curs_set(0)
    curses.init_pair(COLOR_NORMAL, 0, curses.COLOR_WHITE)

    color_dict = {}
    with open(COLOR_FILE, 'r') as f:
        for line in f:
            nr, fg, bg = line.strip().split(',')
            curses.init_pair(int(nr), int(fg), int(bg))
            
    # Get starting time
    with open(file_name, 'r') as f:
        d = f.readline()
        d = d.strip().split(',')
        date, level, y, x, s, color_id, attr = d
        d0 = date_parser(date)

    with open(file_name, 'r') as f:
        for line in f:
            
            d = line.strip().split(',')
            
            date, level, y, x, s, color_id, attr = d
            date = date_parser(date)
            color = 0
            if color_id != 'None':
                color = curses.color_pair(int(color_id))
            if attr != 'None':
                color = color | int(attr)
            
            stdscr.addstr(int(y), int(x), s, color)
            stdscr.refresh()
            dt = date - d0
            
            time.sleep(dt.total_seconds())
            d0 = date
    k = stdscr.getkey()



def load_keys():
    keys = {}
    with open(CRED_FILE, 'r') as f:
        lines = [x.strip() for x in f.readlines()]
    for line in lines:
        k, v = line.split(':')
        keys[k] = v
    return keys


def replay_v2(stdscr, file_name):
    data = bin_unpacker(file_name)
    stdscr.clear()
    curses.curs_set(0)
    curses.init_pair(COLOR_NORMAL, 0, curses.COLOR_WHITE)

    color_dict = {}
    with open(COLOR_FILE, 'r') as f:
        for line in f:
            nr, fg, bg = line.strip().split(',')
            curses.init_pair(int(nr), int(fg), int(bg))
            
    d0 = datetime.datetime.fromtimestamp(data[0][0])  # start time

    for d in data:
            
        date, level, y, x, s, color_id, attr = d
        date = datetime.datetime.fromtimestamp(date)
        color = 0
        if color_id != None:
            color = curses.color_pair(int(color_id))
        if attr != None:
            color = color | int(attr)
        
        stdscr.addstr(int(y), int(x), s, color)
        stdscr.refresh()
        dt = date - d0
        
        time.sleep(dt.total_seconds())
        d0 = date
    k = stdscr.getkey()

def replay_save(stdscr, file_name):
    if 'v2.bin' in file_name:
        replay_v2(stdscr, file_name)
    else:
        replay_v1(stdscr, file_name)

    time.sleep(3)
    sys.exit()



def gen_shadow_hash(type_, passwd):
    # https://www.shellhacks.com/linux-generate-password-hash/
    if type_ == 'md5':
        salt = crypt.mksalt(crypt.METHOD_MD5)
        
    elif type_ == 'sha256':
        salt = crypt.mksalt(crypt.METHOD_SHA256)
        
    elif type_ == 'sha512':
        salt = crypt.mksalt(crypt.METHOD_SHA512)

    myhash = crypt.crypt(passwd, salt)
    return myhash
        


def generate_creds(fn):
    with open(fn, 'w') as f:
        rc4_key = ''.join(random.choices(string.ascii_letters, k=4))
        f.write('rc4:' + rc4_key)
        
        other_pw_file = 'pass.txt'
        if os.path.isfile(other_pw_file):
            with open(other_pw_file, 'r') as ff:
                passwd = ff.read() 
                # The strength of this password rocks!
                # Keeping a hashed copy of it here, in case I lose the password file again...
                # $6$mmUGx94Qaj9bmzyI$GqPaUiIXEENoAlzWd1NV5Qvm3wQMLPJLQvAg4tRmfW5wZTlynzPrs8wCCM6zcVvL3YSEbdyh7W3P.W2ByJfRe/
            # myhash = gen_shadow_hash('sha512', passwd)
            f.write('\nvery_strong:' + passwd)

        


def main(stdscr):
    if len(sys.argv) == 1:
        generate_creds(CRED_FILE)
        play_live(stdscr)
    else:
        replay_save(stdscr, sys.argv[1])

curses.wrapper(main)
