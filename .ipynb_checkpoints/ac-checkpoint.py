import math

from dataclasses import dataclass, field, fields
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate


def grad_in_rad(grad: float) -> float:
    return grad * (math.pi/180)


def kmh_in_ms(kmh: float) -> float:
    return kmh / 3.6


def plot_polar():
    c_L_list = np.linspace(-0.2, 1, 100)
    c_D_list = [c_D(cD_0=cD_0, cL_cruise=x, wing_span=wing_span,
                    wing_area=wing_area, e=e) for x in c_L_list]

    fig, ax = plt.subplots()
    ax.plot(c_D_list, c_L_list)

    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.spines['bottom'].set_position('zero')

    ax.grid(True, which='both')
    plt.show()


@dataclass
class Variable():
    v: Any
    unit: str = ""
    boundaries: list = field(default_factory=list)
    name: str = ""
    description: str = ""
    



@dataclass
class Aircraft():

    weight: Variable = Variable(1950, "kg", boundaries=[1200, 1980], name="Weight")
    wing_area: Variable = Variable(16.3, "m^2", name="Wing Area")
    wing_span: Variable = Variable(13.1, "m", name="Wing Span")

    cruise_speed: Variable = Variable(250, "km/h", boundaries=[100,350], name="Cruise Speed")
    climb_speed: Variable = Variable(80, "km/h", boundaries=[60,120], name="Climb Speed") 
    cruise_range: Variable = Variable(350 * 1000, "m", boundaries=[100 * 1000, 600 * 1000], name="Cruise Range") 
    cruise_height: Variable = Variable(3000, "m", [3000, 4000], name="Cruise Height")

    e: Variable = Variable(0.8, "-", boundaries=[0.7, 0.8], name="Oswald-Faktor")  #
    cD_0: Variable = Variable(0.03, "-", boundaries=[0.02, 0.04], name="cD_0")  # 0.02 - 0.04 according to Filippone 2000

    eff_total: Variable = Variable(0.3986, "-", boundaries=[0.35, 0.55], name="Total Efficency Propulsion System")

    cL_climb: Variable = field(init=False)
    cD_climb: Variable = field(init=False)
    LD_climb: Variable = field(init=False)

    cL_cruise: Variable = field(init=False)
    cD_cruise: Variable = field(init=False)
    LD_cruise: Variable = field(init=False)

    p_cruise: Variable = field(init=False)
    e_cruise: Variable = field(init=False)
    h2_required: Variable = field(init=False)

    def __post_init__(self):
        # Climb
        self.cL_climb = Variable(self.calc_cL(speed=self.climb_speed), "-", name="c_L_climb")
        self.cD_climb = Variable(self.calc_cD(self.cL_climb), "-", name="c_D_climb")
        self.LD_climb = Variable(self.cL_climb.v / self.cD_climb.v, "-", name="L/D")

        # Cruise
        self.cL_cruise = Variable(self.calc_cL(speed=self.cruise_speed, rho=0.909), "-", name="c_L_cruise")
        self.cD_cruise = Variable(self.calc_cD(self.cL_cruise), "-", name="c_D_cruise")
        self.LD_cruise = Variable(self.cL_cruise.v / self.cD_cruise.v , "-", name="L/D")

        # Power, Energy, Fuel
        self.p_cruise = Variable(self.calc_total_power(), "kW", name="P_cruise")
        self.e_cruise = Variable(self.calc_total_energy(), "kWh", name="E_cruise")
        self.h2_required = Variable(self.e_cruise.v / 33.33, "kg" , name="Hydrogen required")  # kg



    def calc_cD(self, cL) -> float:
        return self.cD_0.v + ((cL.v ** 2) / (math.pi * (self.wing_span.v**2 / self.wing_area.v) * self.e.v))

    def calc_cL(self, speed, rho=1.225) -> float:
        return (2 * self.weight.v * 9.81) / (rho * self.wing_area.v * kmh_in_ms(speed.v)**2)


    def calc_total_energy(self) -> float:
        """Result in kWh"""
        return ((self.cruise_range.v / 1_000_000) * 9.81 * self.weight.v) / (self.eff_total.v * self.LD_cruise.v * 3.6)


    def calc_total_power(self) -> float:
        """Result in kW"""
        return ((self.weight.v * 9.81) / (self.LD_cruise.v * 1000)) * (kmh_in_ms(self.cruise_speed.v) / self.eff_total.v)

    
    def __str__(self) -> str:
        output = list()

        for f in fields(self):
            var = getattr(self, f.name)
            output.append([f"{var.name} [{var.unit}]", round(var.v,2)])

        return tabulate(output, headers=["Attribute", "Value"])

a = Aircraft()


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
cruise_speed = np.linspace(150, 350, 100)

lines = list()
labels = list()

for eff in np.arange(0.40,0.50, 0.02):

    e_cruise = list()
    p_cruise = list()
    aircrafts = list()

    for x in cruise_speed:
        # Silent Air Taxi
        #a = Aircraft(cruise_speed=Variable(x, "km/h"), eff_total=Variable(eff), weight=Variable(1500), cD_0=Variable(0.02), cruise_range=Variable(450_000))
        # Piper PA-46 
        a = Aircraft(cruise_speed=Variable(x, "km/h"), eff_total=Variable(eff), cD_0=Variable(0.025), weight=Variable(1700))
        aircrafts.append(a)
        p_cruise.append(a.p_cruise.v)
        e_cruise.append(a.e_cruise.v)

    lines.append(ax1.plot(cruise_speed, e_cruise, label=f"Wirkungsgrad (TTP): {round(eff, 2)}")[0])
    labels.append("$\eta_{TTP}=$" + f"{round(eff, 2)}")
    ax2.plot(cruise_speed, p_cruise, "--" , label=f"Wirkungsgrad: {round(eff, 2)}")
    
    #ax.annotate(f" E:{round(min(var),2)}", xy=(cruise_speed[var.index(min(var))], min(var)), xytext=(cruise_speed[var.index(min(var))], min(var)+5), size=10)

ax1.grid(True)
ax2.grid(True)
ax1.set_ylim(0,550)
ax2.set_ylim(0,550)
ax2.set_ylabel("Leistung [kW]")
ax1.set_ylabel("Tatsächlicher Energiebedarf [kWh]")
ax1.set_xlabel("Reisegeschwindigkeit [km/h]")


ax1.legend()
# fig.legend(
#     lines,
#     labels, 
#     loc="lower center",
#     borderaxespad=0.1,
#     ncol=3
# )

plt.tight_layout()
plt.subplots_adjust(bottom=0.14)
plt.show()

print(Aircraft(cruise_speed=Variable(250, "km/h"), eff_total=Variable(0.42), cD_0=Variable(0.025), weight=Variable(1700)))



