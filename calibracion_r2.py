#!/usr/bin/env python
'''
To run the SRR measurement script:

python calibracion_srr_r2.py 192.168.1.12 -g 0xf000000 -l 131072 -b spec_2sb_r2_2in_2000_2016_Jan_20_0114.bof
python calibracion_srr_r2.py 192.168.1.12 -g 0xf000000 -l 131072 -b spec_2sb_r2_2016_Jan_24_0544.bof
python calibracion_srr_r2.py 192.168.1.12 -g 0xf000000 -l 131072 -b spec_2sb_r2_v2_2016_Jan_23_1909.bof

\nAuthor: Ed, November 2013.
'''

#import corr,time,numpy,struct,sys,logging,pylab,matplotlib,math,Gnuplot, Gnuplot.funcutils,array, telnetlib
import corr, time, struct, sys, logging, Gnuplot, valon_synth, telnetlib, numpy as np
from math import *
import adc5g

bitstream = 'No_bof_file_error'
katcp_port=7147

t1 = time.time()  #Inicializa cronometro.

print ('__________________________________________________')
print ('                                                  ')
print ('  ____    _    _     ____ _   _ _        _        ')
print (' / ___|  / \  | |   / ___| | | | |      / \       ')
print ('| |     / _ \ | |  | |   | | | | |     / _ \      ')
print ('| |___ / ___ \| |__| |___| |_| | |___ / ___ \     ')
print (' \____/_/   \_\_____\____|\___/|_____/_/   \_\    ')
print ('                                                  ')
print ('      ____  ____  ____                            ')
print ('     / ___||  _ \|  _ \                           ')
print ('     \___ \| |_) | |_) |                          ')
print ('      ___) |  _ <|  _ <                           ')
print ('     |____/|_| \_\_| \_\                          ')
print ('                                                  ')

def hhmmss(segundostotales):
    hh = segundostotales // 3600
    mm = (segundostotales % 3600)//60
    ss = (segundostotales %3600) %60
    return hh,mm,ss

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data():   
    acc_n = fpga.read_uint('acc_cnt')

#    fpga.write_int('data_ctrl_lec_done',0)
#    fpga.write_int('data_ctrl_sel_we',1)

    a_0l=struct.unpack('>512Q',fpga.read('dout0_0',512*8,0))
    a_1l=struct.unpack('>512Q',fpga.read('dout0_1',512*8,0))
    a_2l=struct.unpack('>512Q',fpga.read('dout0_2',512*8,0))
    a_3l=struct.unpack('>512Q',fpga.read('dout0_3',512*8,0))
#
    a_0m=struct.unpack('>512Q',fpga.read('dout1_0',512*8,0))
    a_1m=struct.unpack('>512Q',fpga.read('dout1_1',512*8,0))
    a_2m=struct.unpack('>512Q',fpga.read('dout1_2',512*8,0))
    a_3m=struct.unpack('>512Q',fpga.read('dout1_3',512*8,0))

#    fpga.write_int('data_ctrl_lec_done',1)
#    fpga.write_int('data_ctrl_sel_we',0)  

    interleave_a=[]
    interleave_b=[]
    interleave_log=[]        
    interleave_log_b=[]

    for i in range(512):
        interleave_a.append(float(((float(a_0l[i])+1)/(2**24))))#24 es el original
        interleave_a.append(float(((float(a_1l[i])+1)/(2**24))))
        interleave_a.append(float(((float(a_2l[i])+1)/(2**24))))
        interleave_a.append(float(((float(a_3l[i])+1)/(2**24))))
        interleave_b.append(float(((float(a_0m[i])+1)/(2**24))))
        interleave_b.append(float(((float(a_1m[i])+1)/(2**24))))
        interleave_b.append(float(((float(a_2m[i])+1)/(2**24))))
        interleave_b.append(float(((float(a_3m[i])+1)/(2**24))))

    for k in range(4*512):
        interleave_log.append(10*log10(interleave_a[k]))
        interleave_log_b.append(10*log10(interleave_b[k]))

    return acc_n, interleave_a, interleave_log, interleave_log_b

