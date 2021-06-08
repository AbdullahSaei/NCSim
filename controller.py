from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.ttk as ttk
from turtle import Turtle
import matplotlib

plt.style.use('seaborn-deep')
matplotlib.use('TkAgg')


def setup_turtles():
    tur = Turtle()
    tur.pu()
    tur.ht()
    tur.color("saddle brown")
    tur.pensize(2)
    return tur


def draw_arrow(snd_pckt):
    # Drawing arrow head
    snd_pckt.left(45)
    snd_pckt.backward(10)
    snd_pckt.forward(10)
    snd_pckt.right(90)
    snd_pckt.backward(10)
    snd_pckt.penup()


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
        self.turs = [setup_turtles() for _ in range(len(self.nodes))]
        self.focus_node = None

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

            draw_arrow(snd_pckt)

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

            draw_arrow(snd_pckt)

    def popup(self, x, y):
        # remove other menu lists
        self.aMenu.unpost()
        self.bMenu.unpost()

        # get cursor tkk position
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
        # x_root = self.root.winfo_pointerx()
        # y_root = self.root.winfo_pointery()
        if self.get_node((x, y)):
            self.focus_node = self.get_node((x, y))


def create_graph(root):
    fig, ax = plt.subplots()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    canvas.draw()
    return ax, canvas


def display_data(frame, values, headers=None, assert_empty=False):
    # check if frame is empty
    if assert_empty and frame.winfo_children():
        return False
    elif frame.winfo_children():
        lbl_headers, lbl_vals = frame.winfo_children()
    else:
        lbl_headers = tk.Label(frame)
        lbl_vals = tk.Label(frame)

    # Create header
    if headers:
        lbl_headers.config(
            font='{Fira Sans} 12 {bold}', text=("\n".join(
                map(lambda s: f"{s.replace('_', ' ')}:", headers)
            )))
        lbl_headers.pack(side=tk.LEFT, pady=10, padx=5, fill=tk.BOTH)

    # Create values label
    lbl_vals.config(font='{Fira Sans} 12', text=(
        "\n".join(map(str, values))))
    lbl_vals.pack(side=tk.LEFT, pady=10, padx=5, fill=tk.BOTH)


