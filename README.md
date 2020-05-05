# Double pendulum simulation

To start simulation run `main.py`.

## Description
This program simulates double pendulum dynamics with different initial parameters like: masses of balls, rods lengths and deflection angles. An interesting phenomena behind this process in a chaos behavior, when initial parameters has a huge influence of the future evolution.

## How does it work
This program has 4 modules in `\modules`:    
- **pendulum.py**  Creates a pendulum instance and calculates its evolution in time solving differential equations with `scipy.integrate.odeint`.  
- **frames.py** For each pendulum on each time step creates a shot with `matplotlib` and save it in `\frames` dir.  
- **window.py** Draw a simple GUI with `tkinter`. And has a function `simulation` that integrates all of the program flow.  
- **gif_player.py** Draw an animation in the `tkinter` window from files  in `\frames`

