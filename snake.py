from tkinter import *
from math import floor, ceil
import random
from enum import Enum


class Game:
    def __init__(self, frame_rate=5, canvas_width=500,
        canvas_height=500, rows=20, columns=20, border_width=1,
        max_candy_age=25):
        # Game Board Info
        self.canvas_width = (canvas_width // rows) * rows
        self.canvas_height = (canvas_height // columns) * columns
        self.rows = rows
        self.columns = columns
        self.cell_width = self.canvas_width // self.columns
        self.cell_height = self.canvas_height // self.rows
        self.border_width = border_width
        self.frame_rate = frame_rate
        self.max_candy_age = max_candy_age

        # Game Info
        self.frame = 0
        self.score = 0
        self.snake = Snake(self, (columns // 2), (rows // 2))
        self.candies = []
        self.last_event = None

        # Set up Tk GUI
        self.root = Tk()
        self.restart_button = Button(self.root, text="Restart", command=self.reset)
        self.restart_button.pack()
        self.scorestring = StringVar(0)
        self.scoreboard = Label(self.root, textvariable=self.scorestring)
        self.scoreboard.pack()
        self.board = Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.board.pack()
        self.drawings = []

        # Monitor Keys
        self.root.bind("<Up>", self.keypress)
        self.root.bind("<Down>", self.keypress)
        self.root.bind("<Left>", self.keypress)
        self.root.bind("<Right>", self.keypress)

    def keypress(self, event):
        self.last_event = event

    def fill_cell(self, x, y, color="blue"):
        top = (self.cell_width * x) + self.border_width
        left = (self.cell_height * y) + self.border_width
        self.drawings.append(self.board.create_rectangle(
            top, left, top + self.cell_height - self.border_width,
            left + self.cell_width - self.border_width, fill=color))

    def reset(self):
        self.candies = []
        self.score = 0
        self.frame = 0
        self.snake = Snake(self, (self.columns // 2), (self.rows // 2))

    def exec(self):
        if self.last_event != None:
            self.snake.handle_input(self.last_event)
            self.last_event = None
        self.snake.exec(self.frame)

        for candy in self.candies:
            candy.exec()

        for x in range(len(self.candies)):
            if (self.snake.eat(self.candies[x]) or
                (self.candies[x].age > self.max_candy_age)):
                self.candies.pop(x)
                self.candies.append(Candy(self))

        if len(self.candies) < 3 and random.random() > 0.7:
            candy = Candy(self)
            self.candies.append(candy)

        self.frame += 1

    def get_unsafe_cells(self):
        unsafe = []
        occupied = []
        for candy in self.candies:
            occupied.append((candy.x, candy.y))

        for x,y in self.snake.blocks:
            occupied.append((x, y))

        for x,y in occupied:
            unsafe.append(self.wrap_around(x + 1, y))
            unsafe.append(self.wrap_around(x - 1, y))
            unsafe.append(self.wrap_around(x, y + 1))
            unsafe.append(self.wrap_around(x, y - 1))

        return set(unsafe + occupied)

    def wrap_around(self, x, y):
        if x >= self.columns:
            x = 0
        elif x < 0:
            x = self.columns - 1

        if y >= self.rows:
            y = 0
        elif y < 0:
            y = self.rows - 1

        return x, y

    def draw(self):
        self.scorestring.set(self.score)
        for drawing in self.drawings:
            self.board.delete(drawing)
        self.drawings = []
        self.snake.draw()
        for candy in self.candies:
            candy.draw()

    def cycle(self):
        self.draw()
        self.exec()
        self.root.after(ceil((1000/self.frame_rate)), self.cycle)


class Candy:
    class CandyType(Enum):
        cherry = 0
        poison = 1
        shrink = 2

    CandyTypeColors = {
        CandyType.cherry: 'red',
        CandyType.poison: 'black',
        CandyType.shrink: 'green'
    }

    def __init__(self, game, x=None, y=None, type=None):
        self.game = game
        unsafe_cells = self.game.get_unsafe_cells()
        if x is None:
            x = random.randrange(0, game.columns)
        if y is None:
            y = random.randrange(0, game.rows)

        while (x,y) in unsafe_cells:
            x = random.randrange(0, game.columns)
            y = random.randrange(0, game.rows)

        self.x = x
        self.y = y
        self.age = 0
        self.type = Candy.CandyType(random.randrange(0, len(Candy.CandyType)))

    def exec(self):
        self.age += 1

    def draw(self):
        self.game.fill_cell(self.x,self.y, Candy.CandyTypeColors[self.type])

class Snake:
    def __init__(self, game, x=0, y=0, dx=1, dy=0):
        self.length = 4
        self.blocks = [(x,y)]
        self.dx = dx
        self.dy = dy
        self.game = game
        self.dead = False

    def exec(self, frame):
        if self.dead:
            try:
                self.blocks.pop()
            except IndexError:
                pass

        else:
            head_x, head_y = self.blocks[0]
            while len(self.blocks) >= self.length:
                self.blocks.pop()

            head_x += self.dx
            head_y += self.dy

            self.blocks.insert(0, self.game.wrap_around(head_x, head_y))
            if self.test_collision():
                self.game.snake.die()

    def handle_input(self, event):
        if event.keysym == 'Up' and self.dy != 1:
            self.dx = 0
            self.dy = -1
        elif event.keysym == 'Down' and self.dy != -1:
            self.dx = 0
            self.dy = 1
        elif event.keysym == 'Right' and self.dx != -1:
            self.dx = 1
            self.dy = 0
        elif event.keysym == 'Left' and self.dx != 1:
            self.dx = -1
            self.dy = 0

    def eat(self, candy):
        if not self.dead:
            x, y = self.blocks[0]
            if ((candy.x == x) and
                (candy.y == y)):
                self.length += 1
                self.game.score += 1
                return True
        return False

    def test_collision(self):
        head_x, head_y = self.blocks[0]
        for x,y in self.blocks[1:]:
            if head_x == x and head_y == y:
                return True
        return False

    def die(self):
        self.dead = True
        print("You died")

    def draw(self):
        if len(self.blocks) > 0:
            self.game.fill_cell(*self.blocks[0], 'black')
        if len(self.blocks) > 1:
            for x,y in self.blocks[1:]:
                self.game.fill_cell(x,y, 'blue')

if __name__ == '__main__':
    game = Game()
    game.cycle()
    mainloop()