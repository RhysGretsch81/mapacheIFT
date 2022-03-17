import pyrtl

from ift.gates import *
from ift.full_adder import *
from ift.multiplier import *
from ift.comparator import *

BITMAX = 32

def simulate_gates(op, a_inp, b_inp, a_t_inp, b_t_inp):
    a, b = pyrtl.Input(BITMAX, 'a'), pyrtl.Input(BITMAX, 'b')
    a_t, b_t = pyrtl.Input(BITMAX, 'a_t'), pyrtl.Input(BITMAX, 'b_t') 
    
    if op=='AND': o, o_t = and_gate(a, b, a_t, b_t)
    elif op=='OR': o, o_t = or_gate(a, b, a_t, b_t)
    elif op=='XOR': o, o_t = xor_gate(a, b, a_t, b_t)
    elif op=='XNOR': o, o_t = xnor_gate(a, b, a_t, b_t)

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    sim_inputs = {
        'a': a_inp,
        'b': b_inp,
        'a_t': a_t_inp,
        'b_t': b_t_inp
    }

    sim.step(sim_inputs)
    o_val, o_t_val = sim.inspect(o), sim.inspect(o_t)
    pyrtl.reset_working_block()
    return o_t_val


def simulate_add(op, a_inp, b_inp, c_inp, a_t_inp, b_t_inp, c_t_inp):
    a, b, c = pyrtl.Input(BITMAX, 'a'), pyrtl.Input(BITMAX, 'b'), pyrtl.Input(BITMAX, 'c')
    a_t, b_t, c_t = pyrtl.Input(BITMAX, 'a_t'), pyrtl.Input(BITMAX, 'b_t'), pyrtl.Input(BITMAX, 'c_t')
    
    sum, carry, sum_t, carry_t = full_adder_32bit(a, b, c, a_t, b_t, c_t)

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    sim_inputs = {
        'a': a_inp,
        'b': b_inp,
        'c': c_inp,
        'a_t': a_t_inp,
        'b_t': b_t_inp,
        'c_t': c_t_inp
    }

    sim.step(sim_inputs)
    sum_val, carry_val = sim.inspect(sum), sim.inspect(carry)
    sum_t_val, carry_t_val = sim.inspect(sum_t), sim.inspect(carry_t)
    pyrtl.reset_working_block()
    return sum_val, carry_val, sum_t_val, carry_t_val


def simulate_comparator(op, a_inp, b_inp, a_t_inp, b_t_inp):
    a, b = pyrtl.Input(BITMAX, 'a'), pyrtl.Input(BITMAX, 'b')
    a_t, b_t = pyrtl.Input(BITMAX, 'a_t'), pyrtl.Input(BITMAX, 'b_t')
    
    l, e, g, l_t, e_t, g_t = comparator_32bit(a, b, a_t, b_t)

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    sim_inputs = {
        'a': a_inp,
        'b': b_inp,
        'a_t': a_t_inp,
        'b_t': b_t_inp
    }

    sim.step(sim_inputs)
    less, equal, greater = sim.inspect(l), sim.inspect(e), sim.inspect(g)
    less_t, equal_t, greater_t = sim.inspect(l_t), sim.inspect(e_t), sim.inspect(g_t)
    pyrtl.reset_working_block()
    return less, equal, greater, less_t, equal_t, greater_t


def simulate_multiplier(a_inp, b_inp, a_t_inp, b_t_inp):
    
    a, b = pyrtl.Input(BITMAX, 'a'), pyrtl.Input(BITMAX, 'b')
    a_t, b_t = pyrtl.Input(BITMAX, 'a_t'), pyrtl.Input(BITMAX, 'b_t')

    # p, p_t = multiplier(a, b, a_t, b_t)
    #p, p_t = multiplier_8bit(a, b, a_t, b_t)
    #p, p_t = multiplier_16bit(a, b, a_t, b_t)
    p, p_t = multiplier_32bit(a, b, a_t, b_t)

    sim_trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=sim_trace)

    sim_inputs = {
        'a': a_inp,
        'b': b_inp,
        'a_t': a_t_inp,
        'b_t': b_t_inp
    }

    sim.step(sim_inputs)

    p_val, p_t_val = sim.inspect(p), sim.inspect(p_t)
    pyrtl.reset_working_block()
    return p_val, p_t_val


def trackInfo(op, a, b, a_t=None, b_t=None, c=None, c_t=None):
    if op=='AND' or op=='OR' or op=='XOR' or op=='XNOR':
        return simulate_gates(op, a, b, a_t, b_t)
    elif op=="ADD":
        sum, carry, sum_t, carry_t = simulate_add(op, a, b, c, a_t, b_t, c_t)
        return sum, carry, sum_t, carry_t
    elif op=="MULT":
        o, o_t = simulate_multiplier(a, b, a_t, b_t)
        return o, o_t
    elif op=="COMP":
        less, equal, greater, less_t, equal_t, greater_t = simulate_comparator(op, a, b, a_t, b_t)
        return less, equal, greater, less_t, equal_t, greater_t

    return "Operation not available. Select from [AND, OR, XOR, XNOR, ADD, MULT, COMP]"


## Testing 
if __name__=='__main__':

    # NOTE: for ADD, the inputs to execute look like (a, b, a_t, b_t, c, c_t)
    print(execute('ADD', 2, 3, 7, 7, 0, 7))

    # RUN to execute comparison
    # print(execute('COMP', 2, 3, 0, 7, 7, 0))