##############################################################
### Se abren los archivos en los cuales se escriben los datos

srr_datos=open('srr_datos.dat','w')
lsb_usb_testtone=open('lsb_usb_testtone.dat','w')
datos_teo_corregido=open('datos_teo_corregido.dat','w')

################   START OF MAIN   ###########################

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=2*(2**28)/2048,
        help='Set the number of vectors to accumulate between dumps. default is 2*(2^28)/2048, or just under 2 seconds.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0x00001000,
        help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile',type='str', default='',
        help='Specify the bof file to load')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. Run with the -h flag to see all options.\nExiting.'
        exit()
    else:
        roach = args[0] 
    if opts.boffile != '':
        bitstream = opts.boffile

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    time.sleep(1)
    if fpga.is_connected():
	print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA with %s...' %bitstream,
    if not opts.skip:
        fpga.progdev(bitstream)
        print 'done'
    else:
        print 'Skipped.'
    print 'Configuring FFT shift register...',
    fpga.write('shift_ctrl','\x00\x00\x0f\xff')
    print 'done'
    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    # Calibrating ADCs
    print 'Calibrating the time delay at the adc interface...'  
    adc5g.sync_adc(fpga)
    opt1, glitches1 = adc5g.calibrate_mmcm_phase(fpga, 1,['snapshot_z1_c','snapshot_z1_a',])
    #opt2, glitches2 = adc5g.calibrate_mmcm_phase(fpga, 0,['snapshot_z0_c','snapshot_z0_a',])
    time.sleep(0.5)

    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'
    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
        fpga.write_int('gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'

# Se inicializan graficos y sus parametros.

    g0 = Gnuplot.Gnuplot(debug=0)
    g1 = Gnuplot.Gnuplot(debug=0)
    g2 = Gnuplot.Gnuplot(debug=0)

    bw=trunc(fpga.est_brd_clk())*4
    print ('BW obtenido es: '+str(fpga.est_brd_clk()))

    g0.clear()    
    g0.title('ADC1 spectrum using '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    g0.xlabel('Channel #')
    g0.ylabel('Power AU (dB)')
    g0('set style data linespoints')
    g0('set yrange [0:120]')
    g0('set xrange [-50:2098]')
    g0('set ytics 5')
    g0('set xtics 256')
    g0('set grid y')
    g0('set grid x')	

    g1.clear()    
    g1.title('ADC0 spectrum using '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    g1.xlabel('Channel #')
    g1.ylabel('Power AU (dB)')
    g1('set style data linespoints')
    g1('set yrange [0:120]')
    g1('set xrange [-50:2098]')
    g1('set ytics 5')
    g1('set xtics 256')
    g1('set grid y')
    g1('set grid x')

### starting the measurement proccess

#    rys = telnetlib.Telnet("172.17.89.49",5025)
    agi = telnetlib.Telnet("192.168.1.34",5023) #psg 6GHZ
    #agi = telnetlib.Telnet("192.168.1.36",5020) #anritzu 40GHz
    #agi = telnetlib.Telnet("192.168.1.33",5025) #rys 3.2GHZ")
    #valon=valon_synth.Synthesizer('/dev/ttyUSB0')

#    rys.write("output off\r\n")
    agi.write("output off\r\n")

#setting LO
#    LO=input('LO frequency [GHz] ? : ')  #GHz
#    rys.write("freq "+str(LO)+"ghz\r\n") # Cambiar frec de LO
#    rys.write("power 18dbm\r\n")
#    rys.write("output on\r\n")


#setting RF start point
#    agi.write("freq 15ghz\r\n")
#    agi.write("power 16dbm\r\n")   ##para setup double down-conversion
    agi.write("freq 3.0ghz\r\n")
    time.sleep(0.1)
    agi.write("power -23dbm\r\n") ##para setup pseudo frontend
    time.sleep(0.1)
    agi.write("output on\r\n")
# measurement

    srr=[]
    rf=[]
    tono_usb=[]
    tono_lsb=[]
    canales=[]
    ch=[]

    print ('bw es: '+ str(bw))
    bw=float(trunc(fpga.est_brd_clk())*4.0/1000)
    LO=3.0
    start=LO-bw
    stop=LO+bw
    print ''
    points=input('Number of points? :') #Numero de puntos para mostrar SRR
    modo_memoria=input('modo memoria? (1,2 o 3)=')
    g2.clear()    
    g2.title('Sideband Rejection Ratio using '+bitstream+' | running at '+str(bw)+' GHz')
    g2.xlabel('RF freq (GHz) - shown LSB and USB -')
    g2.ylabel('SSR (dB)')
    g2('set style data linespoints')
    g2('set yrange [0:60]')
    g2('set xrange ['+str(start-0.05)+":"+str(stop+0.05)+']')
    g2('set ytics 5')
    g2('set xtics 0.1')
    g2('set grid y')
    g2('set grid x')

################################################################
############  INICIO ADQUISICION DE DATOS DE LA OPTIMIZACION ###
################################################################
    ampq=[]
    degq=[]
    ampi=[]
    degi=[]
    #matriz_datos_optimos=np.loadtxt('datos_teo_2500LO-12dbm.dat')   ##ARCHIVO DAT
    #matriz_datos_optimos=np.loadtxt('datos_teo_exitoso_27_marzo_2014_sin_dctrl.dat')   ##ARCHIVO DAT
    matriz_datos_optimos=np.loadtxt('datos_teo.dat')
    #matriz_datos_optimos=np.loadtxt('datos_teo_7_septiembre_2015_dctrl.dat')
    

################################################################
############  CARGAR DATOS EN MEMORIA   ########################
################################################################ # modo_memoria=1 (para completar con datos optimizados o teoricos) 
                   # modo_memoria=2 (completa con datos 1 de amp y 90 grados)

    if modo_memoria == 1:

        for i in range (0,(len(matriz_datos_optimos)/4)):
            ampi.append(matriz_datos_optimos[i,1])
        for i in range ((len(matriz_datos_optimos)/4),(2*(len(matriz_datos_optimos)/4))):
            degi.append(matriz_datos_optimos[i,1])

    # USB
        for i in range ((2*(len(matriz_datos_optimos)/4)),(3*(len(matriz_datos_optimos)/4))):
            ampq.append(matriz_datos_optimos[i,1])
        for i in range ((3*(len(matriz_datos_optimos)/4)),(4*(len(matriz_datos_optimos)/4))):
            degq.append(matriz_datos_optimos[i,1])
    
    #ampq.reverse()
    #degq.reverse()
    
    # Se crea datos_teo_corregido, que contiene los datos de la calibracion en forma ordenada
    # para que se puedan leer en Matlab y generar los graficos correspondientes.

        for i in range(1,1022,1): #for i in range(1,1022,1):
            datos_teo_corregido.write('0 '+str(ampi[i-1])+' '+str(((LO)-2*i*float(bw)/2048)*1000)+' \n')   
        for i in range(1,1022,1):
            datos_teo_corregido.write('0 '+str(degi[i-1])+' '+str(((LO)-2*i*float(bw)/2048)*1000)+' \n') 
        for i in range(1,1022,1):
            datos_teo_corregido.write('0 '+str(ampq[i-1])+' '+str(((LO)+2*i*float(bw)/2048)*1000)+' \n')   
        for i in range(1,1022,1):
            datos_teo_corregido.write('0 '+str(degq[i-1])+' '+str(((LO)+2*i*float(bw)/2048)*1000)+' \n')
        datos_teo_corregido.close()

        for j in range(0,510):
            print ('Escribiendo memoria '+str(j)+' de 510')
            # CANAL I = LSB
            fpga.write('VCM0_RE_BRAM',struct.pack('>1l',ampi[2*j]*cos((pi/180)*degi[2*j])*2**24),4*j)  #canal 0, 4 ...  (4i)
            fpga.write('VCM0_IM_BRAM',struct.pack('>1l',ampi[2*j]*sin((pi/180)*degi[2*j])*2**24),4*j) 

            fpga.write('VCM1_RE_BRAM',struct.pack('>1l',((ampi[2*j]+ampi[(2*j)+1])/2)*cos((pi/180)*((degi[2*j]+degi[(2*j)+1])/2))*2**24),4*j)  #canal 1, 5 ..
            fpga.write('VCM1_IM_BRAM',struct.pack('>1l',((ampi[2*j]+ampi[(2*j)+1])/2)*sin((pi/180)*((degi[2*j]+degi[(2*j)+1])/2))*2**24),4*j)

            fpga.write('VCM2_RE_BRAM',struct.pack('>1l',ampi[(2*j)+1]*cos((pi/180)*degi[(2*j)+1])*2**24),4*j)  #canal 2, 6 ...
            fpga.write('VCM2_IM_BRAM',struct.pack('>1l',ampi[(2*j)+1]*sin((pi/180)*degi[(2*j)+1])*2**24),4*j)
      
            fpga.write('VCM3_RE_BRAM',struct.pack('>1l',((ampi[(2*j)+1]+ampi[(2*j)+2])/2)*cos((pi/180)*((degi[(2*j)+1]+degi[(2*j)+2])/2))*2**24),4*j)
            fpga.write('VCM3_IM_BRAM',struct.pack('>1l',((ampi[(2*j)+1]+ampi[(2*j)+2])/2)*sin((pi/180)*((degi[(2*j)+1]+degi[(2*j)+2])/2))*2**24),4*j)
   

            # CANAL Q = USB
            fpga.write('VCM4_RE_BRAM',struct.pack('>1l',ampq[2*j]*cos((pi/180)*degq[2*j])*2**24),4*j)  #canal 0, 4 ...
            fpga.write('VCM4_IM_BRAM',struct.pack('>1l',ampq[2*j]*sin((pi/180)*degq[2*j])*2**24),4*j)  

            fpga.write('VCM5_RE_BRAM',struct.pack('>1l',((ampq[2*j]+ampq[(2*j)+1])/2)*cos((pi/180)*((degq[2*j]+degq[(2*j)+1])/2))*2**24),4*j)  #canal 1, 5 ...
            fpga.write('VCM5_IM_BRAM',struct.pack('>1l',((ampq[2*j]+ampq[(2*j)+1])/2)*sin((pi/180)*((degq[2*j]+degq[(2*j)+1])/2))*2**24),4*j)

            fpga.write('VCM6_RE_BRAM',struct.pack('>1l',ampq[(2*j)+1]*cos((pi/180)*degq[(2*j)+1])*2**24),4*j)  #canal 2, 6 ...
            fpga.write('VCM6_IM_BRAM',struct.pack('>1l',ampq[(2*j)+1]*sin((pi/180)*degq[(2*j)+1])*2**24),4*j)

            fpga.write('VCM7_RE_BRAM',struct.pack('>1l',((ampq[(2*j)+1]+ampq[(2*j)+2])/2)*cos((pi/180)*((degq[(2*j)+1]+degq[(2*j)+2])/2))*2**24),4*j)  
            fpga.write('VCM7_IM_BRAM',struct.pack('>1l',((ampq[(2*j)+1]+ampq[(2*j)+2])/2)*sin((pi/180)*((degq[(2*j)+1]+degq[(2*j)+2])/2))*2**24),4*j)        
        print('--- Escritura de memorias terminada  ---')

    elif modo_memoria == 2:  # Llena las memorias con unos y ceros
        for i in range(512):
            print ('Escribiendo memoria '+str(i)+' de 511')
            #print ('Escribiendo memoria '+str(j)+' de 512')
            fpga.write('VCM0_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM0_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM1_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM1_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM2_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM2_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM3_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM3_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM4_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM4_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM5_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM5_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM6_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM6_IM_BRAM',struct.pack('>1l',1*2**24),4*i)
            fpga.write('VCM7_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM7_IM_BRAM',struct.pack('>1l',1*2**24),4*i)


    elif modo_memoria == 3:  # Llena las memorias con ceros
        for i in range(512):
            print ('Escribiendo memoria '+str(i)+' de 512')
            fpga.write('VCM0_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM0_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM1_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM1_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM2_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM2_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM3_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM3_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM4_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM4_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM5_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM5_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM6_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM6_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM7_RE_BRAM',struct.pack('>1l',0*2**24),4*i)
            fpga.write('VCM7_IM_BRAM',struct.pack('>1l',0*2**24),4*i)
    ################################################################
    ############  FIN CARGAR DATOS EN MEMORIA   ####################
    ################################################################

    for i in range(points):
        rf.append(start+((stop-start)*i/points))
    
    modo=1   # Se elige el MODO  

    ##### INICIO DE GRAFICO SSR (MODO 1)
    ######################################################################
    if modo == 1:
        srr_datos.write('#Valores SRR    #Frecuencia   \n')


        for i in range(points):
            agi.write("freq " + str(rf[i]) + "ghz\r\n")
#           valon.set_frequency(valon_synth.SYNTH_A,1000*rf[i])


            time.sleep(1)
            acc_n, interleave_a, interleave_log, interleave_log_b = get_data()
            time.sleep(0.1)

            interleave_log[0]=interleave_log[1]
            interleave_log_b[0]=interleave_log_b[1]
#
            g0.plot(interleave_log_b)
            g1.plot(interleave_log)
#
            srr.append([rf[i],abs(max(interleave_log)-max(interleave_log_b))])
            g2.plot(srr)
            ### Escribe datos SRR en archivo .dat
            srr_datos.write(str(srr[i][1])+' '+str(rf[i])+' \n')

#
    elif modo ==2:
    ##### INICIO DE TONO DE PRUEBA (LSB AND USB SPECTRA FOR TEST TONE) (MODO 2)
    ######################################################################
        agi.write("freq " + str(2.6) + "ghz\r\n")   # TONO DE PRUEBA  en 2600 MHz
        time.sleep(1)
        acc_n, interleave_a, interleave_log, interleave_log_b = get_data()
        time.sleep(0.1)
        interleave_log[0]=interleave_log[1]
        interleave_log_b[0]=interleave_log_b[1]

        g0.plot(interleave_log_b)
        g1.plot(interleave_log)
    
        for i in range(0,len(interleave_log_b)):
            lsb_usb_testtone.write(str(interleave_log[i])+' '+str(interleave_log_b[i])+' '+str(i)+' \n')
         
    ######################################################################
    ######################################################################
    lsb_usb_testtone.close()
    t_ejec = time.time()-t1
    hh,mm,ss=hhmmss(t_ejec)
    print('El tiempo de ejecucion del programa (Grafica SRR) fue: '+str(hh)+'[h] ,'+str(mm)+'[min] ,'+str(ss),'[seg].')
    srr_datos.write('# FIN de datos SRR \n')
    #srr_datos.write('# Tiempo de ejecucion : '+str(hh)+'[h] ,'+str(mm)+'[min] ,'+str(ss),'[seg].')
    srr_datos.close()
    print ('')
    print ('Measurement finished!  - '+str(points)+' points')
    print ('')

    out=raw_input('Enter a filename to save data:(none to exit)')
    if out!='':
        f = open(str(out), 'w')
        f.write("RF (GHz),SSR (dB)\n")
        for i in range (points):
            f.write(str(srr[i][0])+","+str(srr[i][1])+"\n") 
except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()
exit_clean()
