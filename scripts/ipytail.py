"""ipytail.py - like tail, but for Jupyter notebooks.
"""
import sys
import json
import argparse

def markdown_cell(text):
    return {
        'cell_type': 'markdown',
        'source': text, 
        'metadata': {}
    }

class IPyTail:
    def __init__(self, max_cells=10, max_lines=25):
        self.max_cells = max_cells
        self.max_lines = max_lines

    def ipytail(self, filenames):
        notebooks = [self.process_file(f) for f in filenames]
        return self.merge(filenames, notebooks)

    def merge(self, filenames, notebooks):
        if len(notebooks) == 1:
            return notebooks[0]

        nb = dict(notebooks[0])

        def format_nb():		
            for title, n in zip(filenames, notebooks):
                yield markdown_cell("## ==> {} <==\n".format(title))
                yield from n['cells']

        nb['cells'] = list(format_nb())
        return nb

    def process_file(self, filename):
        nb = self.read_notebook(filename)
        nb = self.tail(nb, self.max_cells)
        nb = self.trim_notebook_outputs(nb, self.max_lines)
        return nb		

    def read_notebook(self, filename):
        return json.load(open(filename))

    def tail(self, notebook, n):
        cells = notebook['cells'][-n:]
        return dict(notebook, cells=cells)

    def trim_notebook_outputs(self, notebook, max_lines):
        cells = [self._trim_cell_outputs(cell, max_lines) for cell in notebook['cells']]
        return dict(notebook, cells=cells)

    def _trim_cell_outputs(self, cell, max_lines):
        """Limit the number of lines in each output of the cell to max_lines.

        A cell can contain multiple outputs, one for stdout, another for stderr
        and some other. This limits each output to max_lines. 
        """
        if 'outputs' not in cell:
            return cell
        outputs = [self._trim_output(output, max_lines) for output in cell.get('outputs', [])]
        return dict(cell, outputs=outputs)

    def _trim_output(self, output, max_lines):
        if 'text' in output and len(output['text']) > max_lines:		
            n = (max_lines+1) // 2
            head = output['text'][:n] 
            tail = output['text'][-n:]
            text = head + ['...\n'] + tail
            return dict(output, text=text)
        else:
            return output


def ipytail(filename, n=10, max_lines=0):
    """Returns a new notebook with last n entries from the notebook.

    If max_lines is specified, output of each cell is limited to
    so many rows.
    """
    notebook = json.loads(open(filename))
    notebook['cells'] = notebook['cells'][-n:]

    if max_lines > 0:
        for cell in notebook['cells']:
            limit_cell_output(cell, max_lines)
    return notebook

def parse_arguments():
    p = argparse.ArgumentParser()
    p.add_argument("-n", "--num-cells",
                   type=int, 
                   default=10,
                   help="Number of cells to include")

    p.add_argument("-l", 
                   dest="max_lines",
                   type=int,
                   default=25,
                   help="Maximum number of lines allowed in the cell output")
    p.add_argument("filenames", nargs="+")
    return p.parse_args()

def main():
    args = parse_arguments()

    ipytail = IPyTail(args.num_cells, args.max_lines)
    nb = ipytail.ipytail(args.filenames)
    print(json.dumps(nb, indent=True))

if __name__ == '__main__':
    main()