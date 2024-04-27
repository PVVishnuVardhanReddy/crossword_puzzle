import sys
from crossword import *
class CrosswordCreator():
    def __init__(self, crossword):
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }
    def letter_grid(self, assignment):
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters
    def print(self, assignment):
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()
    def save(self, assignment, filename):
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )
        img.save(filename)
    def solve(self):
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())
    def enforce_node_consistency(self):
        for variable in self.crossword.variables:
            for word in self.crossword.words:
                if len(word) != variable.length:
                    self.domains[variable].remove(word)
    def enforce_node_consistency(self):
        for variable in self.crossword.variables:
            self.domains[variable] = [word for word in self.domains[variable] if len(word) == variable.length]
    def revise(self, x, y):
        var1, var2 = self.crossword.overlaps[x, y]
        revised = False
        for x_word in set(self.domains[x]):
            valid_overlap = any(x_word[var1] == y_word[var2] for y_word in self.domains[y])
            if not valid_overlap:
                self.domains[x].remove(x_word)
                revised = True
        return revised  
    def ac3(self, arcs=None):       
        if arcs is None:
            arcs = []
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    arcs.append((x,y))
        while arcs:
            (x,y) = arcs.pop()
            if self.revise(x,y):
                if not self.domains[x]:
                    return False                
                for z in self.crossword.neighbors(x) - set(self.domains[y]):
                    arcs.append((z,x))
        return True
    def assignment_complete(self, assignment):
        for variable in self.crossword.variables:

            if variable not in assignment.keys():
                return False            
            if not assignment.get(variable):
                return False           
        return True
    def consistent(self, assignment): 
        for x_1 in assignment:
            word = assignment.get(x_1)
            if len(word) != x_1.length:
                return False
            for x_2 in assignment:
                word2 = assignment.get(x_2)
                if x_1 != x_2:
                    if word == word2:
                        return False
                    overlap = self.crossword.overlaps[x_1, x_2]
                    if overlap:
                        a, b = overlap
                        if word[a] != word2[b]:
                            return False
        return True
    def order_domain_values(self, var, assignment):
        results = {}
        for i in self.domains[var]:
            results[i] = 0
            for neighbor in self.crossword.neighbors(var) - assignment.keys():
                if i in self.domains[neighbor]:
                    results[i] += 1 
        return sorted(results, key=results.get)
    def select_unassigned_variable(self, assignment):
        unassigned_vars = [var for var in self.crossword.variables if var not in assignment]
        if not unassigned_vars:
            return None
        variable = min(unassigned_vars, key=lambda var: (len(self.domains[var]), -len(self.crossword.neighbors(var))))
        return variable
    def backtrack(self, assignment):
        if self.assignment_complete(assignment):
            return assignment        
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            assignment[var] = None
        return None    
def main():
    if len(sys.argv) not in [2, 3]:
        sys.exit("Usage: python generate.py structure words [output]")
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)
if __name__ == "__main__":
    main()