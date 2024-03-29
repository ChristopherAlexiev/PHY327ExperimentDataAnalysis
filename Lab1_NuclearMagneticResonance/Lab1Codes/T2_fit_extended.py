"""
odr_fit_to_data_extended.py
    A program that uses Orthogonal Distance Regression to fit x,y data
        with random and (optional) systematic uncertainties in 
        both x & y.
        Monte Carlo methods are used to calculate the output parameter
        uncertainties and Confidence Interval for the fit.

    This example fits a Gaussian to data in file gauss_ODR.txt.

    To fit your own data, go to the Mandatory User Definitions.
        You need to change:
    (1) func(x,*p) to return the function you are trying to fit,
            p are the parameters that the fit optimizes,
            x are the independent variable(s)
    (2) the name of the data file to be read in by numpy.loadtxt,
    (3) the initial guesses (p_guess) for the fit parameters. The fit
             will not converge if your guess is poor.

    Note: scipy.odr and scipy.optimize.curve_fit require x & p in
              opposite orders, so we use a "swapped" function so we can
              use the curve_fit convention here.

    For information on scipy.odr, see
    http://docs.scipy.org/doc/scipy/reference/odr.html

    Copyright (c) 2018 University of Toronto
    Last Modification  :   29 July 2018 by David Bailey
    Original Version   :   16 August 2017 by David Bailey
        Based on odr_fit_to_data.py by Michael Luzi and David Bailey
    Contact: David Bailey <dbailey@physics.utoronto.ca>
                (www.physics.utoronto.ca/~dbailey)
    License: Released under the MIT License; the full terms are
                appended to the end of this file, and are also found
                at www.opensource.org/licenses/mit-license.php
"""
# Use python 3 consistent printing and unicode
from __future__ import print_function
from __future__ import unicode_literals

import inspect                # docs.python.org/library/inspect.html
from matplotlib import pyplot # matplotlib.org/api/pyplot_api.html
import numpy                  # numpy.scipy.org/
import scipy.odr           # docs.scipy.org/doc/scipy/reference/odr.html


#################################################################
#### Define functions that may be referenced in the User
####     definitions that immediately follow
#################################################################
# Define some uncertainty distribution functions for smearing data
def gaussian_distribution(x,dx):
    from numpy.random import normal
    return normal(x,dx)
def uniform_distribution(x,dx):
    from numpy.random import uniform
    return uniform(x-dx, x+dx)
def t_distribution(x,dx,nu=1):
    # Student's t distribution with nu degrees of freedom
    #   The default (nu=1) is Cauchy/Lorentzian
    from numpy.random import standard_t
    return x+dx*standard_t(nu,len(dx))

## Define some possible functions to be fitted
#    You may, of course, define your own.
#  The arguments for these functions are (x,*p), e.g. instead of (p,x),
#    to be consistent with what is used for scipy.optimize.curve_fit
def T1exponential(x,*p):
    M_0     = p[0]    
    T_1 = p[1]
    return ( M_0*(1-2*numpy.exp(-1*x/T_1)))

def T2exponential(x,*p):
    I_0     = p[0]    
    T_2 = p[1]
    return ( I_0*numpy.exp(-1*x/T_2))

def AbsoluteExponential(x,*p) :
    y_mu     = p[0]    
    mu       = p[1]    
    sigma    = p[2]    
    return ( y_mu*numpy.exp(-1*abs((x-mu)/sigma)) )
def LogNormal(x,*p) :
    y_mu     = p[0]    
    mu       = p[1]    
    sigma    = p[2]    
    return ( y_mu*numpy.exp(-1*(numpy.log(x)-numpy.log(mu))**2/(2*sigma**2)) )
def Cauchy(x,*p) :
    # Cauchy / Lorentzian / Breit-Wigner peak with contant background:
    #B           = p[0]    #   Constant Background
    x1_peak     = p[0]    #   Height above/below background
    x1          = p[1]    #   Central value
    width_x1    = p[2]    #   Half-Width at Half Maximum
    return (x1_peak*(1/(1+((x-x1)/width_x1)**2)) )
