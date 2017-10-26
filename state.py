variables = ['Inflow', 'Volume', 'Outflow']

possible_amounts = {'Inflow': [0,1], 'Volume': [0,1,2], 'Outflow': [0,1,2]}
possible_ders = {'Inflow': [-1,0,1], 'Volume': [-1,0,1], 'Outflow': [-1,0,1]}
amount_dict = {0: 'zero', 1: 'positive', 2: 'max'}
der_dict = {-1: 'negative', 0: 'zero', 1: 'positive'}


class State:
    def __init__(self, values, num=-1, conflicting=False):
        self.inflow_amount = values[0]
        self.inflow_der = values[1]
        self.volume_amount = values[2]
        self.volume_der = values[3]
        self.outflow_amount = values[4]
        self.outflow_der = values[5]
        # self.num will be set depending on the position of this state in the states list
        self.num = num
        self.links = []
        self.conflicting = conflicting

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

    def next_state(self, num=-1):
        next_state = State(self.to_list(), num)
        inter_state_trace = ""

        # inflow positive derivative changes inflow amount
        if self.inflow_der == 1:
            inter_state_trace += "\n\t- The inflow's derivative is positive, so it must increase."
            next_state.inflow_amount = min(next_state.inflow_amount + 1, max(possible_amounts['Inflow']))
        # inflow negative derivative changes inflow amount
        if self.inflow_der == -1:
            inter_state_trace += "\n\t- The inflow's derivative is negative, so it must decrease."
            next_state.inflow_amount = max(next_state.inflow_amount - 1, min(possible_amounts['Inflow']))
        # volume negative derivative changes volume amount
        if self.volume_der == -1:
            inter_state_trace += "\n\t- The volume's derivative is negative, so it must decrease."
            next_state.volume_amount = max(next_state.volume_amount - 1, min(possible_amounts['Volume']))
        # volume positive derivative changes volume amount
        if self.volume_der == 1:
            inter_state_trace += "\n\t- The volume's derivative is positive, so it must increase."
            next_state.volume_amount = min(next_state.volume_amount + 1, max(possible_amounts['Volume']))
        # outflow negative derivative changes outflow amount
        if self.outflow_der == -1:
            inter_state_trace += "\n\t- The outflow's derivative is negative, so it must decrease."
            next_state.outflow_amount = max(next_state.outflow_amount - 1, min(possible_amounts['Outflow']))
        # outflow positive derivative changes outflow amount
        if self.outflow_der == 1:
            inter_state_trace += "\n\t- The outflow's derivative is positive, so it must increase."
            next_state.outflow_amount = min(next_state.outflow_amount + 1, max(possible_amounts['Outflow']))

        # ensure no negative derivative when amount is 0
        if next_state.inflow_amount == 0 and next_state.inflow_der == -1: next_state.inflow_der = 0
        if next_state.volume_amount == 0 and next_state.volume_der == -1: next_state.volume_der = 0
        if next_state.outflow_amount == 0 and next_state.outflow_der == -1: next_state.outflow_der = 0

        return next_state

    def has_interstate_transition(self):
        # Return true if this and next state are the same
        return not self.compare(self.next_state())

    def resolve_dependencies(self):
        intra_state_trace = ""
        if not self.conflicting:
            # outflow amount influences volume derivative
            if self.outflow_amount >= 1:
                intra_state_trace += "\n\t- The outflow is positive, so the volume's derivative must decrease."
                self.volume_der = max(self.volume_der - 1, min(possible_ders['Volume']))        
            # inflow amount influences volume derivative
            if self.inflow_amount >= 1:
                intra_state_trace += "\n\t- The inflow is positive, so the volume's derivative must increase."
                self.volume_der = min(self.volume_der + 1, max(possible_ders['Volume']))
        if self.outflow_der != self.volume_der:
            intra_state_trace += "\n\t- The volume's derivative must be equal to the outflow's derivative."
            # outflow derivative is equal to volume derivative
            self.outflow_der = self.volume_der

    def has_influence_conflicts(self):
        return (self.inflow_amount >= 1) and (self.outflow_amount >= 1) and (self.volume_der != 0)

    def get_conflicting_states(self):
        if self.has_influence_conflicts():
            state1 = State(self.to_list(), conflicting=True)
            state2 = State(self.to_list(), conflicting=True)

            if self.volume_der == 1:
                state1.volume_der = 1
                state2.volume_der = 0
                state1.volume_amount = min(self.volume_amount + 1, max(possible_amounts['Volume']))
                state2.volume_amount = min(self.volume_amount + 1, max(possible_amounts['Volume']))
            elif self.volume_der == -1:
                state1.volume_der = -1
                state2.volume_der = 0
                state1.volume_amount = max(state1.volume_amount - 1, min(possible_amounts['Volume']))
                state2.volume_amount = max(state2.volume_amount - 1, min(possible_amounts['Volume']))
            return state1, state2            
        else:
            raise ValueError("The state has no influence conflicts")

    def flip_inflow_der(self):
        if self.inflow_amount == 1:
            self.inflow_der = -1
        elif self.inflow_amount == 0:
            self.inflow_der = 1


    def __str__(self):
        """ A human-readable string representation of the state.
        """
        inflow_astr = amount_dict[self.inflow_amount]
        inflow_dstr = der_dict[self.inflow_der]
        volume_astr = amount_dict[self.volume_amount]
        volume_dstr = der_dict[self.volume_der]
        outflow_astr = amount_dict[self.outflow_amount]
        outflow_dstr = der_dict[self.outflow_der]

        return (
            "\n\tThe inflow is " + inflow_astr + " and has a " + inflow_dstr + " derivative." +
            "\n\tThe volume is " + volume_astr + " and has a " + volume_dstr + " derivative." +
            "\n\tThe outflow is " + outflow_astr + " and has a " + outflow_dstr + " derivative.")