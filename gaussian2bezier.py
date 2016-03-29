from scipy.optimize import curve_fit
import scipy.stats as stats
import numpy as np
import pylab

x = np.linspace(-3, 0)
y = stats.norm.pdf(x)


def _bezier_normal_xy(x0, p1x, p1y, p2x):
    x1 = np.array([[i] for i in np.linspace(0, 1, len(x0))])
    min_x = np.min(x0)
    max_x = np.max(x0)
    min_y = stats.norm.pdf(min_x)
    max_y = stats.norm.pdf(max_x)
    p0 = np.array([min_x, min_y])
    p1 = np.array([p1x, p1y])
    p2 = np.array([p2x, max_y])
    p3 = np.array([max_x, max_y])

    def binomial_coef(n, i):
        return np.product(range(1, n+1))/np.product(range(1, i+1))/np.product(range(1, n-i+1))

    def bernstein_polynomial(x, n, i):
        return binomial_coef(n, i) * (x ** i) * ((1 - x) ** (n - i))

    result = bernstein_polynomial(x1, 3, 0) * p0 + \
             bernstein_polynomial(x1, 3, 1) * p1 + \
             bernstein_polynomial(x1, 3, 2) * p2 + \
             bernstein_polynomial(x1, 3, 3) * p3
    diff = stats.norm.pdf(result[:, 0]) - result[:, 1]
    return diff


def bezier_normal_xy(x0, p1x, p1y, p2x):
    x1 = np.array([[i] for i in np.linspace(0, 1, len(x0))])
    min_x = np.min(x0)
    max_x = np.max(x0)
    min_y = stats.norm.pdf(min_x)
    max_y = stats.norm.pdf(max_x)
    print "min_y ", min_y
    print "max_y ", max_y
    print min_y / max_y
    p0 = np.array([min_x, min_y])
    p1 = np.array([p1x, p1y])
    p2 = np.array([p2x, max_y])
    p3 = np.array([max_x, max_y])

    def binomial_coef(n, i):
        return np.product(range(1, n+1))/np.product(range(1, i+1))/np.product(range(1, n-i+1))

    def bernstein_polynomial(x, n, i):
        return binomial_coef(n, i) * (x ** i) * ((1 - x) ** (n - i))

    result = bernstein_polynomial(x1, 3, 0) * p0 + \
             bernstein_polynomial(x1, 3, 1) * p1 + \
             bernstein_polynomial(x1, 3, 2) * p2 + \
             bernstein_polynomial(x1, 3, 3) * p3
    return result

def x_bezier_normal_xy(x0, p1x, p1y, p2x):
    x1 = np.array([[i] for i in np.linspace(0, 1, len(x0))])
    min_x = np.min(x0)
    max_x = np.max(x0)
    min_y = stats.norm.pdf(min_x)
    max_y = stats.norm.pdf(max_x)
    p0 = np.array([min_x, min_y])
    p1 = np.array([p1x, p1y])
    p2 = np.array([p2x, max_y])
    p3 = np.array([max_x, max_y])

    def binomial_coef(n, i):
        return np.product(range(1, n+1))/np.product(range(1, i+1))/np.product(range(1, n-i+1))

    def bernstein_polynomial(x, n, i):
        return binomial_coef(n, i) * (x ** i) * ((1 - x) ** (n - i))

    result = bernstein_polynomial(x1, 3, 0) * p0 + \
             bernstein_polynomial(x1, 3, 1) * p1 + \
             bernstein_polynomial(x1, 3, 2) * p2 + \
             bernstein_polynomial(x1, 3, 3) * p3
    return result


(opts, cov) = curve_fit(_bezier_normal_xy, x, np.zeros(len(x)), [-0.5, 0.1, -2])

print "p1 x: {}, y: {}, p2 x: {}".format(*opts)
# p1 x: -1.25486806631, p1 y: 0.00192599899084, p2 x: -0.858789829499
(ax, fig) = pylab.subplots()

results = bezier_normal_xy(x, *opts)

delta_x = [0]

def x_to_u(x, a, b, c):
    return c + 2 ** (x * a + b)

def x_to_u_(x, a, b, c):
    return -0.54168062 + 2 ** (x * 1.42705621 - 0.81917911)

for i in range(1, results.shape[0]):
    delta_x.append(results[i, 0] - results[0, 0])

new_x = np.linspace(0, 1)
dx_rev = 1 - np.array(list(reversed(delta_x))) / 3

(xu_opts, cov) = curve_fit(x_to_u, new_x, dx_rev)

print xu_opts
#
# results_2 = x_to_u(x, *xu_opts)


fig.plot(new_x, dx_rev)
fig.plot(new_x, x_to_u(new_x, *xu_opts))
# fig.plot(np.linspace(-3, 0), results[:, 1])
# fig.plot(x, y)

pylab.show()

# test lat longs
(lat1, lng1) = 30, 30  # bottom right
(lat2, lng2) = 45, 15  # bottom left
(lat3, lng3) = 60, 60  # top right
(lat4, lng4) = 75, 45  # top left