def linear(x,*p) :
    # A linear function with:
    #   Constant Background          : p[0]
    #   Slope                        : p[1]
    return p[0]+p[1]*x
def cubic(x,*p) :
    # A cubic function with:
    #   Constant Background          : p[0]
    #   Slope                        : p[1]
    #   Curvature                    : p[2]
    #   3rd Order coefficient        : p[3]
    return p[0]+p[1]*x+p[2]*x**2+p[3]*x**3
def absolute_power(x,*p) :
    # A "peak like" (hence the minus sign) absolute power function
    mu    = p[0]    #  Central position
    nu    = p[1]    #  Power exponent
    y_mu  = p[2]    #  Normalization
    y0    = p[3]    #  Background offset
    return y_mu*abs(x-mu)**nu + y0
def gaussian(x,*p) :
    from numpy import exp
    mu     = p[0]    #   Peak position
    sigma  = p[1]    #   Peak width
    y_mu   = p[2]    #   Peak height scale
    return y_mu*exp(-(x-mu)**2/(2*sigma**2))
def semicircle(x,*p) :
    # The upper half of a circle:
    R           = p[0]    #   Radius of circle
    x0          = p[1]    #   x coordinate of centre of circle
    y0          = p[2]    #   y coordinate of centre of circle
    from numpy import array, sqrt
    y=[]
    for i in range(len(x)) :
        y_squared = R**2-(x[i]-x0)**2
        if y_squared < 0 :   # Outside the x range of the circle,
            y.append(y0)     #   the y value is just y0
        else :
            y.append(sqrt(y_squared)+y0)
    return array(y)
def inverse(x,*p) :
    return p[0] + p[1]*x + p[2]/x**2

#################################################################

#################################################################
#### Mandatory User Definitions
#################################################################
## Choose function, data to fit, and intial guesses:
func      = T2exponential
data_file = "T2Data.txt"
sampleTitle = "T2 Sample 1B Sep 24"
x_label, y_label   = "x = (time ms)", "y = (Voltage mV)"
p_guess   = (1100, 1)     # Guess for Gaussian fit to gauss_ODR.tx-989
#################################################################
#### Optional User Definitions
#################################################################
# Define axis labels for plot

# Choose optional plots
plot_initial_guess = True
plot_MC_fits       = True
# Number of Monte Carlo iterations
#    For tests, this can be small, e.g. 101
#    For serious work, this should be 1001 or larger.
Number_of_MC_iterations       = 1001
# Set probability distributions associated with uncertainties
smear_x_data   = gaussian_distribution  # Random x
smear_y_data   = gaussian_distribution  # Random y
smear_scale_x  = gaussian_distribution  # Systematic x scale
smear_scale_y  = gaussian_distribution  # Systematic y scale
smear_x_offset = gaussian_distribution  # Systematic x offset
smear_y_offset = gaussian_distribution  # Systematic y offset
# Are x & y systematics correlated with the same calibration factors?
correlated_offset = False
correlated_scale  = True
# Uncertainties can be set by hand here
#    Random uncertainties cannot be zero for ODR,
#       but systematics can be zero.
#    To compare to Least Squares fit of the same data, turn off the
#        effect of the x uncertainties by setting x_sigma_set to a very 
#        small value, but it cannot be exactly zero
#  Random uncertainties (cannot be zero for ODR).
x_sigma_set, y_sigma_set = None, None
#  Linear systematics
x_offset, dx_offset, x_scale, dx_scale = None, None, None, None
y_offset, dy_offset, y_scale, dy_scale = None, None, None, None
#################################################################

