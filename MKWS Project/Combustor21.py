import tkinter as tk
import math
import csv
import matplotlib.pyplot as plt
import cantera as ct
from PIL import Image, ImageTk
import os

class FuelPart:
    def _init_(self, entryName, entryX):
        self.entryName = entryName
        self.entryX = entryX


def showDiagrams():
    
    window = tk.Toplevel(root)
    window.title("Diagrams")

    imgT = ImageTk.PhotoImage(Image.open("Temperature.png"))
    panelT = tk.Label(window, image = imgT)
    panelT.grid(row = 0, column = 0)

    imgP = ImageTk.PhotoImage(Image.open("Pressure.png"))
    panelP = tk.Label(window, image = imgP)
    panelP.grid(row = 0, column = 1, padx = 10)

    imgX = ImageTk.PhotoImage(Image.open("X.png"))
    panelX = tk.Label(window, image = imgX)
    panelX.grid(row = 1, column = 0)

    window.mainloop()
    

def combustor():
	
    # use reaction mechanism GRI-Mech 3.0

    gas = ct.Solution('gri30.xml')

    # create a reservoir for the fuel inlet, and set to pure methane.
    fuelX = 'CH4:' + eCH4.get() + ',C2H6:' + eC2H6.get() + ',N2:' + eN2.get()
    i = 0
    while i < len(newFuelParts):
        name = newFuelParts[i].entryName.get()
        x = newFuelParts[i].entryX.get()
        if float(x) > 0:
            fuelX += ',' + name + ':' + x
        i += 1

    
    gas.TPX = float(eFuelT.get()), ct.one_atm, fuelX  
    fuel_in = ct.Reservoir(gas)
    fuel_mw = gas.mean_molecular_weight

    # use predefined function Air() for the air inlet
    air = ct.Solution('air.xml')
    air_in = ct.Reservoir(air)
    air_mw = air.mean_molecular_weight

    # to ignite the fuel/air mixture, we'll introduce a pulse of radicals. The
    # steady-state behavior is independent of how we do this, so we'll just use a
    # stream of pure atomic hydrogen.
    gas.TPX = float(eCombustorT.get()), float(eCombustorP.get()) * ct.one_atm, 'H:1.0'
    igniter = ct.Reservoir(gas)

    # create the combustor, and fill it in initially with N2
    gas.TPX = float(eCombustorT.get()), float(eCombustorP.get()) * ct.one_atm, 'N2:1.0'
    combustor = ct.IdealGasReactor(gas)
    combustor.volume = 1.0

    # create a reservoir for the exhaust
    exhaust = ct.Reservoir(gas)

    # lean combustion, phi = 0.5
    equiv_ratio = float(eRatio.get())

    # compute fuel and air mass flow rates
    factor = 0.1
    air_mdot = factor * 9.52 * air_mw
    fuel_mdot = factor * equiv_ratio * fuel_mw

    # create and install the mass flow controllers. Controllers m1 and m2 provide
    # constant mass flow rates, and m3 provides a short Gaussian pulse only to
    # ignite the mixture
    m1 = ct.MassFlowController(fuel_in, combustor, mdot=fuel_mdot)

    # note that this connects two reactors with different reaction mechanisms and
    # different numbers of species. Downstream and upstream species are matched by
    # name.
    m2 = ct.MassFlowController(air_in, combustor, mdot=air_mdot)

    # The igniter will use a Gaussian time-dependent mass flow rate.
    fwhm = 0.2
    amplitude = 0.1
    t0 = 1.0
    igniter_mdot = lambda t: amplitude * math.exp(-(t-t0)**2 * 4 * math.log(2) / fwhm**2)
    m3 = ct.MassFlowController(igniter, combustor, mdot=igniter_mdot)

    # put a valve on the exhaust line to regulate the pressure
    v = ct.Valve(combustor, exhaust, K=1.0)

    # the simulation only contains one reactor
    sim = ct.ReactorNet([combustor])

    # take single steps to 6 s, writing the results to a CSV file for later
    # plotting.
    tfinal = 4.0
    tnow = 0.0
    Tprev = combustor.T
    tprev = tnow
    states = ct.SolutionArray(gas, extra=['t','tres'])

    while tnow < tfinal:
        tnow = sim.step()
        tres = combustor.mass/v.mdot(tnow)
        Tnow = combustor.T
        if abs(Tnow - Tprev) > 1.0 or tnow-tprev > 2e-2:
            tprev = tnow
            Tprev = Tnow
            states.append(gas.state, t=tnow, tres=tres)

    states.write_csv('combustor.csv', cols=('t','T','tres','X'))


    #matplotlib
    plt.figure()
    plt.plot(states.t, states.T)
    plt.xlabel('Time [s]')
    plt.ylabel('Temperature [K]')
    plt.title('Temperature')
    plt.plot()
    plt.savefig('Temperature.png')

    plt.figure()
    plt.plot(states.t, states.P)
    plt.xlabel('Time [s]')
    plt.ylabel('Pressure [Pa]')
    plt.title('Pressure')
    plt.plot()
    plt.savefig('Pressure.png')

    plt.figure()
    plt.plot(states.t, states.X)
    plt.xlabel('Time [s]')
    plt.ylabel('Concentration H20')
    plt.title('H20')
    plt.plot()
    plt.savefig('X.png')

    print('OK!')
    
