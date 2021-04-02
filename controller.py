from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from statistics import mean
import tkinter as tk
import tkinter.ttk as ttk
from turtle import Turtle
import matplotlib
matplotlib.use('TkAgg')


class MouseClick:
    def __init__(self, master, nodes):
        # store root
        self.root = master
        # create a popup menu
        self.aMenu = tk.Menu(master, tearoff=0)
        self.aMenu.add_command(label='Show coverage',
                               command=self.show_coverage)
        self.aMenu.add_command(label='Show neighbours',
                               command=self.show_neighbors)
        self.aMenu.add_command(label='Show reachables',
                               command=self.show_tx_reachables)
        self.aMenu.add_separator()
        self.aMenu.add_command(label='Hide coverages',
                               command=self.hide_coverage)
        self.aMenu.add_command(label='Hide neighbors',
                               command=self.hide_neighbors)

        # reduced menu created for empty clicks
        self.bMenu = tk.Menu(master, tearoff=0)
        self.bMenu.add_command(label='Show all neighbours',
                               command=self.show_all_neighbors)
        self.bMenu.add_separator()
        self.bMenu.add_command(label='Clear all',
                               command=self.hide_all_coverages)

        self.nodes = nodes
        self.turs = [self.setup_turtles() for _ in range(len(self.nodes))]
        self.focus_node = None

    def setup_turtles(self):
        tur = Turtle()
        tur.pu()
        tur.ht()
        tur.color("saddle brown")
        tur.pensize(2)
        return tur

    def show_coverage(self):
        # self.focus_node.show_coverage()
        i, n = self.focus_node
        tur = self.turs[i]
        tur.goto(n.xcor(), n.ycor() - n.coverage)
        tur.setheading(0)
        tur.pendown()
        tur.circle(n.coverage)
        tur.penup()
        tur.goto(n.pos())

    def hide_coverage(self):
        # self.focus_node.hide_coverage()
        i, _ = self.focus_node
        tur = self.turs[i]
        tur.pendown()
        tur.clear()
        tur.penup()

    def hide_all_coverages(self):
        for tur in self.turs:
            tur.pendown()
            tur.clear()
            tur.penup()

    def show_neighbors(self):
        _, tx_node = self.focus_node
        rx_nodes = tx_node.get_neighbors()
        # draw arrow for all neighbors
        for rx_node in rx_nodes:
            snd_pckt = self.turs[rx_node.node_id]
            snd_pckt.setposition(tx_node.pos())
            snd_pckt.setheading(snd_pckt.towards(rx_node.pos()))
            snd_pckt.fd(11)
            snd_pckt.pendown()
            snd_pckt.fd(rx_node.distance(snd_pckt) - 11)

            # Drawing arrow head
            snd_pckt.left(45)
            snd_pckt.backward(10)
            snd_pckt.forward(10)
            snd_pckt.right(90)
            snd_pckt.backward(10)
            snd_pckt.penup()

    def hide_neighbors(self):
        _, tx_node = self.focus_node
        rx_nodes = tx_node.get_neighbors()
        # draw arrow for all neighbors
        for rx_node in rx_nodes:
            self.turs[rx_node.node_id].clear()

    def show_all_neighbors(self):
        for n in self.nodes:
            self.focus_node = (n.node_id, n)
            self.show_neighbors()

    def show_tx_reachables(self):
        reachables = []
        for node in self.nodes:
            if self.focus_node[0] in [n.node_id for n in node.get_neighbors()]:
                reachables.append((node.node_id, node))

        i, node = self.focus_node
        for i_n, n in reachables:
            snd_pckt = self.turs[i_n]
            snd_pckt.setposition(n.pos())
            snd_pckt.setheading(snd_pckt.towards(node.pos()))
            snd_pckt.fd(11)
            snd_pckt.pendown()
            snd_pckt.fd(node.distance(snd_pckt) - 11)

            # Drawing arrow head
            snd_pckt.left(45)
            snd_pckt.backward(10)
            snd_pckt.forward(10)
            snd_pckt.right(90)
            snd_pckt.backward(10)
            snd_pckt.penup()

    def popup(self, x, y):
        # remove other menu lists
        self.aMenu.unpost()
        self.bMenu.unpost()

        # get curser tkk position
        x_root = self.root.winfo_pointerx()
        y_root = self.root.winfo_pointery()

        # if click on node
        if self.get_node((x, y)):
            self.aMenu.post(x_root, y_root)
        else:
            self.bMenu.post(x_root, y_root)

    def get_node(self, pos):
        dis = [n.distance(pos) for n in self.nodes]
        nearest_node = self.nodes[dis.index(min(dis))]
        self.focus_node = (dis.index(min(dis)), nearest_node) if (
            min(dis) < 15) else None
        return self.focus_node

    def left_click(self, x, y):
        self.aMenu.unpost()
        self.bMenu.unpost()
        x_root = self.root.winfo_pointerx()
        y_root = self.root.winfo_pointery()
        if self.get_node((x, y)):
            self.focus_node = self.get_node((x, y))


