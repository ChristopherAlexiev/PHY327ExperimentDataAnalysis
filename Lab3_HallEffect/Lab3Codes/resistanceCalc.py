import math
delta = 0.000001
R_a = 2.46267
R_b = 2.29567
z_minus1 = 2*(math.log(2)/math.log(math.e))/(math.pi*(R_a+R_b))
z_i = 0
while True:
    y_i = 1/math.exp(math.pi*z_minus1*R_a)+1/math.exp(math.pi*z_minus1*R_b)
    z_i = z_minus1-((1-y_i)/math.pi)/(R_a/math.exp(math.pi*z_minus1*R_a)+R_b/math.exp(math.pi*z_minus1*R_b))
    if (abs(z_i-z_minus1)/z_i < delta):
        break
    z_minus1 = z_i
print(z_i)
print("resistance: " + str(1/z_i))