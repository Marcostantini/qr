from random import randint
import networkx as nx
import matplotlib.pyplot as plt
import os

import warnings
warnings.filterwarnings("ignore")

variables = ['Inflow', 'Volume', 'Outflow']

possible_amounts = {'Inflow': [0,1], 'Volume': [0,1,2], 'Outflow': [0,1,2]}
possible_ders = {'Inflow': [-1,0,1], 'Volume': [-1,0,1], 'Outflow': [-1,0,1]}
amount_dict = {0: 'zero', 1: 'positive', 2: 'max'}
der_dict = {-1: 'negative', 0: 'zero', 1: 'positive'}

class State:
    def __init__(self, values, num = -1):
        self.inflow_amount = values[0]
        self.inflow_der = values[1]
        self.volume_amount = values[2]
        self.volume_der = values[3]
        self.outflow_amount = values[4]
        self.outflow_der = values[5]
        # self.num will be set depending on the position of this state in the states list
        self.num = num
        self.links = []
        self.intra_state_trace = ""
        self.inter_state_trace = ""

    def set_num(self, num):
        self.num = num

    def add_link(self, num):
        if num not in self.links:
            self.links.append(num)

    def set_inflow_der(self, der):
        self.inflow_der = der

    def to_list(self):
        return [self.inflow_amount, self.inflow_der, self.volume_amount, self.volume_der, self.outflow_amount, self.outflow_der]

    def compare(self, other):
        equal = False
        if self.to_list() == other.to_list():
            equal = True
        return equal

    def __str__(self):
        """ A human-readable string representation of the state.
        Intended to be used for the trace output.
        """
        inflow_astr = amount_dict[self.inflow_amount]
        inflow_dstr = der_dict[self.inflow_der]
        volume_astr = amount_dict[self.volume_amount]
        volume_dstr = der_dict[self.volume_der]
        outflow_astr = amount_dict[self.outflow_amount]
        outflow_dstr = der_dict[self.outflow_der]

        return (
            "\nThe inflow is " + inflow_astr + " and has a " + inflow_dstr + " derivative.\n" +
            "\nThe volume is " + volume_astr + " and has a " + volume_dstr + " derivative.\n" +
            "\nThe outflow is " + outflow_astr + " and has a " + outflow_dstr + " derivative.\n")

def in_states(states, test_state):
    in_states = False
    for state in states:
        if state.compare(test_state):
            in_states = True
    return in_states

def state_index(states, test_state):
    index = 0
    while index < len(states):
        if states[index].compare(test_state):
            break;
        else: index += 1
    return index

def prune_transitions(trace, states):
    n_states = len(states) - 1
    idx = trace.index(str(n_states))
    extra = trace[idx + 1:]
    last = extra.index("hrulefill")
    return trace[:idx+last-1]

def generate_states(init = State([0,0,0,0,0,0], 0)):
    complete_trace = ""
    trace_is_complete = False
    states = [init]
    current_state = 0
    # these are the derivatives to be applied to the inflow in cycle
    inflow_der_cycle = [0,1,0,-1]
    inflow_der = 0
    exo_steps = 0
    der = 1
    set_up_steps = 100
    iterations = 1000
    while exo_steps < iterations:
        # current number of states
        current_nos = len(states)
        # use the last state generated but change the inflow derivative
        new_state = State(states[current_state].to_list())
        der = inflow_der_cycle[inflow_der % len(inflow_der_cycle)]
        if der != 0 and der == -new_state.inflow_der:
            inflow_der += 1
            der = inflow_der_cycle[inflow_der % len(inflow_der_cycle)]
        if new_state.inflow_amount == 0 and der == -1:
            der = 0
        new_state.set_inflow_der(der)
        # if such state is new it gets added to the list of states
        if not in_states(states, new_state) and exo_steps <= set_up_steps:
            new_state.set_num(len(states))
            states[current_state].add_link(new_state.num)
            states.append(new_state)
            current_state = new_state.num
        # if it's a known states it gets linked to the current state because it's in the current state reach
        elif in_states(states, new_state) and current_state != state_index(states, new_state):
            states[current_state].add_link(state_index(states, new_state))
            current_state = state_index(states, new_state)
        stop = False
        while not stop:
            # a new state is generated following the rules in test_step()
            test_state, state_trace = test_step(states[current_state])
            if not trace_is_complete:
                complete_trace += state_trace
            # if it's a new states it gets added to the list of states and the loop terminates to allow a change in the inflow derivative
            if not in_states(states, test_state) and exo_steps <= set_up_steps:
                test_state.set_num(len(states))
                states[current_state].add_link(test_state.num)
                states.append(test_state)
                current_state = test_state.num
                stop = True
            # if it's a known states it gets linked to the current state because it's in the current state reach
            elif in_states(states, test_state) and current_state != state_index(states, test_state):
                states[current_state].add_link(state_index(states, test_state))
                current_state = state_index(states, test_state)
            # if the test_state is the same as the last state visited the while loop stops
            else: stop = True
        # if no states have been added the exo_steps counter increases
        if current_nos == len(states):
            exo_steps += 1
        # if a new state has been found the exo_steps counter is set to 0
        else:
            exo_steps = 0
        # change in the inflow derivative
        inflow_der += 1
        # after set_up_steps the current state is randomly picked from the states generated
        if exo_steps > set_up_steps:
            current_state = randint(0, len(states)-1)
    
    print("The following states were generated:")
    for i, state in enumerate(states):
        print(str(i) + ": " + str(state.to_list()))
    print("Transitions between states:")
    for i, state in enumerate(states):
        print(str(i) + ": " + str(state.links))
    return states, prune_transitions(complete_trace, states)