#################################################################
#### Initialization
#################################################################
## Load data to fit
#     Any lines in the data file starting with '#' are ignored
#     "data" are values, "sigma" are uncertainties,
try : # Default delimiter is whitespace
    Data = numpy.loadtxt( data_file, comments='#', unpack = True)
except : # But comma delimiters are also okay
    Data = numpy.loadtxt( data_file, comments='#', unpack = True,
                             delimiter=',')
# Default format is for each data point line to have 4 values in this
#         order: x value, x uncertainty, y value, y uncertainty
if len(Data) == 4 :  # Default format
    x_in_file, x_sigma_in_file, y_in_file, y_sigma_in_file = Data
    # A scale factor is occasionally useful for handling systematics of
    #   measurements taken on different ranges of an instrument, but if
    #   not given it can be assumed to be 1.
    scale_factor      = numpy.array([1]*len(x_in_file))
elif   len(Data) == 5 :
    # If data points do have a scale factor, it is the 5th value.
    x_in_file, x_sigma_in_file, y_in_file, y_sigma_in_file, \
                scale_factor = Data
else :
    print("WARNING!!! Input data file has illegal number of columns!")

# Check if there are any offset or scale systematic uncertainties
#     assuming x_true = a_x + b_x * x_measured
#     assuming y_true = a_y + b_y * y_measured
sys_x, sys_y = [0, 0, 1, 0], [0, 0, 1, 0]
with open(data_file) as file:
    for i,line in enumerate(file):
        if   line.startswith('#  a_x, da_x, b_x, db_x =') :
            sys_x = [float(f) for f 
                         in line.rstrip().split("=")[1].split(",")]
        elif line.startswith('#  a_y, da_y, b_y, db_y =') :
            sys_y = [float(f) for f 
                         in line.rstrip().split("=")[1].split(",")]

# Set systematic uncertainties that have not been previously defined
#    Offset and offset uncertainty are multiplied by the scale factor.
if x_offset  == None : x_offset  = sys_x[0]*scale_factor
if dx_offset == None : dx_offset = sys_x[1]*scale_factor
if x_scale   == None : x_scale   = sys_x[2]
if dx_scale  == None : dx_scale  = sys_x[3]
if y_offset  == None : y_offset  = sys_y[0]*scale_factor
if dy_offset == None : dy_offset = sys_y[1]*scale_factor
if y_scale   == None : y_scale   = sys_y[2]
if dy_scale  == None : dy_scale  = sys_y[3]
# Applied systematic scaling to data
x_data  = x_offset + x_in_file * x_scale
y_data  = y_offset + y_in_file * y_scale
# Set random uncertainties from file if they are 
#           not set in the code above
if x_sigma_set == None :
    x_sigma = x_sigma_in_file * x_scale
else :
    x_sigma = x_sigma_set * x_scale
if y_sigma_set == None :
    y_sigma = y_sigma_in_file * y_scale
else :
    y_sigma = y_sigma_set * y_scale

#################################################################
#### Primary ODR Fit
#################################################################
# Load data for ODR fit
data = scipy.odr.RealData(x=x_data, y=y_data, sx=x_sigma, sy=y_sigma)
# Load model for ODR fit
#    Irritatingly, scipy.odr and scipy.optimize.curve_fit require x & p
#    in opposite orders, so to be consistent with functions defined for
#    curve_fit we use a little "swapped" wrapper function.
def swapped(a,b):
    return func(b,*a)
model = scipy.odr.Model(swapped)

## Now fit model to data
#	job=10 selects central finite differences instead of forward
#       differences when doing numerical differentiation of function
#	maxit is maximum number of iterations
#   The scipy.odr documentation is a bit murky, so to be clear note
#        that calling ODR automatically sets full_output=1 in the
#        low level odr function.
fitted = scipy.odr.ODR(data, model, beta0=p_guess, maxit=50, job=0)