class Controller:
    def __init__(self, master, summ_header, auto_run, auto_full, **configs):
        self.root = master
        self.summ_header = summ_header
        self.configs = configs
        self.num_nodes = int(configs.get("num_nodes", 0))

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
        self.stat_frame = ttk.Frame(n)  # first page
        self.aod_grph_frame = ttk.Frame(n)  # second page
        self.ranks_grph_frame = ttk.Frame(n)  # third page
        self.summ_frame = ttk.Frame(n)  # forth page
        n.add(self.stat_frame, text='Statistics')
        n.add(self.aod_grph_frame, text='AoD Graph')
        n.add(self.ranks_grph_frame, text='Ranks Graph')
        n.add(self.summ_frame, text='KPIs')
        n.pack(fill=tk.BOTH, expand=1)

        self.new_generation_cleanup(clear_frames=False)
        self.create_controller(auto_run=auto_run, auto_full=auto_full)
        self.aod_ax, self.aod_canvas = create_graph(self.aod_grph_frame)
        self.ranks_ax, self.ranks_canvas = create_graph(
            self.ranks_grph_frame)
        self.create_analysis(self.stat_frame)

    def create_summ_tree(self, root):
        # taking all the columns heading in a variable "df_col".
        df = self.df_nodes
        df_col = df.columns.values

        # create scrollbar
        scroll = ttk.Scrollbar(root)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        # create tree view
        tree = ttk.Treeview(root, show='headings', height=7,
                            yscrollcommand=scroll.set)
        scroll.config(command=tree.yview)
        # all the column name are generated dynamically.
        tree['columns'] = df_col

        # generating for loop to create columns and give heading to them through df_col var.
        for col, x in enumerate(df_col):
            tree.column(col, width=50, anchor='e')
            tree.heading(col, text=x.replace('_', ' '),
                         command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
        tree.pack(expand=True, fill=tk.BOTH)
        return tree

    def update_summ_tree(self, tree, data):
        if data:
            df = pd.DataFrame(data)
            color = "#" + ("%06x" % np.random.randint(12000000, 13000000))
            # generating for loop to add new values to tree
            for _, row in df.iterrows():
                vals = list(map(int, row.tolist()))

                # generating for loop to print values of dataframe in treeview column.
                tree.insert('', 0, values=vals, tags=color)
                tree.tag_configure(color, background=color)

            self.df_nodes = self.df_nodes.append(df, ignore_index=True)

    def create_analysis(self, master):
        # Create paned windows
        all_pane = ttk.PanedWindow(master, orient=tk.VERTICAL)
        top_pane = ttk.PanedWindow(all_pane, orient=tk.HORIZONTAL)
        bottom_pane = ttk.PanedWindow(all_pane, orient=tk.HORIZONTAL)

        # Create top label frames
        self.f_config = ttk.Labelframe(top_pane, text='Configurations')
        self.f_current = ttk.Labelframe(top_pane, text='Current run')

        # Show Configurations to reserve size
        display_data(self.f_config, list(self.configs.values()),
                     list(self.configs.keys()))
        top_pane.add(self.f_config, weight=20)
        top_pane.add(self.f_current, weight=52)
        # top_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create bottom pane
        rnds = self.configs.get("num_rounds", 1)
        self.f_at_tx = ttk.Labelframe(bottom_pane, text=f'@ tx = {rnds}')
        self.f_at_100 = ttk.Labelframe(
            bottom_pane, text='@ all nodes 100% AoD')
        bottom_pane.add(self.f_at_tx, weight=20)
        bottom_pane.add(self.f_at_100, weight=31)

        # add panes to all_pane
        all_pane.add(top_pane)
        all_pane.add(bottom_pane)
        all_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create Header and Tx data
        self.headers_current = ["Round", "Avg Ranks", "Avg AoD",
                                "Max AoD", "Min AoD", "Nodes 100%", "Nodes <50%"]
        vals = [0 for _ in range(self.num_nodes)]
        ranks = [(1, 1, 1) for _ in range(self.num_nodes)]
        stats = None
        self.data = [vals, ranks, stats]
        # Show data
        display_data(self.f_current, vals, self.headers_current)
        self.update_analysis(self.data)

    def update_analysis(self, data, r_curr=0, r_num=0, r_xtra=0):
        self.data = data
        # Extract data
        vals, ranks, stats = data

        # prepare data
        arr = np.array(vals)
        s_rank, g_rank, h_rank = zip(*ranks)
        avg_ranks = np.mean(s_rank)
        self.avg_rank.append(avg_ranks)

        # Calculate full done and half done nodes
        f_dn = len(arr[arr == 100]) if arr[arr == 100].any() else 0
        h_dn = len(arr[arr <= 50]) if arr[arr <= 50].any() else 0

        # headers_current = ["Round", "Avg Ranks",
        # "Max AoD", "Avg AoD", "Nodes 100%", "Nodes <50%"]
        run_values = [f"{r_curr}/{r_num}", f"{avg_ranks:.2f}/{self.num_nodes}",
                      f"{arr.mean():.2f}%", f"{np.max(arr):.2f}%", f"{np.min(arr):.2f}%",
                      f"{f_dn}/{self.num_nodes}", f"{h_dn}/{self.num_nodes}"]
        display_data(self.f_current, run_values)

        # Show message if it is the specified round
        if r_curr and not r_xtra and r_curr == r_num:
            # snapshot the current results for that round
            headers = self.headers_current[1:]
            display_data(self.f_at_tx, run_values[1:], headers)

        # update other GUIs
        self.update_summ_tree(self.summ_tree, stats)
        self.update_hist_graph(arr, r_num, self.aod_ax, self.aod_canvas)
        self.update_ranks_graph(self.avg_rank, r_curr, r_num, r_xtra,
                                self.ranks_ax, self.ranks_canvas)

    def update_hist_graph(self, arr, round_no, ax, canvas):
        # Graphs update
        n_range = [*range(self.num_nodes)]
        ax.clear()  # clear axes from previous plot
        ax.set_title(
            f'Availability of data for {self.num_nodes} nodes @ tx {round_no}')
        ax.set_xlabel('Nodes')
        ax.set_xticks(n_range)
        ax.set_ylabel('Availability of Data percentage (%)')
        ax.set_ylim(0, 100)  # set the y lim to bottom, top
        ax.bar(n_range, arr)
        canvas.draw()

    def update_ranks_graph(self, arr, r_current, r_num, r_xtra, ax, canvas):
        round_no = r_num + r_xtra
        x_range = np.arange(0, round_no + 1)
        # Graphs update
        ax.clear()  # clear axes from previous plot
        ax.plot(arr)
        ax.set_title(
            f'Average ranks of {self.num_nodes} decoders Vs num of transmissions')
        ax.set_xlabel(f'Num of transmissions {r_current}')
        ax.set_xticks(x_range)
        ax.set_ylabel('Avg ranks of decoders')
        # set the y lim to bottom, top
        ax.set_yticks(np.arange(self.num_nodes + 1))
        ax.margins(x=0)
        ax.grid()
        # Add horizontal lines
        ax.axhline(self.num_nodes, label="max rank", ls='--', color='r')
        # Add a vertical lines
        if r_num and r_current >= r_num:
            ax.axvline(r_num, label=f"tx = {r_num}", ls=':', color='r')
            ax.axhline(np.interp(r_num, x_range, arr),
                       label=f"rank @ tx {r_num}", ls='--', color='gray')
        if self.num_nodes in arr:
            index = np.searchsorted(arr, self.num_nodes)
            ax.axvline(index, label="full AoD", ls='--', color='g')
            self.show_full_aod_stats(r_current)

        ax.legend(loc='lower right')
        canvas.draw()

    def show_full_aod_stats(self, r_curr):
        # check if frame is empty
        if self.f_at_100.winfo_children():
            return False
        # prepare data
        rnds = self.configs.get("num_rounds", 0)
        df = self.df_nodes.query(f" round == {r_curr}")

        # Calculate ratio
        reception_ratio = df['rx_success'].sum() / df['rx_total'].sum() * 100
        collision_ratio = df['rx_collisions'].sum() / \
            df['rx_total'].sum() * 100
        ignored_ratio = df['rx_ignored'].sum() / df['rx_total'].sum() * 100
        missed_ratio = df['rx_missed'].sum() / df['rx_total'].sum() * 100
        pathloss_ratio = df['rx_SINR_loss'].sum() / df['rx_total'].sum() * 100

        # Create header
        headers = ["Num of rounds", "Expected rounds", "Reception success %",
                   "Collision %", "Ignored msgs %", "Missed msgs %", "SINR loss %"]
        # Values format
        values = [f"{r_curr}", f"{rnds}", f"{reception_ratio:.2f}%",
                  f"{collision_ratio:.2f}%", f"{ignored_ratio:.2f}%",
                  f"{missed_ratio:.2f}%", f"{pathloss_ratio: .2f}%"]

        # display values
        display_data(self.f_at_100, values, headers)

    def treeview_sort_column(self, tv, col, reverse):
        l = [(int(tv.set(k, col)), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(col, command=lambda _col=col: self.treeview_sort_column(
            tv, _col, not reverse))

    def new_generation_cleanup(self, clear_frames=True):
        # Clean up
        self.avg_rank = []

        # Clear dataframe
        self.df_nodes = pd.DataFrame(columns=self.summ_header)

        # clear frames
        if clear_frames:
            frames = [self.f_at_100, self.summ_frame, self.f_at_tx]
            for frame in frames:
                # destroy all widgets from frame
                for widget in frame.winfo_children():
                    widget.destroy()

        # create clean frame
        self.summ_tree = self.create_summ_tree(self.summ_frame)

    def create_controller(self, auto_run, auto_full):
        # Radio buttons
        # Container for Radio buttons
        tk.Label(self.ctrlr, text='methods:', anchor='w').pack(pady=(10, 0))
        # Radio variable
        self.cont_run = tk.IntVar()
        if not auto_run:
            self.cont_run.set(3)
        else:
            self.cont_run.set(0)
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

        # Checkbox variable
        self.auto_full = tk.BooleanVar()
        if auto_full:
            self.auto_full.set(True)
        else:
            self.auto_full.set(False)
        self.CB1 = tk.Checkbutton(self.ctrlr, text="Run until full Aod",
                                  variable=self.auto_full, onvalue=True, offvalue=False)
        self.CB1.pack(anchor=tk.W)

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
            self.ctrlr, text="Extra round", width=15)
        self.btn_xtr_rnd['state'] = 'disabled'
        self.btn_xtr_rnd.pack()

        ttk.Separator(self.ctrlr, orient='horizontal').pack(
            side='top', fill='x', pady=10)

        # footer buttons
        self.btn_to_full = tk.Button(
            self.ctrlr, text="Full AoD", width=15)
        self.btn_to_full['state'] = 'disabled'
        self.btn_to_full.pack()

        btn_ext = tk.Button(self.ctrlr, text="Exit app", width=15,
                            command=self.close_window)
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

    def is_run_to_full(self):
        return self.auto_full.get()

    def nxt_clicked(self):
        self.is_nxt.set(True)

    def is_nxt_clicked(self):
        return self.is_nxt.get()

    def post_click(self):
        self.is_nxt.set(False)

    def get_xtr_btns(self):
        return [self.btn_xtr_gen, self.btn_xtr_rnd, self.btn_to_full]

    def close_window(self):
        try:
            self.root.destroy()
            self.root.quit()
        except Exception as e:
            print(e)
            print("bye bye")