def test_step(state):    
    intra_state_trace = ""
    inter_state_trace = ""

    test_state = State(state.to_list())

    # volume positive derivative changes volume amount
    if state.volume_der == 1:
        inter_state_trace += "\n\\item The volume's derivative is positive, so it must increase."
        test_state.volume_amount = min(test_state.volume_amount + 1, max(possible_amounts['Volume']))
    # outflow positive derivative changes outflow amount
    if state.outflow_der == 1:
        inter_state_trace += "\n\\item The outflow's derivative is positive, so it must increase."
        test_state.outflow_amount = min(test_state.outflow_amount + 1, max(possible_amounts['Outflow']))
    # volume negative derivative changes volume amount
    if state.volume_der == -1:
        inter_state_trace += "\n\\item The volume's derivative is negative, so it must decrease."
        test_state.volume_amount = max(test_state.volume_amount - 1, min(possible_amounts['Volume']))
    # outflow negative derivative changes outflow amount
    if state.outflow_der == -1:
        inter_state_trace += "\n\\item The outflow's derivative is negative, so it must decrease."
        test_state.outflow_amount = max(test_state.outflow_amount - 1, min(possible_amounts['Outflow']))

    # outflow amount influences volume derivative
    if test_state.outflow_amount >= 1 and test_state.inflow_amount < 1:
        intra_state_trace += "\n\\item The outflow is positive, so the volume's derivative must decrease."
        test_state.volume_der = max(test_state.volume_der - 1, min(possible_ders['Volume']))        
    # inflow amount influences volume derivative
    if test_state.inflow_amount >= 1:
        intra_state_trace += "\n\\item The inflow is positive, so the volume's derivative must increase."
        test_state.volume_der = min(test_state.volume_der + 1, max(possible_ders['Volume']))
    if test_state.outflow_der != test_state.volume_der:
        intra_state_trace += "\n\\item The volume's derivative must be equal to the outflow's derivative."
        # outflow derivative is equal to volume derivative
        test_state.outflow_der = test_state.volume_der    

    # inflow positive derivative changes inflow amount
    if state.inflow_der == 1:
        inter_state_trace += "\n\\item The inflow's derivative is positive, so it must increase."
        test_state.inflow_amount = min(test_state.inflow_amount + 1, max(possible_amounts['Inflow']))
    # inflow negative derivative changes inflow amount
    if state.inflow_der == -1:
        inter_state_trace += "\n\\item The inflow's derivative is negative, so it must decrease."
        test_state.inflow_amount = max(test_state.inflow_amount - 1, min(possible_amounts['Inflow']))
    # ensure no negative derivative when amount is 0
    if test_state.inflow_amount == 0 and test_state.inflow_der == -1: test_state.inflow_der = 0
    if test_state.volume_amount == 0 and test_state.volume_der == -1: test_state.volume_der = 0
    if test_state.outflow_amount == 0 and test_state.outflow_der == -1: test_state.outflow_der = 0

    state_trace = "\n\\textbf{State " + str(state.num) + "}" + "\n\n\\setlength{\\leftskip}{10pt}" + str(state)
    state_trace += "\n\\textit{Inter-state transitions}: " + ("None\n" if inter_state_trace == "" else "\n\\begin{itemize}" + inter_state_trace + "\n\\end{itemize}")
    if inter_state_trace != "":
        state_trace += "\nResults:\n" + str(test_state)
    state_trace += "\n\\textit{Intra-state transitions}: " + ("None\n" if intra_state_trace == "" else "\n\\begin{itemize}" + intra_state_trace + "\n\\end{itemize}") + "\n"
    state_trace += "\\setlength{\\leftskip}{0pt}\n"
    if not (inter_state_trace != "" or intra_state_trace != ""):
        state_trace += "\nThis is a final state.\n"
    state_trace += "\n\\hrulefill\n"

    return test_state, state_trace

def draw_state_graph(states):
    graph = nx.DiGraph()
    labels = {}
    # Add nodes
    for state in states:
        graph.add_node(state.num)
        labels[state.num] = state.num
    # Add edges
    for state in states:
        for destination in state.links:
            graph.add_edge(state.num, destination)
    f = plt.figure()
    nx.draw(graph, labels=labels)
    f.savefig("state_graph.png")

def generate_learner_document(trace):
    filename = "LearnerDocument"
    head = open("texhead")
    learner_doc = open(filename + ".tex", "w")
    learner_doc.write(head.read())

    learner_doc.write(trace)
    learner_doc.write("\n\end{document}")

    head.close()
    learner_doc.close()

    os.system("pdflatex " + filename + " -quiet")
    print(filename + ".pdf saved succesfully.")

if __name__ == "__main__":
    print("Generating states...")
    states, trace = generate_states()    
    draw_state_graph(states)
    generate_learner_document(trace)