output = fitted.run()
p   = output.beta      # 'beta' is an array of the parameter estimates
# Note: odr, unlike curve_fit, returns a standard parameter
#           covariance matrix.
cov = output.cov_beta
#"Quasi-chi-squared" is defined to be the
#           [total weighted sum of squares]/dof
#	i.e. same as numpy.sum((residual/sigma_odr)**2)/dof or
#       numpy.sum(((output.xplus-x)/x_sigma)**2
#                                +((y_data-output.y)/y_sigma)**2)/dof
#	Converges to conventional chi-square for zero x uncertainties.
quasi_chisq = output.res_var
uncertainty = output.sd_beta # parameter standard uncertainties
#  scipy.odr scales the parameter uncertainties by quasi_chisq.
#    If the fit is poor, i.e. quasi_chisq is large, the uncertainties
#    are scaled up, which makes sense. If the fit is too good,
#    i.e. quasi_chisq << 1, it suggests that the uncertainties have
#    been overestimated, but it seems risky to scale down the
#    uncertainties. i.e. The uncertainties shouldn't be too sensistive
#    to random fluctuations of the data, and if the uncertainties are
#    overestimated, this should be understood and corrected.
if quasi_chisq < 1.0 :
    uncertainty = uncertainty/numpy.sqrt(quasi_chisq)
if False: # debugging print statements
    print("sd_beta",output.sd_beta)
    print("cov_beta",output.cov_beta)
    print("delta",output.delta)
    print("epsilon",output.epsilon)
    print("res_var",output.res_var)
    print("rel_error",output.rel_error)

######################## PRINT THE RESULTS ###########################
print("\n***********************************************************")
print("               ORTHOGONAL DISTANCE REGRESSION")
print("***********************************************************")
print("\nFitting {0} Data points from file {1} this Model function"
                                    .format(len(x_data),data_file))
print(" ",inspect.getsource(func))

# If systematic uncertainties are not zero, print them
if (dx_offset+dx_scale+dy_offset+dy_scale > 0).any :
    print("Systematics")
    print("   correlated_offset = ", correlated_offset)
    print("   correlated_scale  = ",correlated_scale)
if (dy_offset+dy_scale > 0).any :
    print("   x_true = {0}+/-{1} + ({2}+/-{3})*x_measured".format(
                sys_x[0],sys_x[1],sys_x[2],sys_x[3]))
if (dy_offset+dy_scale > 0).any :
    print("   y_true = {0}+/-{1} + ({2}+/-{3})*y_measured".format(
                *sys_y))

print("\n**** ODR has finished with: " + output.stopreason[0]+"\n")

print(" Estimated parameters, uncertainties, and starting guesses")
for i in range(len(p)) :
    print(("   p[{0}] = {1:10.5g} +/- {2:10.5g}"+
           "          Guessed: {3:<10.5g}").
            format(i,p[i],uncertainty[i],p_guess[i]))

# number of degrees of freedom for fit
dof = len(x_data) - len(p_guess)

cor = numpy.empty_like(cov)
for i,row in enumerate(cov):
    for j in range(len(p)) :
        cor[i,j] = cov[i,j]/numpy.sqrt(cov[i,i]*cov[j,j])
print("\n ODR Correlation Matrix\n\t"
          + str(cor).replace('\n','\n\t'))

# Calculate initial residuals and adjusted error 'sigma_odr'
#                 for each data point
delta   = output.delta   # estimated x-component of the residuals
epsilon = output.eps     # estimated y-component of the residuals
# (dx_star,dy_star) are the projections of x_sigma and y_sigma onto
#    the residual line, i.e. The differences in x & y between the data
#    point and the point where the orthogonal residual line intersects
#    the ellipse' created by x_sigma & y_sigma.
dx_star = ( x_sigma*numpy.sqrt( ((y_sigma*delta)**2) /
                ( (y_sigma*delta)**2 + (x_sigma*epsilon)**2 ) ) )
