# -*- coding: utf-8 -*-

"""Calculate the crossword and export image and text files."""

# Authors: David Whitlock <alovedalongthe@gmail.com>, Bryan Helmig
# Crossword generator that outputs the grid and clues as a pdf file and/or
# the grid in png/svg format with a text file containing the words and clues.
# Copyright (C) 2010-2011 Bryan Helmig
# Copyright (C) 2011-2012 David Whitlock
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random, time, string, cairo
 
class Crossword(object):
    def __init__(self, cols, rows, empty = '-', available_words=[]):
        self.cols = cols
        self.rows = rows
        self.empty = empty
        self.available_words = available_words
        self.current_word_list = []
        self.prep_grid_words()
 
    def prep_grid_words(self):
        """Initialize grid and word list."""
        self.grid = [[self.empty for j in range(self.cols)] for i in range(self.rows)]
        try:
            temp_list = [Word(word.word, word.clue) if isinstance(word, Word) else Word(word[0], word[1]) for word in self.available_words]
        except:
            temp_list = [Word(word[0], 'Write clue for ' + word[0]) for word in self.available_words]
        random.shuffle(temp_list) # randomize word list
        temp_list.sort(key=lambda i: len(i.word), reverse=True) # sort by length
        self.available_words = temp_list
 
    def compute_crossword(self, time_permitted = 1.00, spins=2):
        time_permitted = float(time_permitted)
        copy = Crossword(self.cols, self.rows, self.empty, self.available_words)
 
        start_full = float(time.time())
        while (float(time.time()) - start_full) < time_permitted:
            copy.current_word_list = []
            copy.prep_grid_words()
            copy.first_word(copy.available_words[0])
            [copy.add_words(word) for i in range(spins) for word in copy.available_words if word not in copy.current_word_list]
            if len(copy.current_word_list) > len(self.current_word_list):
                self.current_word_list = copy.current_word_list
                self.grid = copy.grid
            if len(self.current_word_list) == len(self.available_words):
                break
        return
 
    def get_coords(self, word):
        """Return possible coordinates for each letter."""
        coordlist = []
        temp_list =  [(l, r, self.grid[r].index(letter)) for l, letter in enumerate(word.word) for r in range(self.rows) if letter in self.grid[r]]
        for coord in temp_list:
            letc, rowc, colc = coord[0], coord[1], coord[2]
            if rowc - letc >= 0 and ((rowc - letc) + word.length) <= self.rows:
                col, row, vertical = (colc, rowc - letc, 1)
                score = self.check_fit_score(col, row, vertical, word)
                if score:
                    coordlist.append([colc, rowc - letc, 1, score])
            if colc - letc >= 0 and ((colc - letc) + word.length) <= self.cols:
                col, row, vertical = (colc - letc, rowc, 0)
                score = self.check_fit_score(col, row, vertical, word)
                if score:
                        coordlist.append([colc - letc, rowc, 0, score])
        random.shuffle(coordlist)
        coordlist.sort(key=lambda i: i[3], reverse=True)
        return coordlist
 
    def first_word(self, word):
        """Place the first word at a random position in the grid."""
        vertical = random.randrange(0, 2)
        if vertical:
            col = random.randrange(0, self.cols)
            row = random.randrange(0, self.rows - word.length)
        else:
            col = random.randrange(0, self.cols - word.length)
            row = random.randrange(0, self.rows)
        self.set_word(col, row, vertical, word)

    def add_words(self, word):
        """Add the rest of the words to the grid."""
        fit = False
        count = 0
        coordlist = self.get_coords(word)
 
        while not fit:
            try: 
                col, row, vertical = coordlist[count][0], coordlist[count][1], coordlist[count][2]
            except IndexError: return # no more cordinates, stop trying to fit

            if coordlist[count][3]: # already filtered these out, but double check
                fit = True 
                self.set_word(col, row, vertical, word) 
            count += 1
        return
 
    def check_fit_score(self, col, row, vertical, word):
        """Return score (0 means no fit, 1 means a fit, 2+ means a cross)."""
        if col < 0 or row < 0:
            return 0
 
        count, score = 1, 1 # give score a standard value of 1, will override with 0 if collisions detected
        for letter in word.word:            
            try:
                active_cell = self.grid[row][col]
            except IndexError:
                return 0
            if active_cell == self.empty or active_cell == letter:
                pass
            else:
                return 0
            if active_cell == letter:
                score += 1
 
            if vertical:
                if active_cell != letter:
                    if not self.check_cell_empty(col+1, row) or not self.check_cell_empty(col-1, row):
                        return 0
                if count == 1 and not self.check_cell_empty(col, row-1):
                    return 0
                if count == len(word.word) and not self.check_cell_empty(col, row+1) and row + 1 != self.rows:
                    return 0
            else:
                if active_cell != letter:
                    if not self.check_cell_empty(col, row-1) or not self.check_cell_empty(col, row+1):
                        return 0
                if count == 1 and not self.check_cell_empty(col-1, row):
                    return 0
                if count == len(word.word) and not self.check_cell_empty(col+1, row) and col + 1 != self.cols:
                    return 0

            if vertical: # progress to next letter and position
                row += 1
            else: # else horizontal
                col += 1
 
            count += 1
 
        return score
 
    def set_word(self, col, row, vertical, word):
        """Put words on the grid and add them to the word list."""
        word.col = col + 1
        word.row = row + 1
        word.vertical = vertical
        self.current_word_list.append(word)

        for letter in word.word:
            self.grid[row][col] = letter
            if vertical:
                row += 1
            else:
                col += 1
        return
 
    def check_cell_empty(self, col, row):
        try:
            cell = self.grid[row][col]
            if cell == self.empty: 
                return True
        except IndexError:
            pass
        return False
 
    def solution(self):
        answer = '\n'.join([''.join(['{} '.format(c) for c in self.grid[r]]) for r in range(self.rows)])
        return answer + '\n' + str(len(self.current_word_list)) + ' out of ' + str(len(self.available_words))
 
    def order_number_words(self): # orders words and applies numbering system to them
        self.current_word_list.sort(key=lambda i: (i.col))
        self.current_word_list.sort(key=lambda i: (i.row))
        count, icount = 1, 1
        for word in self.current_word_list:
            word.number = count
            if icount < len(self.current_word_list):
                if word.col == self.current_word_list[icount].col and word.row == self.current_word_list[icount].row:
                    pass
                else:
                    count += 1
            icount += 1

    def draw_img(self, name, context, px, xoffset, yoffset):
        for r in range(self.rows):
            for i, c in enumerate(self.grid[r]):
                if c != self.empty:
                    context.set_line_width(1.0)
                    context.set_source_rgb(0.5, 0.5, 0.5)
                    context.rectangle(xoffset+(i*px), yoffset+(r*px), px, px)
                    context.stroke()
                    context.set_line_width(1.0)
                    context.set_source_rgb(0, 0, 0)
                    context.rectangle(xoffset+1+(i*px), yoffset+1+(r*px), px-2, px-2)
                    context.stroke()
                    if '_key.' in name:
                        self.draw_letters(c, context, xoffset+(i*px)+10, yoffset+(r*px)+22, 14)

        self.order_number_words()
        for word in self.current_word_list:
            x, y = xoffset+((word.col-1)*px), yoffset+((word.row-1)*px)
            self.draw_letters(str(word.number), context, x+3, y+10, 8)

    def draw_letters(self, text, context, xval, yval, fontsize, bold=False):
        if bold:
            context.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        else:
            context.select_font_face('monospace')
        context.set_font_size(fontsize)
        context.move_to(xval, yval)
        context.show_text(text)

    def create_img(self, name):
        px = 28
        if name.endswith('png'):
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 10+(self.cols*px), 10+(self.rows*px))
        else:
            surface = cairo.SVGSurface(name, 10+(self.cols*px), 10+(self.rows*px))
        context = cairo.Context(surface)
        context.set_source_rgb(1, 1, 1)
        context.rectangle(0, 0, 10+(self.cols*px), 10+(self.rows*px))
        context.fill()
        self.draw_img(name, context, 28, 5, 5)
        if name.endswith('png'):
            surface.write_to_png(name)
        else:
            context.show_page()
            surface.finish()

    def export_pdf(self, xwname, filetype, width=595, height=842):
        px, xoffset, yoffset = 28, 36, 72
        name = xwname + filetype
        surface = cairo.PDFSurface(name, width, height)
        context = cairo.Context(surface)
        context.set_source_rgb(1, 1, 1)
        context.rectangle(0, 0, width, height)
        context.fill()
        context.save()
        sc_ratio = float(width-(xoffset*2))/(px*self.cols)
        if self.cols <= 21:
            sc_ratio, xoffset = 0.8, float(1.25*width-(px*self.cols))/2
        context.scale(sc_ratio, sc_ratio)
        self.draw_img(name, context, 28, xoffset, 80)
        context.restore()
        context.set_source_rgb(0, 0, 0)
        self.draw_letters(xwname, context, round((width-len(xwname)*10)/2), yoffset/2, 18, bold=True)
        x, y = 36, yoffset+5+(self.rows*px*sc_ratio)
        self.draw_letters('Across', context, x, y, 14, bold=True)
        clues = self.wrap(self.legend())
        for line in clues.splitlines()[3:]:
            if y >= height-(yoffset/2)-15:
                context.show_page()
                y = yoffset/2
            if line.strip() == 'Down':
                if self.cols > 17 and y > 700:
                    context.show_page()
                    y = yoffset/2
                self.draw_letters('Down', context, x, y+15, 14, bold=True)
                y += 16
                continue
            self.draw_letters(line, context, x, y+15, 10)
            y += 16
        context.show_page()
        surface.finish()

    def create_files(self, name, save_format, gtkmode=False):
        img_files = ''
        if 'p' in save_format:
            self.export_pdf(name, '_grid.pdf')
            self.export_pdf(name, '_key.pdf')
            img_files += name + '_grid.pdf ' + name + '_key.pdf '
        if 'l' in save_format:
            self.export_pdf(name, 'l_grid.pdf', 612, 792)
            self.export_pdf(name, 'l_key.pdf', 612, 792)
            img_files += name + 'l_grid.pdf ' + name + 'l_key.pdf '
        if 'n' in save_format:
            self.create_img(name + '_grid.png')
            self.create_img(name + '_key.png')
            img_files += name + '_grid.png ' + name + '_key.png '
        if 's' in save_format:
            self.create_img(name + '_grid.svg')
            self.create_img(name + '_key.svg')
            img_files += name + '_grid.svg ' + name + '_key.svg '
        if 'n' in save_format or 's' in save_format:
            self.clues_txt(name + '_clues.txt')
            img_files += name + '_clues.txt'
        if not gtkmode:
            print('The following files have been saved to your current working directory:\n' + img_files)

    def wrap(self, text, width=80):
        lines = []
        for paragraph in text.split('\n'):
            line = []
            len_line = 0
            for word in paragraph.split():
                len_word = len(word)
                if len_line + len_word <= width:
                    line.append(word)
                    len_line += len_word + 1
                else:
                    lines.append(' '.join(line))
                    line = [word]
                    len_line = len_word + 1
            lines.append(' '.join(line))
        return '\n'.join(lines)

    def word_bank(self): 
        temp_list = list(self.current_word_list)
        random.shuffle(temp_list)
        return 'Word bank\n' + ''.join(['{}\n'.format(word.word) for word in temp_list])
 
    def legend(self):
        outStrA, outStrD = '\nClues\nAcross\n', 'Down\n'
        for word in self.current_word_list:
            if word.vertical:
                outStrD += '{:d}. {}\n'.format(word.number, word.clue)
            else:
                outStrA += '{:d}. {}\n'.format(word.number, word.clue)
        return outStrA + outStrD
 
    def clues_txt(self, name):
        with open(name, 'w') as clues_file:
            clues_file.write(self.word_bank())
            clues_file.write(self.legend())

class Word(object):
    def __init__(self, word=None, clue=None):
        self.word = word.upper()
        self.clue = clue
        self.length = len(self.word)
        self.row = None
        self.col = None
        self.vertical = None
        self.number = None