def addFuel_click(event):
    nameNext = tk.StringVar()
    nameNext.set('H2')
    lblNext = tk.Entry(root, width = 5, textvariable = nameNext)
    lblNext.grid(row=6 + len(newFuelParts), column=0)
    svNext = tk.StringVar()
    svNext.set('0')
    eNext = tk.Entry(root, width = 8, textvariable = svNext)
    eNext.grid(row=6 + len(newFuelParts), column=1)
    next = FuelPart()
    next.entryName = lblNext
    next.entryX = eNext
    newFuelParts.append(next)

    

def start_click(event):
    combustor()

newFuelParts = []

root = tk.Tk()
root.title("Combustor")
root.geometry("500x300")

butDiagram = tk.Button(root, text="Diagram", command=showDiagrams)
butDiagram.grid(row = 0, column = 2)

butQUIT = tk.Button(root, text="QUIT", command=root.quit, fg = "red")
butQUIT.grid(row=0, column=0)

butStart = tk.Button(root, text="START")
butStart.grid(row = 0, column = 1)
butStart.bind("<Button-1>", start_click)

butStart = tk.Button(root, text="Add Fuel")
butStart.grid(row = 0, column = 3)
butStart.bind("<Button-1>", addFuel_click)

lblFuel = tk.Label(root, text='Fuel:')
lblFuel.grid(row=1, column=0)

sv1 = tk.StringVar()
sv1.set(94.22)
eCH4 = tk.Entry(root, textvariable = sv1, width = 8)
eCH4.grid(row=3, column=1)
lblCH4 = tk.Label(root, text = "X  CH4")
lblCH4.grid(row=3, column=0)

lblC2H6 = tk.Label(root, text = "X  C2H6")
lblC2H6.grid(row=4, column=0)
sv2 = tk.StringVar()
sv2.set('3.16')
eC2H6 = tk.Entry(root, width = 8, textvariable = sv2)
eC2H6.grid(row=4, column=1)

lblN2 = tk.Label(root, text = "X  N2")
lblN2.grid(row=5, column=0)
sv3 = tk.StringVar()
sv3.set('2.62')
eN2 = tk.Entry(root, width = 8, textvariable = sv3)
eN2.grid(row=5, column=1)


#Fuel Temperature widgets
lblFuelT = tk.Label(root, text = 'Temperature [K]')
lblFuelT.grid(row = 2, column = 0)
svfT = tk.StringVar()
svfT.set('500')
eFuelT = tk.Entry(root, textvariable = svfT, width = 8)
eFuelT.grid(row=2, column=1)

  
lblOxidiser = tk.Label(root, text='Oxidiser: Air')
lblOxidiser.grid(row=2, column=3)

#Combustor Temperature 
lblCombustorT = tk.Label(root, text = 'Combustor Temperature [K]')
lblCombustorT.grid(row = 3, column = 3)
svCT = tk.StringVar()
svCT.set('300')
eCombustorT = tk.Entry(root, textvariable = svCT, width = 8)
eCombustorT.grid(row=3, column=4)

#Combustor Pressure 
lblCombustorP = tk.Label(root, text = 'Combustor Pressure [atm]')
lblCombustorP.grid(row = 4, column = 3)
svCP = tk.StringVar()
svCP.set('1')
eCombustorP = tk.Entry(root, textvariable = svCP, width = 8)
eCombustorP.grid(row=4, column=4)

#Equivalence ratio 
lblRatio = tk.Label(root, text = 'Equivalence ratio')
lblRatio.grid(row = 5, column = 3)
svR = tk.StringVar()
svR.set('0.5')
eRatio = tk.Entry(root, textvariable = svR, width = 8)
eRatio.grid(row=5, column=4)




#fuelX = []
#fuelX.append(eCH4)
#fuelX.append(eC2H6)






root.mainloop()

