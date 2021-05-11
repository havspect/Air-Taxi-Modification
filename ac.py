import math

from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate
import seaborn as sns

sns.set(style='ticks')


def grad_in_rad(grad: float) -> float:
    return grad * (math.pi/180)


def kmh_in_ms(kmh: float) -> float:
    return kmh / 3.6


def c_D(cD_0: float, cL_cruise: float, e: float, wing_span: float, wing_area: float) -> float:
    return cD_0 + ((cL_cruise ** 2) / (math.pi * (wing_span**2 / wing_area) * e))


def calc_total_energy(range: int, eff_total: float, weight: int, LD: float) -> float:
    """Result in kWh"""
    return ((range / 1_000_000) * 9.81 * weight) / (eff_total * LD * 3.6)


def calc_total_power(cruise_speed: int, weight: int, LD: float, eff_total: float) -> float:
    """Result in kW"""
    return ((weight * 9.81) / (LD * 1000)) * (kmh_in_ms(cruise_speed) / eff_total)


mtow = 1980  # kg
wing_area = 16.3  # m^2
wing_span = 13.1  # m
cruise_speed: int = 250  # km/h
climb_speed: int = 80  # km/h
range: int = 370 * 1000  # m
e: float = 0.8  #
cD_0: float = 0.03  # 0.02 - 0.04 according to Filippone 2000
eff_total: float = 0.3695


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
class Aircraft():

    weight: int = 1980  # kg
    wing_area: float = 16.3  # m^2
    wing_span: float = 13.1  # m
    cruise_speed: int = 250  # km/h
    climb_speed: int = 80  # km/h
    range: int = 370 * 1000  # m
    e: float = 0.8  #
    cD_0: float = 0.03  # 0.02 - 0.04 according to Filippone 2000
    eff_total: float = 0.3695

    cL_climb: float = field(init=False)
    cD_climb: float = field(init=False)
    LD_climb: float = field(init=False)

    cL_cruise: float = field(init=False)
    cD_cruise: float = field(init=False)
    LD_cruise: float = field(init=False)

    p_cruise: float = field(init=False)
    e_cruise: float = field(init=False)
    h2_required: float = field(init=False)

    def __post_init__(self):
        # Climb
        self.cL_climb = self.calc_cL(speed=self.climb_speed)
        self.cD_climb = self.calc_cD(self.cL_climb)
        self.LD_climb = self.cL_climb / self.cD_climb

        # Cruise
        self.cL_cruise = self.calc_cL(speed=self.cruise_speed)
        self.cD_cruise = self.calc_cD(self.cL_cruise)
        self.LD_cruise = self.cL_cruise / self.cD_cruise 

        # Power, Energy, Fuel
        self.p_cruise = self.calc_total_power()
        self.e_cruise = self.calc_total_energy()
        self.h2_required = self.e_cruise / 33.33  # kg



    def calc_cD(self, cL) -> float:
        return self.cD_0 + ((cL ** 2) / (math.pi * (self.wing_span**2 / self.wing_area) * self.e))

    def calc_cL(self, speed) -> float:
        return (2 * self.weight * 9.81) / (1.225 * self.wing_area * kmh_in_ms(speed)**2)


    def calc_total_energy(self) -> float:
        """Result in kWh"""
        return ((self.range / 1_000_000) * 9.81 * self.weight) / (self.eff_total * self.LD_cruise * 3.6)


    def calc_total_power(self) -> float:
        """Result in kW"""
        return ((self.weight * 9.81) / (self.LD_cruise * 1000)) * (kmh_in_ms(self.cruise_speed) / self.eff_total)

    
    def __str__(self) -> str:
        return tabulate([
            ["Power cruise [kW]", round(self.p_cruise, 2)],
            ["Total energy [kWh]", round(self.e_cruise, 2)],
            ["Mass h2 [kg]", round(self.h2_required, 2)],
            ["L/D [-]", round(self.LD_cruise, 2)]], 
            headers=["Attribute", "Value"])



cruise_speed = np.linspace(150, 300, 100)
var = [Aircraft(cruise_speed=x).e_cruise for x in cruise_speed]
var2 = [Aircraft(cruise_speed=x, eff_total=0.45).e_cruise for x in cruise_speed]

fig, ax = plt.subplots()
ax.plot(cruise_speed, var, label="Wirkungsgrad: 0.39")
ax.plot(cruise_speed, var2, label="Wirkungsgrad: 0.44")
ax.set_ylabel("Energie [kWh]")
ax.set_xlabel("Reisegeschwindigkeit [km/h]")
ax.legend()
plt.show()
