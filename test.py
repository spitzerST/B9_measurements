import log_handlers,katcp_wrapper,time,numpy,struct,sys,logging,pylab,matplotlib,math,Gnuplot, Gnuplot.funcutils,array, telnetlib
from math import *
import adc5g
from visa import *
import os


print "inicio"
directory = 'F:\RAFAEL RODRIGUEZ\google_drive_raig_account\B9_Prueba de conepto\[2016-04-05]\SRR y cal Roach 2-1'

from time import gmtime, strftime
print strftime("%d-%m-%Y", gmtime())


print directory
time.sleep(2)
if not os.path.exists(directory):
    os.makedirs(directory)
'''

bw=1000
bitstream=str(1000)
razon_amplitud1=[]
razon_amplitud2=[]

g0 = Gnuplot.Gnuplot(debug=0)
#g0.clear()
#time.sleep(10)
g0.title('Upper Side Band amplitude ratio '+bitstream+' | Max frequency = '+str(bw)+' MHz')
g0.xlabel('Channel #')
g0.ylabel('Power AU (dB)')
g0('set style data linespoints')
g0('set yrange [0.0:200]')
g0('set xrange [-5:17]')
g0('set ytics 10')
g0('set xtics 1')
g0('set grid y')
g0('set grid x')
g0('set term position 10,100')
g0('set terminal wxt size 500,250')  
#g0('set size 1, 0.5')


squares = []
for x in range(10):
    razon_amplitud1.append([x,x**2])
g0.plot(razon_amplitud1)



g1 = Gnuplot.Gnuplot(debug=0)
#g0.clear()
g1('set term position 100,600')
g1('set terminal wxt size 500,250')  

#time.sleep(10)
g1.title('Upper Side Band amplitude ratio '+bitstream+' | Max frequency = '+str(bw)+' MHz')
g1.xlabel('Channel #')
g1.ylabel('Power AU (dB)')
g1('set style data linespoints')
g1('set yrange [0.0:200]')
g1('set xrange [-5:17]')
g1('set ytics 10')
g1('set xtics 1')
g1('set grid y')
g1('set grid x')



#g0('set size 1, 0.5')


squares = []
for x in range(10):
    razon_amplitud2.append([x,x**1])
g1.plot(razon_amplitud2)




temp= raw_input() 

'''
rf_source = telnetlib.Telnet("192.168.1.34",5023)
print "send idn"
rf_source.write("*IDN?\r\n")
print "idn sent ok"

print rf_source.read_some()
print ('OK')

lo_source= instrument("TCPIP0::192.168.1.36::inst0::INSTR")#telnetlib.Telnet("192.168.1.35",5025)
lo_source.write("freq "+str(6)+"ghz\r\n")
print "freq ok"
lo_source.write("*IDN?\r\n")
print lo_source.read()

#lo_source.write("output off\r\n")
#lo_source.write("freq "+str(float(lo)/1000)+"ghz\r\n")
#lo_source.write("output on\r\n")'''