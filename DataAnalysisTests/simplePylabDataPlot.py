"""
    simple_pylab_data_plot.py
    A very simple example of using pylab to plot some data

    Modified 27 October 2012 by David C. Bailey <dbailey@physics.utoronto.ca>
        based on pyplot tutorial at
        http://matplotlib.sourceforge.net/users/pyplot_tutorial.html.

    Requires data file: gauss.txt

"""
# pylab (http://www.scipy.org/PyLab) includes numpy and most of scipy
import matplotlib
import matplotlib.pyplot as plt
import numpy

# Read in data file
x, y, dy = numpy.loadtxt('gauss.txt', unpack=True)

# Create plot showing data as medium sized, filled red circles with error-bars
plt.errorbar(x, y, yerr=dy, fmt='ro', markersize=5)

# Display all created plots
plt.show()

##### End simple_pylab_data_plot.py