dy_star = ( y_sigma*numpy.sqrt( ((x_sigma*epsilon)**2) /
                ( (y_sigma*delta)**2 + (x_sigma*epsilon)**2 ) ) )
sigma_odr = numpy.sqrt(dx_star**2 + dy_star**2)
# residual is positive if the point lies above the fitted curve,
#             negative if below
residual = ( numpy.sign(y_data-func(x_data,*p))
              * numpy.sqrt(delta**2 + epsilon**2) )

# Print quasi-chi-squared and associated quasi-CDF
#   WARNING: This CDF is not valid for large x uncertainties!
from scipy.special import chdtrc      # Chi-squared survival function
print(("\n Quasi Chi-Squared/dof   = {0:10.5f}," +
         " Quasi CDF = {1:10.5f}%").
       format(quasi_chisq, 100.*float(chdtrc(dof,dof*quasi_chisq))))

#################################################################
#### Monte Carlo estimation of uncertainties
#################################################################
print("\n**** Running Monte Carlo CDF Estimator ****")
# Initialize Monte Carlo output distributions
p_dist_Data, p_dist_Model  = [], []
quasi_chisq_dist           = []
# Initialize timing measurement
import time
start_time = time.clock()
for i in range(Number_of_MC_iterations) :
    # Starting with the x and x uncertainty (x_sigma) values from
    #    the data, calculate Monte Carlo values assuming an uncertainty
    #    distibution defined above by smear e.g. gaussian, uniform, â€¦
    #    Code can be modified if different uncertainties have different
    #    associated uncertainty distributions.
    x_scale_MC  = smear_scale_x(x_scale,dx_scale)
    x_offset_MC = smear_x_offset(x_offset,dx_offset)
    if correlated_scale  :
        y_scale_MC  = x_scale_MC
    else :
        y_scale_MC  = smear_scale_y(y_scale,dy_scale)
    if correlated_offset :
        y_offset_MC = x_offset_MC
    else :
        y_offset_MC = smear_y_offset(y_offset,dy_offset)
    # Applied MC systematic scaling to smeared x data
    x = (x_offset_MC + smear_x_data(x_in_file,x_sigma_in_file ) \
                                         * x_scale_MC)
    # Set random uncertainties from file if they were not set by hand
    if x_sigma_set == None :
        x_sigma_MC = x_sigma_in_file * x_scale_MC
    else :
        x_sigma_MC = x_sigma_set     * x_scale_MC
    if y_sigma_set == None :
        y_sigma_MC = y_sigma_in_file * y_scale_MC
    else :
        y_sigma_MC = y_sigma_set     * y_scale_MC

    ## Generate smeared y data for fits to determine
    #      parameter uncertainties
    y = (y_offset_MC + smear_y_data(y_in_file,y_sigma_in_file ) \
                                         * y_scale_MC)
    # Set up data and model for ODR fit
    data_dist = scipy.odr.RealData( x=x, y=y, sx=x_sigma_MC,
                                              sy=y_sigma_MC)
    model_dist = scipy.odr.Model(swapped)
    fit_dist = scipy.odr.ODR(data_dist, model_dist, p, maxit=50, job=0)
    # Run ODR fit on Monte Carlo x,y pseudo-data
    output_dist = fit_dist.run()
    # Ignore results if some fit parameters is Not a Number ("nan")
    if numpy.isnan(numpy.sum(output_dist.beta)) :
        continue
    p_dist_Data.append(output_dist.beta)
    ## Calculate y using Model function for Monte Carlo x, then smear by
    #   y uncertainty  to determine cdf for above ODR fit
    y_measured_MC = (func(x_data,*p)-y_offset_MC)/y_scale_MC
    y = (y_offset_MC + smear_y_data(y_measured_MC,y_sigma_MC ) \
                                         * y_scale_MC)
    data_dist = scipy.odr.RealData( x=x, y=y, sx=x_sigma,  sy=y_sigma)
    fit_dist = scipy.odr.ODR(data_dist, model_dist, p, maxit=50, job=0)
    output_dist = fit_dist.run()
    quasi_chisq_dist.append(output_dist.res_var)
    p_dist_Model.append(output_dist.beta)
