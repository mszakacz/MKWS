import sys
import os
import math
import cantera as ct
import numpy
import csv


'''
Fuel
 +            --------->  PREMIXER (Ideal Gas Reactor) ---------> Combustor (CSTR)
EGR oxidiser
'''

# defining the phases
fuel2= ct.Solution('gri30.cti')  # Natural Gas: 94.22% CH4, 3.16% C2H6 and 2.62% N2
egr=ct.Solution('gri30.cti')     # For Exhaust Gas Recirculation Oxidiser: 3% CO2, 17% O2, N2 79%, Ar 1%

#defining composition of fuel, fuel reservoir

fuel2.TPX= 700.0, 10.3e5,'CH4:0.9422,C2H6:0.0316,N2:0.0262'  # Natural Gas Composition
NG_inlet2= ct.Reservoir(fuel2)
NG_mw2= fuel2.mean_molecular_weight

# Creating Igniter Reservoir ; Stream of H radicals to ignite the mixture
fuel2.TPX=1000.0,ct.one_atm,'H:1'
igniter=ct.Reservoir(fuel2)

#defining composition of oxidiser and reservoir

egr.TPX= 700.0, 10.3e5,'CO2:0.03,O2:0.17,N2:0.79,AR:0.01'  # EGR oxidiser
oxy_inlet2= ct.Reservoir(egr)
#oxy_mw= egr.mean_molecular_weight


#mixer: filled initially with nitrogen

fuel2.TPX= 700.0,10.3e5,'N2:1'
mixer2=ct.IdealGasReactor(fuel2, energy='on')
mixer2.volume=10e-6   # Volume Computed as per experimental dimensions in m3

combustor=ct.IdealGasReactor(fuel2,energy='on')
combustor.volume=71.136e-6   # Experimental Dimensions in m3

exhaust2=ct.Reservoir(fuel2)  # Exhaust Reservoir

eq_ratio2=1  # Equivalence Ratio
# mdot of oxidiser - 1.4 kg/s according to the experiment

fuel_pipe2= ct.MassFlowController(NG_inlet2, mixer2, mdot=1.4*eq_ratio2)
oxy_pipe2=ct.MassFlowController(oxy_inlet2,mixer2,mdot=1.4)


# Igniter modeled as pulsed radicals of Hydrogen
fwhm=0.2
amp=0.1
t0=1
igniter_mdot= lambda t:amp*math.exp(-(t-t0)**2*4*math.log(2)/fwhm**2)
ignite_pipe=ct.MassFlowController(igniter,combustor,mdot=igniter_mdot)

# The premixed reactants have to enter the combustor

mixer2combustor=ct.MassFlowController(mixer2,combustor)

#exhaust valve

v2=ct.Valve(combustor, exhaust2, K=100)

#reactor Network

sim=ct.ReactorNet([mixer2, combustor])


#time stepping

t_init2=0
temp=numpy.zeros(100)
comp=numpy.zeros(100)

tfinal = 6.0
tnow = 0.0
Tprev = combustor.T
tprev = tnow
states = ct.SolutionArray(fuel2, extra=['t','tres'])

for n in range(100):
    tres2= combustor.mass/1.4
    t_init2+=2*tres2
    sim.advance(t_init2)


print(combustor.thermo.report())
