
import numpy
def moving_average(interval, window_size):
    window= numpy.ones(int(window_size))/float(window_size)
    print window
    print interval
    return numpy.convolve(interval, window, 'valid')

a = range(1,100)
ma = moving_average(a, 10)
print ma