# Convert outputs to numpy array
p_dist_Model = numpy.array(p_dist_Model)
p_dist_Data  = numpy.array(p_dist_Data)

end_time = time.clock()

Actual_MC_iterations = len(p_dist_Data)
print("    {0} successful MC simulations in {1:7g} seconds.".format(
                Actual_MC_iterations, end_time-start_time))
# Covariance matrix for Monte Carlo parameter outputs
MC_cov = numpy.cov(p_dist_Data,rowvar=False)
# Correlation matrix
MC_cor = numpy.empty_like(MC_cov)
for i,row in enumerate(MC_cov):
    for j in range(len(p)) :
        MC_cor[i,j] = MC_cov[i,j]/numpy.sqrt(MC_cov[i,i]*MC_cov[j,j])
# Sort the simulated quasi-chi-squared values
quasi_chisq_sort = numpy.sort(quasi_chisq_dist)
# Find the index of the sorted simulated quasi-chi-squared value
# nearest to the data quasi-chi-squared value, to estimate the cdf
print("\n Fraction of Monte Carlo quasi-chi-squared values larger" +
           " than value for ODR fit:")
MC_CDF = 100.*(1.0-numpy.abs(quasi_chisq_sort-quasi_chisq).argmin()
                                   /float(Actual_MC_iterations))
# The minimum CDF value from Monte Carlo is 1/Actual_MC_iterations,
#   so warn if at minimum
if MC_CDF < 100./(Actual_MC_iterations-1) :
    print("    Monte Carlo CDF is less than {0:6.1f}%".format(MC_CDF))
    print("             and is consistent with 0.0%")
    print("    For a better limit run with more iterations!")
else :
    print("    Monte Carlo CDF = {0:6.1f}%".format(MC_CDF))

# Indices of 68.3% interval of MC distribution
k_16     = int(Actual_MC_iterations*0.158655254)
k_84     = int(Actual_MC_iterations*0.841344746)
print("\n MC Fit parameters Average + Standard Deviation; Median"
              + " and 68.3% interval")
ave_p = numpy.average(p_dist_Data,axis=0)
std_p = numpy.std(    p_dist_Data,axis=0)
med_p = numpy.median( p_dist_Data,axis=0)

for i in range(len(p)) :
    sorted_p_i = numpy.sort(p_dist_Data[:,i])
    print (("   p[{0}] = {1:11.5g} +/- {2:11.5g} ;"
                     + " {3:11.5g} + {4:11.5g} - {5:11.5g}")
                     .format(i, ave_p[i], std_p[i], med_p[i],
                             sorted_p_i[k_84]-med_p[i],
                             med_p[i] - sorted_p_i[k_16] ))
# Print warning if scale uncertainties are too large
#   The problem with large scale errors is that if the actual scale is
#   underestimated, the effect of the scale uncertainty is reduced so
#   the likelihood of large values is underestimated.
if numpy.any(dx_scale > 0.1) :
    print("!!!WARNING!!! x scale Uncertainty (",dx_scale,") is so\n",
        " large that parameter uncertainties may be underestimated!!!")
if numpy.any(dy_scale > 0.1) :
    print("!!!WARNING!!! y scale Uncertainty (",dy_scale,") is so\n",
        " large that parameter uncertainties may be underestimated!!!")

print("\n Monte Carlo Correlation Matrix\n\t"
          + str(MC_cor).replace('\n','\n\t'))

print("\n Check For Bias in MC Fit parameters")

