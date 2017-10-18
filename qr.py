import math
import json
import numpy as np

variables = ['Inflow', 'Volume', 'Outflow']

possible_amounts = {'Inflow': [0,1], 'Volume': [0,1,2], 'Outflow': [0,1,2]}
possible_ders = {'Inflow': [-1,0,1], 'Volume': [-1,0,1], 'Outflow': [-1,0,1]}
amount_dict = {0: 'zero', 1: 'positive', 2: 'max'}
der_dict = {-1: 'negative', 0: 'steady', 1: 'positive'}

class State:
    def __init__(self, values, num = -1):
        self.inflow_amount = values[0]
        self.inflow_der = values[1]
        self.volume_amount = values[2]
        self.volume_der = values[3]
        self.outflow_amount = values[4]
        self.outflow_der = values[5]
        self.num = num
        self.links = []

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

def generate_states(init = State([0,0,0,0,0,0], 0)):
    states = [init]
    current_state = 0
    inflow_der_cycle = [0,1,0,-1]
    inflow_der = 0
    no_new = 0
    while no_new < len(possible_ders['Inflow']):
        # current number of states
        current_nos = len(states)
        new_state = State(states[current_state].to_list())
        der = inflow_der_cycle[inflow_der % len(inflow_der_cycle)]
        new_state.set_inflow_der(der)
        if not in_states(states, new_state):
            new_state.set_num(len(states))
            states[current_state].add_link(new_state.num)
            states.append(new_state)
            current_state = new_state.num
        elif current_state != state_index(states, new_state):
            states[current_state].add_link(state_index(states, new_state))
            current_state = state_index(states, new_state)
        stop = False
        while not stop:
            test_state = test_step(states[current_state])
            if not in_states(states, test_state):
                test_state.set_num(len(states))
                states[current_state].add_link(test_state.num)
                states.append(test_state)
                current_state = test_state.num
                stop = True
            elif current_state != state_index(states, test_state):
                states[current_state].add_link(state_index(states, test_state))
                current_state = state_index(states, test_state)
            else: stop = True
        if current_nos == len(states):
            no_new += 1
        else:
            no_new = 0
        inflow_der += 1
    for state in states:
        print state.to_list()
    # for state in states:
    #     print state.links
    print len(states)

def test_step(state):
    test_state = State(state.to_list())
    # volume positive derivative changes volume amount
    if state.volume_der == 1:
        test_state.volume_amount = min(test_state.volume_amount + 1, max(possible_amounts['Volume']))
    # outflow positive derivative changes outflow amount
    if state.outflow_der == 1:
        test_state.outflow_amount = min(test_state.outflow_amount + 1, max(possible_amounts['Outflow']))
    # volume negative derivative changes volume amount
    if state.volume_der == -1:
        test_state.volume_amount = max(test_state.volume_amount - 1, min(possible_amounts['Volume']))
    # outflow negative derivative changes outflow amount
    if state.outflow_der == -1:
        test_state.outflow_amount = max(test_state.outflow_amount - 1, min(possible_amounts['Outflow']))
    # outflow amount influences volume derivative
    if state.outflow_amount >= 1 and state.inflow_amount < 1:
        test_state.volume_der = max(test_state.volume_der - 1, min(possible_ders['Volume']))
    # inflow amount influences volume derivative
    if state.inflow_amount >= 1:
        test_state.volume_der = min(test_state.volume_der + 1, max(possible_ders['Volume']))
    # outflow derivative is equal to volume derivative
    test_state.outflow_der = test_state.volume_der
    # inflow positive derivative changes inflow amount
    if state.inflow_der == 1:
        test_state.inflow_amount = min(test_state.inflow_amount + 1, max(possible_amounts['Inflow']))
    # inflow negative derivative changes inflow amount
    if state.inflow_der == -1:
        test_state.inflow_amount = max(test_state.inflow_amount - 1, min(possible_amounts['Inflow']))
    # ensure no negative derivative when amount is 0
    if test_state.inflow_amount == 0 and test_state.inflow_der == -1: test_state.inflow_der = 0
    if test_state.volume_amount == 0 and test_state.volume_der == -1: test_state.volume_der = 0
    if test_state.outflow_amount == 0 and test_state.outflow_der == -1: test_state.outflow_der = 0
    return test_state

if __name__ == "__main__":
    generate_states()