class Controller:
    def __init__(self, master, num_nodes):
        self.root = master
        self.num_nodes = num_nodes

        # Create tools window
        tools = tk.Toplevel(self.root, padx=10, pady=10)
        tools.wm_title("Tools")

        # Create pane
        p = ttk.Panedwindow(tools, orient=tk.HORIZONTAL)
        p.pack(fill=tk.BOTH, expand=1)

        # two panes, each of which would get widgets into it:
        self.ctrlr = ttk.Labelframe(p, text='Controller')
        self.anlys = ttk.Labelframe(p, text='Analysis')
        p.add(self.ctrlr)
        p.add(self.anlys)

        # Analysis tabs
        n = ttk.Notebook(self.anlys)
        self.summ_frame = ttk.Frame(n)   # first page
        self.aod_grph_frame = ttk.Frame(n)   # second page
        self.ranks_grph_frame = ttk.Frame(n)   # third page
        n.add(self.summ_frame, text='Statistics')
        n.add(self.aod_grph_frame, text='AoD Graph')
        n.add(self.ranks_grph_frame, text='Ranks Graph')
        n.pack(fill=tk.BOTH, expand=1)

        self.avg_rank = []

        self.create_controller()
        self.aod_ax, self.aod_canvas = self.create_graph(self.aod_grph_frame)
        self.ranks_ax, self.ranks_canvas = self.create_graph(
            self.ranks_grph_frame)
        self.create_analysis(self.summ_frame)

    def create_graph(self, root):
        fig, ax = plt.subplots()

        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()
        return (ax, canvas)

    def create_analysis(self, master):
        # tk.Label(master, text="Current Status:").pack(side=tk.TOP)
        headers = ["Max AoD:", "Avg AoD:", "Nodes 100%:", "Nodes <50%"]
        vals = [0 for _ in range(self.num_nodes)]
        ranks = [(0, 0, 0, 0, 0) for _ in range(self.num_nodes)]
        self.lbl_headers = tk.Label(master)
        self.lbl_headers.config(
            font='{Fira Sans} 12 {bold}', text=("\n".join(headers)))
        self.lbl_headers.pack(side=tk.LEFT, pady=10, padx=5, fill=tk.BOTH)

        self.lbl_vals = tk.Label(master)
        self.lbl_vals.pack(side=tk.LEFT, pady=10, padx=5, fill=tk.BOTH)
        self.update_analysis(vals, ranks, 0, 0)

    def update_analysis(self, vals, ranks, r_num, r_xtra=0):
        arr = np.array(vals)
        _ranks, *_ = zip(*ranks)
        self.avg_rank.append(mean(_ranks))

        f_dn = len(arr[arr == 100]) if arr[arr == 100].any() else 0
        h_dn = len(arr[arr <= 50]) if arr[arr <= 50].any() else 0
        values = [f"{arr.max():.2f}%", f"{arr.mean():.2f}%",
                  f"{f_dn}/{self.num_nodes}", f"{h_dn}/{self.num_nodes}"]
        self.lbl_vals.config(font='{Fira Sans} 11', text=("\n".join(values)))

        self.update_graph(arr, r_num, self.aod_ax, self.aod_canvas)
        self.update_ranks_graph(self.avg_rank, r_num, r_xtra,
                                self.ranks_ax, self.ranks_canvas)
        # print(ranks)

    def update_graph(self, arr, round_no, ax, canvas):
        # Graphs update
        n_range = [*range(self.num_nodes)]
        ax.clear()         # clear axes from previous plot
        ax.set_title(
            f'Availability of data for {self.num_nodes} nodes @ tx {round_no}')
        ax.set_xlabel('Nodes')
        ax.set_xticks(n_range)
        ax.set_ylabel('Availability of Data percentage (%)')
        ax.set_ylim(0, 100)     # set the ylim to bottom, top
        ax.bar(n_range, arr)
        canvas.draw()

    def update_ranks_graph(self, arr, r_num, r_xtra, ax, canvas):
        round_no = r_num + r_xtra
        x_range = np.arange(0, round_no+1)
        # Graphs update
        ax.clear()         # clear axes from previous plot
        ax.plot(arr)
        ax.set_title(f'Avg {self.num_nodes} decoder ranks vs num of tx')
        ax.set_xlabel(f'Num of {round_no} txs')
        ax.set_xlim(0, round_no)
        ax.set_xticks(x_range)
        ax.set_ylabel('Avg decoders rank')
        # set the ylim to bottom, top
        ax.set_yticks(np.arange(self.num_nodes+1))
        ax.margins(x=0)
        ax.grid()
        # Add horizontal lines
        ax.axhline(self.num_nodes, label="max rank", ls='--', color='r')
        # Add a vertical lines
        if r_xtra:
            ax.axvline(r_num, label=f"tx = {r_num}", ls=':', color='r')
            ax.axhline(np.interp(r_num, x_range[:-1], arr),
                       label=f"rank @ tx {r_num}", ls='--', color='gray')
        if self.num_nodes in arr:
            index = np.searchsorted(arr, self.num_nodes)
            ax.axvline(index, label="full AoD", ls='--', color='g')
        ax.legend(loc='upper left')
        canvas.draw()
        # print("done")

    def clear_rank(self):
        self.avg_rank = []

    def create_controller(self):
        # Radio buttons
        # Container for Radio buttons
        tk.Label(self.ctrlr, text='methods:', anchor='w').pack(pady=(10, 0))
        # Radio variable
        self.cont_run = tk.IntVar()
        self.cont_run.set(3)
        self.R1 = tk.Radiobutton(self.ctrlr, text="Run all",
                                 variable=self.cont_run, value=0,
                                 command=self.dis_btns)
        self.R1.pack(anchor=tk.W)

        self.R2 = tk.Radiobutton(self.ctrlr, text="Stop @ generations",
                                 variable=self.cont_run, value=1,
                                 command=lambda: self.enable_nxt_btn('gen'))
        self.R2.pack(anchor=tk.W)

        self.R3 = tk.Radiobutton(self.ctrlr, text="Stop @ rounds",
                                 variable=self.cont_run, value=2,
                                 command=lambda: self.enable_nxt_btn('rnd'))
        self.R3.pack(anchor=tk.W)

        ttk.Separator(self.ctrlr, orient='horizontal').pack(
            side='top', fill='x', pady=10)

        # NEXT Push buttons
        self.is_nxt = tk.BooleanVar(value=False)
        self.btn_nxt_gen = tk.Button(
            self.ctrlr, text="Next generation", width=15,
            command=self.nxt_clicked)
        self.btn_nxt_gen['state'] = 'disabled'
        self.btn_nxt_gen.pack()

        self.btn_nxt_rnd = tk.Button(
            self.ctrlr, text="Next round", width=15,
            command=self.nxt_clicked)
        self.btn_nxt_rnd['state'] = 'disabled'
        self.btn_nxt_rnd.pack()

        ttk.Separator(self.ctrlr, orient='horizontal').pack(
            side='top', fill='x', pady=10)

        # EXTRA push buttons
        self.btn_xtr_gen = tk.Button(
            self.ctrlr, text="Extra generation", width=15)
        self.btn_xtr_gen['state'] = 'disabled'
        self.btn_xtr_gen.pack()

        self.btn_xtr_rnd = tk.Button(
            self.ctrlr, text="Extra round",  width=15)
        self.btn_xtr_rnd['state'] = 'disabled'
        self.btn_xtr_rnd.pack()

        ttk.Separator(self.ctrlr, orient='horizontal').pack(
            side='top', fill='x', pady=10)

        # footer buttons
        self.btn_to_full = tk.Button(
            self.ctrlr, text="Full AoD",  width=15)
        self.btn_to_full['state'] = 'disabled'
        self.btn_to_full.pack()

        btn_ext = tk.Button(self.ctrlr, text="Exit app", width=15,
                            command=self.root.destroy)
        btn_ext.pack()

    def dis_btns(self, dis_all=False):
        self.btn_nxt_gen['state'] = 'disabled'
        self.btn_nxt_rnd['state'] = 'disabled'
        if dis_all:
            self.R1.configure(state=tk.DISABLED)
            self.R2.configure(state=tk.DISABLED)
            self.R3.configure(state=tk.DISABLED)

    def dis_rnd(self):
        self.R3.configure(state=tk.DISABLED)

    def enb_rnd(self):
        self.R3.configure(state=tk.NORMAL)

    def enable_nxt_btn(self, btn):
        if btn == "gen":
            self.btn_nxt_gen['state'] = 'normal'
            self.btn_nxt_rnd['state'] = 'disabled'
        else:
            self.btn_nxt_gen['state'] = 'disabled'
            self.btn_nxt_rnd['state'] = 'normal'

    def is_continuous_run(self):
        return self.cont_run.get()

    def nxt_clicked(self):
        self.is_nxt.set(True)

    def is_nxt_clicked(self):
        return self.is_nxt.get()

    def post_click(self):
        self.is_nxt.set(False)

    def get_xtr_btns(self):
        return [self.btn_xtr_gen, self.btn_xtr_rnd, self.btn_to_full]