# Check if fit on Monte Carlo data tends to give a medianoutput
#    value for the parameters different from the input parameters.
std_p = numpy.std(    p_dist_Model,axis=0)
med_p = numpy.median( p_dist_Model,axis=0)
print("   (Monte Carlo median)/(fit value) - 1")
for i in range(len(p)) :
    bias             = med_p[i]/p[i]-1
    sorted_p_i = numpy.sort(p_dist_Model[:,i])
    # Note: Am using Gaussian approximation for median uncertainty
    bias_uncertainty = (abs((std_p[i]/p[i]))
                            / numpy.sqrt(Actual_MC_iterations-1)
                            * numpy.sqrt(numpy.pi/2))
    print("      p[{0}] Bias : {1:<+9.4g} +/- {2:<9.4g} ({3:7.2f} SD)"
          .format( i, bias, bias_uncertainty, bias/bias_uncertainty) )

#################################################################
#### Plot Section
#################################################################

# create figure with light gray background
fig = pyplot.figure(facecolor="0.98")

# 4 rows, 1 column, subplot 1 fills rows 1 and 2
fit = fig.add_subplot(4,1,(1,2))
fit.set_ylabel(y_label)

pyplot.title(sampleTitle + " - ODR Fit")

# For a smooth look,generate many x values for plotting the model
stepsize = (max(x_data)-min(x_data))/1000.
margin = 50*stepsize
x_model = numpy.arange( min(x_data)-margin,max(x_data)+margin,
                                stepsize)

# Plot data as red circles
fit.plot(x_data,y_data,'ro', markersize=4, label="Data")
# Add error bars on data as red crosses.
fit.errorbar(x_data, y_data, xerr=x_sigma, yerr=y_sigma, fmt='r+')
fit.set_yscale('linear')

# Draw best fit
fit.plot(x_model, func(x_model,*p),    'b-', label="Best ODR Fit")

# Set vertical range from data
pyplot.ylim(min(y_data-2*y_sigma), max(1.05*(y_data+2*y_sigma)))


# Plot ODR distances from points to fitted curve
a = numpy.array([output.xplus,x_data])
b = numpy.array([output.y,y_data])
fit.plot( numpy.array([a[0][0],a[1][0]]),
          numpy.array([b[0][0],b[1][0]]),
          'k-')
for i in range(1,len(y_data)):
    fit.plot( numpy.array([a[0][i],a[1][i]]),
              numpy.array([b[0][i],b[1][i]]),
              'k-')
fit.grid()
fit.set_ylabel(y_label)

#################################################################
#### Residual Plot
#################################################################
residuals = fig.add_subplot(4,1,4)
residuals.set_title("Residuals")
residuals.errorbar(x=x_data,y=residual,yerr=sigma_odr,
                   			fmt="r+", label = "Residuals")
# make sure residual plot has same x axis as fit plot
residuals.set_xlim(fit.get_xlim())
# Draw a horizontal line at zero on residuals plot
pyplot.axhline(y=0, color='b')
# Label axes
residuals.set_xlabel(x_label)
residuals.set_ylabel("$\Delta$"+y_label)
# These data look better in 'plain', not scientific, notation, and if
#   the tick labels are not offset by a constant (as done by default).
pyplot.ticklabel_format(style='plain', useOffset=False, axis='x')
residuals.grid()

#################################################################
#### Optional Data/Fit Plots
#################################################################

# Draw starting guess as dashed green line ('g-')
if plot_initial_guess:
    fit.plot(x_model, func(x_model,*p_guess), 'g-',
                           label="Initial guess", linestyle="--")
if plot_MC_fits :
    fit.plot(x_model, func(x_model,*ave_p),
             'm:', label="Using mean MC values")
    fit.plot(x_model, func(x_model,*med_p),
             'y:', label="Using median MC values")

# Put a legend into row 3 (between data/fit and residual plots)
fit.legend(loc='upper center', bbox_to_anchor=(0.5, -0.085),ncol=2)

# Save the plot to a file
fig.savefig("ODR_Plot.pdf")

# Show the plot
pyplot.show()

"""
Full text of MIT License:

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""