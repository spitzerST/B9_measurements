import log_handlers,katcp_wrapper,time,numpy,struct,sys,logging,pylab,matplotlib,math,Gnuplot, Gnuplot.funcutils,array, telnetlib
from math import *
import adc5g
from visa import *

# set terminal png transparent nocrop enhanced size 610,480 font "arial,8" 
# set output 'multiplt.1.png'
g0 = Gnuplot.Gnuplot(debug=0)
#g1 = Gnuplot.Gnuplot(debug=0)
#g0.clear() 




razon_amplitud1=[]
razon_amplitud2=[]



for x in range(100):
    razon_amplitud1.append([x,(x)**4])
    razon_amplitud2.append([x,10*(x)**1])




g0('set multiplot layout 1,2 rowsfirst title "test"')
g0('set size 0.4,0.4')
g0('set origin 0.5,0.5')
g0('set title "plot 1"')
g0.xlabel('Channel #')
g0.ylabel('Power (dB)')
g0('set style data linespoints')
g0('set xrange [0:10]')
g0('set yrange [0:100]')
g0('set ytics 10')
g0('set xtics 1')
g0('set grid y')
g0('set grid x')
g0.plot(razon_amplitud1)
#g0('unset key')

g0('set title "plot 2"')
g0('set size 0.4,0.4')
g0('set origin 0.5,0.5')
g0.plot(razon_amplitud2)
#g0('unset key')
#g0.xlabel('Channel #')
#g0.ylabel('Power (dB)')
#g0('set style data linespoints')
#g0('set xrange [0:10]')
#g0('set yrange [0:100]')
#g0('set ytics 10')
#g0('set xtics 1')
#g0('set grid y')
#g0('set grid x')
#g0.plot(razon_amplitud2)
#g0('unset key')
'''
g0('set title "Instanteneous power channel z0 a"')
g0.xlabel('Channel #')
g0.ylabel('Power (dB)')
g0('set style data linespoints')
g0('set xrange [0:2048]')
g0('set yrange [0:100]')
g0('set ytics 10')
g0('set xtics 128')
g0('set grid y')
g0('set grid x')
g0.plot(power_spectrum_z0_a)
g0('unset key')
g0('set title "Instanteneous power channel z0 c"')
g0.xlabel('Channel #')
g0.ylabel('Power (dB)')
g0('set style data linespoints')
g0('set xrange [0:2048]')
g0('set yrange [0:100]')
g0('set ytics 10')
g0('set xtics 128')
g0('set grid y')
g0('set grid x')
g0.plot(power_spectrum_z0_c)
g0('unset key')'''
g0('unset multiplot')





temp= raw_input() 